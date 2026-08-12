import os
import random
import string
from typing import Optional

import boto3
from botocore.config import Config
from sqlmodel import Session, select

# ---------------------------------------------------------------------------
# Cloudflare R2 (S3-compatible) — upload et affichage du portrait, réutilisable
# pour tout futur fichier de la plateforme (pas seulement les portraits).
# Le bucket ambrelab-fichiers est privé (accès public désactivé) : on ne
# stocke jamais un lien public en base, seulement la clé objet
# (ex: "elenior/portraits/character-12.jpg"), et on génère une URL présignée
# à la demande, côté upload (PUT) comme côté affichage (GET).
# Identifiants à poser en variables d'environnement Railway :
# R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME.
# ---------------------------------------------------------------------------

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "ambrelab-fichiers")


def get_r2_client():
    """Lève une erreur explicite si les identifiants R2 manquent, plutôt
    qu'un échec obscur au premier appel presigned_url."""
    if not (R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY):
        raise RuntimeError(
            "R2 non configuré : variables R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / "
            "R2_SECRET_ACCESS_KEY manquantes côté Railway."
        )
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4", region_name="auto"),
    )


def generate_upload_url(key: str, content_type: str, expires_in: int = 600) -> str:
    """URL présignée PUT (10 min) : le navigateur envoie l'octet directement
    à R2, l'API ne fait transiter aucun fichier (sobriété : pas de proxy
    binaire côté Railway)."""
    client = get_r2_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": key, "ContentType": content_type},
        ExpiresIn=expires_in,
    )


def generate_download_url(key: str, expires_in: int = 600) -> str:
    """URL présignée GET (10 min) : le bucket reste privé, chaque affichage
    redemande une URL fraîche plutôt que de stocker un lien permanent."""
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )


def generate_session_code(length: int = 6) -> str:
    """Génère un code court pour rejoindre une session (ex: 'K3P9XZ')."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def sync_combat_sheet_from_character(session: Session, character_id: int) -> None:
    """
    Recopie vers le CombatSheet lié à ce personnage les valeurs qui
    dépendent directement du détail combat de la fiche (arme équipée,
    maîtrise correspondante) — de simples recopies relationnelles, pas des
    calculs de règles.

    Ne touche PAS à l'encombrement net ni au PV/PP max : ce sont des
    calculs de règles (réduction Force/Agilité, table page 23) qui restent
    du côté client, comme tous les autres calculs de la fiche. Le client
    les écrit lui-même via PUT /combatsheets/{id} une fois calculés.

    Ne fait rien si le personnage n'a pas encore de CombatSheet lié — pas
    une erreur, juste rien à synchroniser pour l'instant.
    """
    # Import différé pour éviter un import circulaire (models importe déjà
    # ce fichier indirectement via main.py).
    from .models import CombatSheet, CharacterWeapon, CharacterWeaponMastery

    combat_sheet = session.exec(
        select(CombatSheet).where(CombatSheet.character_id == character_id)
    ).first()
    if not combat_sheet:
        return

    weapons = session.exec(
        select(CharacterWeapon).where(CharacterWeapon.combat_sheet_id == combat_sheet.id)
    ).all()
    active_weapon = next((w for w in weapons if w.equipee), None)
    if not active_weapon:
        return  # aucune arme marquée "équipée" : on laisse le CombatSheet tel quel

    combat_sheet.weapon_choice = active_weapon.name
    combat_sheet.weapon_type = active_weapon.category

    mastery = session.exec(
        select(CharacterWeaponMastery)
        .where(CharacterWeaponMastery.combat_sheet_id == combat_sheet.id)
        .where(CharacterWeaponMastery.category == active_weapon.category)
    ).first()
    combat_sheet.weapon_mastery = mastery.value if mastery else 0

    session.add(combat_sheet)
    session.commit()


import hmac

MJ_PASSWORD = os.environ.get("MJ_PASSWORD")


def is_mj(password: Optional[str]) -> bool:
    """Compare en temps constant. Si MJ_PASSWORD n'est pas configuré côté
    Railway, personne n'est considéré MJ (fail closed, pas d'accès ouvert
    par oubli de config)."""
    if not MJ_PASSWORD or not password:
        return False
    return hmac.compare_digest(password, MJ_PASSWORD)
