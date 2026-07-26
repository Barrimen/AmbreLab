"""
API commune - Plateforme JDR
Point d'entrée FastAPI. Ajoute tes routes ici au fur et à mesure des besoins.
"""

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import Campaign, CampaignCreate, Character, CharacterCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée les tables au démarrage si elles n'existent pas encore.
    # Suffisant pour démarrer ; passe à Alembic (migrations) si le schéma
    # devient complexe ou si tu veux des migrations versionnées propres.
    create_db_and_tables()
    yield


app = FastAPI(title="API JDR", lifespan=lifespan)

# CORS ouvert pour commencer (tes pages statiques sur Cloudflare Pages
# doivent pouvoir appeler cette API depuis un autre sous-domaine).
# Resserre `allow_origins` à ton domaine une fois en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Utilisé par Railway pour vérifier que le service est vivant."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Exemple : campagnes
# ---------------------------------------------------------------------------

@app.post("/campaigns", response_model=Campaign)
def create_campaign(campaign: CampaignCreate, session: Session = Depends(get_session)):
    db_campaign = Campaign.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return db_campaign


@app.get("/campaigns", response_model=List[Campaign])
def list_campaigns(session: Session = Depends(get_session)):
    return session.exec(select(Campaign)).all()


@app.get("/campaigns/{campaign_id}", response_model=Campaign)
def get_campaign(campaign_id: int, session: Session = Depends(get_session)):
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    return campaign


# ---------------------------------------------------------------------------
# Exemple : personnages, rattachés à une campagne
# ---------------------------------------------------------------------------

@app.post("/campaigns/{campaign_id}/characters", response_model=Character)
def create_character(
    campaign_id: int,
    character: CharacterCreate,
    session: Session = Depends(get_session),
):
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    db_character = Character.model_validate(character, update={"campaign_id": campaign_id})
    session.add(db_character)
    session.commit()
    session.refresh(db_character)
    return db_character


@app.get("/campaigns/{campaign_id}/characters", response_model=List[Character])
def list_characters(campaign_id: int, session: Session = Depends(get_session)):
    statement = select(Character).where(Character.campaign_id == campaign_id)
    return session.exec(statement).all()
