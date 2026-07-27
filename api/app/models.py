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

class CharacterBase(SQLModel):
    name: str
    player_name: Optional[str] = None
    # Adresse vers R2 plutôt que le fichier lui-même (cf. séparation
    # BDD / stockage fichiers qu'on a actée).
    sheet_file_url: Optional[str] = None
    notes: Optional[str] = None


class Character(CharacterBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id")


class CharacterCreate(CharacterBase):
    pass


# ---------------------------------------------------------------------------
# Fiche de combat (permanente, réutilisable d'une rencontre à l'autre)
# Ajoutée pour Le Cadran des Trente Temps (campagne Elénior).
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
