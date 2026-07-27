"""
API commune - Plateforme JDR
Point d'entrée FastAPI. Ajoute tes routes ici au fur et à mesure des besoins.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import (
    Campaign, CampaignCreate, Character, CharacterCreate,
    CombatSheet, CombatSheetCreate, GameSession, GameSessionUpdate,
)
from .utils import generate_session_code


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


# ---------------------------------------------------------------------------
# Fiches de combat (CombatSheet) — Le Cadran des Trente Temps, campagne Elénior
# Permanentes, réutilisables d'une rencontre à l'autre. Toujours filtrées par
# campaign_id, conformément au cloisonnement par jeu/campagne.
# ---------------------------------------------------------------------------

@app.post("/campaigns/{campaign_id}/combatsheets", response_model=CombatSheet)
def create_combatsheet(
    campaign_id: int,
    sheet: CombatSheetCreate,
    session: Session = Depends(get_session),
):
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    db_sheet = CombatSheet.model_validate(sheet, update={"campaign_id": campaign_id})
    session.add(db_sheet)
    session.commit()
    session.refresh(db_sheet)
    return db_sheet


@app.get("/campaigns/{campaign_id}/combatsheets", response_model=List[CombatSheet])
def list_combatsheets(campaign_id: int, session: Session = Depends(get_session)):
    statement = select(CombatSheet).where(CombatSheet.campaign_id == campaign_id)
    return session.exec(statement).all()


@app.get("/combatsheets/{sheet_id}", response_model=CombatSheet)
def get_combatsheet(sheet_id: int, session: Session = Depends(get_session)):
    sheet = session.get(CombatSheet, sheet_id)
    if not sheet:
        raise HTTPException(status_code=404, detail="Fiche introuvable")
    return sheet


@app.put("/combatsheets/{sheet_id}", response_model=CombatSheet)
def update_combatsheet(
    sheet_id: int,
    sheet: CombatSheetCreate,
    session: Session = Depends(get_session),
):
    db_sheet = session.get(CombatSheet, sheet_id)
    if not db_sheet:
        raise HTTPException(status_code=404, detail="Fiche introuvable")
    for key, value in sheet.model_dump(exclude_unset=True).items():
        setattr(db_sheet, key, value)
    session.add(db_sheet)
    session.commit()
    session.refresh(db_sheet)
    return db_sheet


# ---------------------------------------------------------------------------
# Sessions de combat (GameSession) — état temporaire, un seul combat à la fois
# par campagne. Synchronisation par polling léger (pas de WebSocket).
# ---------------------------------------------------------------------------

@app.post("/campaigns/{campaign_id}/sessions", response_model=GameSession)
def create_session(campaign_id: int, session: Session = Depends(get_session)):
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne introuvable")
    initial_state = {
        "round": 1, "phase": "setup", "combatants": [],
        "timeline": [], "currentIndex": 0, "log": [], "pendingTarget": None,
    }
    db_session = GameSession(
        campaign_id=campaign_id,
        code=generate_session_code(),
        state=json.dumps(initial_state),
    )
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    return db_session


@app.get("/campaigns/{campaign_id}/sessions/latest", response_model=GameSession)
def get_latest_session(campaign_id: int, session: Session = Depends(get_session)):
    """Un seul combat possible à la fois pour une campagne : le client
    tombe directement dessus au chargement, sans code à saisir. Si aucune
    session n'existe encore, on en crée une vide."""
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne introuvable")

    statement = (
        select(GameSession)
        .where(GameSession.campaign_id == campaign_id)
        .order_by(GameSession.id.desc())
    )
    existing = session.exec(statement).first()
    if existing:
        return existing

    initial_state = {
        "round": 1, "phase": "setup", "combatants": [],
        "timeline": [], "currentIndex": 0, "log": [], "pendingTarget": None,
    }
    db_session = GameSession(
        campaign_id=campaign_id,
        code=generate_session_code(),
        state=json.dumps(initial_state),
    )
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    return db_session


@app.get("/sessions/{code}", response_model=GameSession)
def get_session_by_code(code: str, session: Session = Depends(get_session)):
    statement = select(GameSession).where(GameSession.code == code)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return result


@app.put("/sessions/{code}", response_model=GameSession)
def update_session_by_code(
    code: str,
    update: GameSessionUpdate,
    session: Session = Depends(get_session),
):
    statement = select(GameSession).where(GameSession.code == code)
    db_session = session.exec(statement).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    db_session.state = update.state
    db_session.updated_at = datetime.utcnow()
    session.add(db_session)
    session.commit()
    session.refresh(db_session)
    return db_session
