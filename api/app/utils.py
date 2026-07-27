import random
import string

from sqlmodel import Session, select


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
