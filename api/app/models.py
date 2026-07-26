from typing import Optional

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
