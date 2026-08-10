from datetime import datetime
from typing import Optional

from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field


# ---------------------------------------------------------------------------
# Campagne
# ---------------------------------------------------------------------------

class CampaignBase(SQLModel):
    name: str
    system: Optional[str] = None  # ex: "7th Sea", "Pathfinder 2e"
    description: Optional[str] = None


class Campaign(CampaignBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class CampaignCreate(CampaignBase):
    pass


# ---------------------------------------------------------------------------
# Personnage
# ---------------------------------------------------------------------------
# Champs "état civil" et transverses de l'onglet Identité (cahier des charges
# fiche de personnage Elénior, section 2.1). Les listes (mineures, sorts,
# armes, etc.) vivent dans des tables séparées ci-dessous, jamais ici.
#
# niveau_personnage : niveau du personnage (1, 2, 3...). À ne pas confondre
# avec CombatSheet.niveau, qui est un PALIER de jeu (Nul/Médiocre/Normale/
# Fort/Supérieure/Légendaire) — deux notions différentes malgré le nom
# proche dans le livre de règles.

class CharacterBase(SQLModel):
    name: str
    player_name: Optional[str] = None

    prenom: Optional[str] = None
    surnom: Optional[str] = None
    classe: Optional[str] = None
    race: Optional[str] = None
    sexe: Optional[str] = None
    age: Optional[int] = None
    religion: Optional[str] = None
    origine: Optional[str] = None
    niveau_personnage: int = 1

    portrait_url: Optional[str] = None  # clé objet R2 (pas une URL publique : le
    # bucket ambrelab-fichiers est privé — voir app/utils.py::generate_download_url)
    description_physique: Optional[str] = None

    # Les 6 majeures (2.1). Mêmes noms que ceux déjà utilisés côté Cadran
    # (pages/elenior/cadran/index.html, const CARACS) pour rester cohérent
    # partout où une majeure est référencée. Valeur brute /100 ; le Cadran
    # applique lui-même la réduction (Majeure/2 + maîtrise...) au moment du
    # jet, donc aucun calcul de règle ici.
    carac_agilite: int = 0
    carac_force: int = 0
    carac_intellect: int = 0
    carac_perception: int = 0
    carac_charisme: int = 0
    carac_foi: int = 0

    pv_actuel: Optional[int] = None
    pv_max: Optional[int] = None
    pv_libres: int = 0  # points libres alloués au PV max (distinct de pp_libres —
    # la fiche d'origine a deux pools séparés, cf. onglet État)
    pp_actuel: Optional[int] = None
    pp_max: Optional[int] = None
    pp_libres: int = 0
    points_libres: int = 0  # ancien champ, conservé mais plus utilisé par la
    # fiche de personnage (voir pv_libres/pp_libres ci-dessus) — inutilisé
    # ailleurs dans le code à ce jour, laissé pour ne rien casser.

    etats_afflictions: Optional[str] = None
    notes: Optional[str] = None  # sert aussi de "notes de campagne" (2.7)

    # Magie (2.4) — champs libres uniquement, aucun moteur de règles ici
    # (voir commentaire plus haut). Les écoles chiffrées vivent dans
    # CharacterMagicSchool, pas ici.
    magie_famille: Optional[str] = None
    magie_type: Optional[str] = None
    magie_aspect: Optional[str] = None
    capacite_unique: Optional[str] = None


class Character(CharacterBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")


class CharacterCreate(CharacterBase):
    pass


# ---------------------------------------------------------------------------
# Fiche de combat (permanente, réutilisable d'une rencontre à l'autre)
# Ajoutée pour Le Cadran des Trente Temps (campagne Elénior).
#
# Reste volontairement "simple" (une arme active, une maîtrise effective) :
# c'est ce que le Cadran attend pour créer vite un combattant. Le détail
# complet d'une fiche de personnage (CharacterWeapon, CharacterWeaponMastery,
# CharacterArmorPiece ci-dessous) alimente ces champs par synchronisation
# (voir app/utils.py::sync_combat_sheet_from_character), le Cadran n'a rien
# à changer à sa façon de lire un CombatSheet.
# ---------------------------------------------------------------------------

class CombatSheetBase(SQLModel):
    name: str
    side_default: str = "allie"  # "allie" ou "adversaire"

    quick_mode: bool = False
    quick_ta: Optional[int] = None
    quick_atk_bonus: Optional[int] = None

    niveau: str = "Normale"  # Nul/Médiocre/Normale/Fort/Supérieure/Légendaire

    carac: dict = Field(default_factory=dict, sa_column=Column(JSON))
    mental: Optional[int] = None  # utilisé pour la Magie (exception 2.1)

    weapon_type: str
    weapon_choice: str
    weapon_quality: str
    weapon_mastery: int = 0

    esquive: int = 0
    parade_skill: int = 0
    encombrement: int = 0

    pv_max: int


class CombatSheet(CombatSheetBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    character_id: Optional[int] = Field(default=None, foreign_key="character.id")


class CombatSheetCreate(CombatSheetBase):
    character_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Session de combat (état temporaire, le temps d'une rencontre)
# Ajoutée pour Le Cadran des Trente Temps (campagne Elénior).
# ---------------------------------------------------------------------------

class GameSessionBase(SQLModel):
    app_name: str = "cadran"
    state: str  # JSON sérialisé, opaque pour l'API — le moteur de jeu reste côté client


class GameSession(GameSessionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")
    code: str = Field(index=True, unique=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GameSessionUpdate(SQLModel):
    state: str


# ---------------------------------------------------------------------------
# Caractéristiques mineures (2.2) — rattachées au personnage, pas au combat :
# elles couvrent aussi bien des compétences sociales/de connaissance que de
# combat, donc pas leur place sous CombatSheet.
# ---------------------------------------------------------------------------

class CharacterMinorSkillBase(SQLModel):
    name: str  # ex: "Pistage"
    value: int = 0  # /35
    majeure_liee: str  # une des 6 majeures, choix contextuel du joueur


class CharacterMinorSkill(CharacterMinorSkillBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterMinorSkillCreate(CharacterMinorSkillBase):
    pass


# ---------------------------------------------------------------------------
# Détail combat (2.3) — rattaché à CombatSheet (option A), alimente ses
# champs simples par synchronisation.
# ---------------------------------------------------------------------------

class CharacterWeaponBase(SQLModel):
    name: str
    category: str  # une des 11 catégories officielles de maîtrise d'armes
    degats: Optional[str] = None
    portee: Optional[str] = None
    proprietes: Optional[str] = None
    encombrement: int = 0
    equipee: bool = False  # une seule à True = l'arme "en main" pour le Cadran


class CharacterWeapon(CharacterWeaponBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    combat_sheet_id: int = Field(foreign_key="combatsheet.id")


class CharacterWeaponCreate(CharacterWeaponBase):
    pass


class CharacterWeaponMasteryBase(SQLModel):
    category: str  # une des 11 catégories officielles
    value: int = 0
    majeure_liee: Optional[str] = None  # une des 6 majeures, choix contextuel du joueur —
    # même mécanique de seuil que CharacterMinorSkill (voir fiche de personnage, jets)


class CharacterWeaponMastery(CharacterWeaponMasteryBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    combat_sheet_id: int = Field(foreign_key="combatsheet.id")


class CharacterWeaponMasteryCreate(CharacterWeaponMasteryBase):
    pass


class CharacterArmorPieceBase(SQLModel):
    localisation: str
    nom: str
    qualite: Optional[str] = None
    encombrement: int = 0
    prot_contondant: int = 0
    prot_percant: int = 0
    prot_tranchant: int = 0
    malus_discretion: int = 0
    res_acide: int = 0
    res_air: int = 0
    res_elec: int = 0
    res_feu: int = 0
    res_froid: int = 0
    res_lumiere: int = 0
    res_son: int = 0


class CharacterArmorPiece(CharacterArmorPieceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    combat_sheet_id: int = Field(foreign_key="combatsheet.id")


class CharacterArmorPieceCreate(CharacterArmorPieceBase):
    pass


# ---------------------------------------------------------------------------
# Magie (2.4, hors journal de brassage — exclu pour l'instant, spécifique
# au Corbeau) et Sorts (2.6). Champs de magie en texte libre (famille, type,
# aspect, capacité unique) restent des colonnes simples sur Character :
# aucun moteur de règles de magie ici, ce sujet est traité séparément.
# ---------------------------------------------------------------------------

class CharacterMagicSchoolBase(SQLModel):
    name: str  # une des 9 écoles officielles
    value: int = 0
    majeure_liee: Optional[str] = None  # même mécanique de seuil que CharacterMinorSkill


class CharacterMagicSchool(CharacterMagicSchoolBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterMagicSchoolCreate(CharacterMagicSchoolBase):
    pass


class CharacterSpecialSkillBase(SQLModel):
    name: str
    description: Optional[str] = None


class CharacterSpecialSkill(CharacterSpecialSkillBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterSpecialSkillCreate(CharacterSpecialSkillBase):
    pass


# NOTE (10/08/2026) : coexiste désormais avec la table Sort du système de
# magie complet (app/models_magie.py) - Sort calcule Coût/Cast à partir des
# tables de règles (aspects/écoles/type), alors que CharacterSpell reste un
# résumé en texte libre sur la fiche de personnage. Décision Obe (option 1) :
# les deux restent actives telles quelles pour l'instant, fusion éventuelle
# à traiter plus tard dans sa propre conversation.
class CharacterSpellBase(SQLModel):
    name: str
    ecole: Optional[str] = None
    cout: Optional[str] = None
    portee: Optional[str] = None
    duree: Optional[str] = None
    description: Optional[str] = None


class CharacterSpell(CharacterSpellBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterSpellCreate(CharacterSpellBase):
    pass


# ---------------------------------------------------------------------------
# Inventaire (2.5)
# ---------------------------------------------------------------------------

class CharacterInventoryItemBase(SQLModel):
    name: str
    quantite: int = 1
    notes: Optional[str] = None


class CharacterInventoryItem(CharacterInventoryItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterInventoryItemCreate(CharacterInventoryItemBase):
    pass


# ---------------------------------------------------------------------------
# Compagnons & Notes (2.7, hors carnet de contrats compromettants — exclu
# pour l'instant, spécifique au Corbeau)
# ---------------------------------------------------------------------------

class CharacterCompanionBase(SQLModel):
    name: str
    type_: Optional[str] = None  # "compagnon" ou "monture", texte libre
    notes: Optional[str] = None


class CharacterCompanion(CharacterCompanionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterCompanionCreate(CharacterCompanionBase):
    pass


class CharacterContactBase(SQLModel):
    name: str
    notes: Optional[str] = None


class CharacterContact(CharacterContactBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    character_id: int = Field(foreign_key="character.id")


class CharacterContactCreate(CharacterContactBase):
    pass
