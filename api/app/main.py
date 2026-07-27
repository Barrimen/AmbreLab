"""
API commune - Plateforme JDR
Point d'entrée FastAPI. Ajoute tes routes ici au fur et à mesure des besoins.
"""

import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Type

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, select

from .database import create_db_and_tables, get_session
from .models import (
    Campaign, CampaignCreate,
    Character, CharacterCreate,
    CombatSheet, CombatSheetCreate,
    GameSession, GameSessionUpdate,
    CharacterMinorSkill, CharacterMinorSkillCreate,
    CharacterWeapon, CharacterWeaponCreate,
    CharacterWeaponMastery, CharacterWeaponMasteryCreate,
    CharacterArmorPiece, CharacterArmorPieceCreate,
    CharacterMagicSchool, CharacterMagicSchoolCreate,
    CharacterSpecialSkill, CharacterSpecialSkillCreate,
    CharacterSpell, CharacterSpellCreate,
    CharacterInventoryItem, CharacterInventoryItemCreate,
    CharacterCompanion, CharacterCompanionCreate,
    CharacterContact, CharacterContactCreate,
)
from .utils import generate_session_code, sync_combat_sheet_from_character


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
# Routes CRUD génériques pour les listes simples de la fiche de personnage.
# Évite de dupliquer le même code 11 fois (mineures, sorts, contacts...) —
# une seule fonction générique par "type de parent" (Character ou
# CombatSheet), appelée une fois par table concernée plus bas.
# ---------------------------------------------------------------------------

def register_character_child_crud(
    app: FastAPI,
    *,
    path_segment: str,
    model: Type[SQLModel],
    create_model: Type[SQLModel],
    on_change=None,
):
    """Enregistre create/list/update/delete pour une table rattachée à
    character_id. `on_change(session, character_id)` est appelé après
    chaque mutation si fourni (utilisé pour la synchro combat)."""

    base_path = f"/characters/{{character_id}}/{path_segment}"
    item_path = f"/{path_segment}/{{item_id}}"

    @app.post(base_path, response_model=model, name=f"create_{path_segment}")
    def create_item(character_id: int, item: create_model, session: Session = Depends(get_session)):
        character = session.get(Character, character_id)
        if not character:
            raise HTTPException(status_code=404, detail="Personnage introuvable")
        db_item = model.model_validate(item, update={"character_id": character_id})
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        if on_change:
            on_change(session, character_id)
            session.refresh(db_item)  # on_change commit -> objets expirés, on recharge
        return db_item

    @app.get(base_path, response_model=List[model], name=f"list_{path_segment}")
    def list_items(character_id: int, session: Session = Depends(get_session)):
        statement = select(model).where(model.character_id == character_id)
        return session.exec(statement).all()

    @app.put(item_path, response_model=model, name=f"update_{path_segment}")
    def update_item(item_id: int, item: create_model, session: Session = Depends(get_session)):
        db_item = session.get(model, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Élément introuvable")
        for key, value in item.model_dump(exclude_unset=True).items():
            setattr(db_item, key, value)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        if on_change:
            character_id = db_item.character_id
            on_change(session, character_id)
            session.refresh(db_item)  # on_change commit -> objets expirés, on recharge
        return db_item

    @app.delete(item_path, name=f"delete_{path_segment}")
    def delete_item(item_id: int, session: Session = Depends(get_session)):
        db_item = session.get(model, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Élément introuvable")
        character_id = db_item.character_id
        session.delete(db_item)
        session.commit()
        if on_change:
            on_change(session, character_id)
        return {"deleted": True}


def register_combatsheet_child_crud(
    app: FastAPI,
    *,
    path_segment: str,
    model: Type[SQLModel],
    create_model: Type[SQLModel],
    on_change=None,
):
    """Même principe que register_character_child_crud, mais rattaché à
    combat_sheet_id. `on_change(session, character_id)` reçoit le
    character_id du CombatSheet parent (pas le combat_sheet_id), pour
    rester cohérent avec la signature de sync_combat_sheet_from_character."""

    base_path = f"/combatsheets/{{combat_sheet_id}}/{path_segment}"
    item_path = f"/{path_segment}/{{item_id}}"

    def _character_id_of(session: Session, combat_sheet_id: int) -> Optional[int]:
        sheet = session.get(CombatSheet, combat_sheet_id)
        return sheet.character_id if sheet else None

    @app.post(base_path, response_model=model, name=f"create_{path_segment}")
    def create_item(combat_sheet_id: int, item: create_model, session: Session = Depends(get_session)):
        sheet = session.get(CombatSheet, combat_sheet_id)
        if not sheet:
            raise HTTPException(status_code=404, detail="Fiche de combat introuvable")
        db_item = model.model_validate(item, update={"combat_sheet_id": combat_sheet_id})
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        if on_change and sheet.character_id:
            on_change(session, sheet.character_id)
            session.refresh(db_item)  # on_change commit -> objets expirés, on recharge
        return db_item

    @app.get(base_path, response_model=List[model], name=f"list_{path_segment}")
    def list_items(combat_sheet_id: int, session: Session = Depends(get_session)):
        statement = select(model).where(model.combat_sheet_id == combat_sheet_id)
        return session.exec(statement).all()

    @app.put(item_path, response_model=model, name=f"update_{path_segment}")
    def update_item(item_id: int, item: create_model, session: Session = Depends(get_session)):
        db_item = session.get(model, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Élément introuvable")
        for key, value in item.model_dump(exclude_unset=True).items():
            setattr(db_item, key, value)
        session.add(db_item)
        session.commit()
        session.refresh(db_item)
        if on_change:
            character_id = _character_id_of(session, db_item.combat_sheet_id)
            if character_id:
                on_change(session, character_id)
                session.refresh(db_item)  # on_change commit -> objets expirés, on recharge
        return db_item

    @app.delete(item_path, name=f"delete_{path_segment}")
    def delete_item(item_id: int, session: Session = Depends(get_session)):
        db_item = session.get(model, item_id)
        if not db_item:
            raise HTTPException(status_code=404, detail="Élément introuvable")
        combat_sheet_id = db_item.combat_sheet_id
        character_id = _character_id_of(session, combat_sheet_id) if on_change else None
        session.delete(db_item)
        session.commit()
        if on_change and character_id:
            on_change(session, character_id)
        return {"deleted": True}


# ---------------------------------------------------------------------------
# Campagnes
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


@app.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int, session: Session = Depends(get_session)):
    campaign = session.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne introuvable")

    has_characters = session.exec(select(Character).where(Character.campaign_id == campaign_id)).first()
    has_sheets = session.exec(select(CombatSheet).where(CombatSheet.campaign_id == campaign_id)).first()
    has_sessions = session.exec(select(GameSession).where(GameSession.campaign_id == campaign_id)).first()
    if has_characters or has_sheets or has_sessions:
        raise HTTPException(
            status_code=400,
            detail="Impossible de supprimer : des personnages, fiches ou sessions sont encore rattachés à cette campagne.",
        )

    session.delete(campaign)
    session.commit()
    return {"deleted": True}


# ---------------------------------------------------------------------------
# Personnages, rattachés à une campagne.
# La création d'un personnage crée systématiquement un CombatSheet lié
# (vide, quick_mode) : le détail combat (armes, maîtrises, armure) a
# toujours besoin d'un CombatSheet à qui se rattacher (option A).
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

    # CombatSheet compagnon, vide pour l'instant — le joueur la remplira
    # depuis la fiche (onglet Combat) ou depuis le Cadran.
    db_sheet = CombatSheet(
        name=db_character.name,
        campaign_id=campaign_id,
        character_id=db_character.id,
        weapon_type="",
        weapon_choice="",
        weapon_quality="",
        pv_max=db_character.pv_actuel or 0,
    )
    session.add(db_sheet)
    session.commit()

    # Le commit ci-dessus expire tous les objets de la session (comportement
    # par défaut de SQLAlchemy), y compris db_character déjà rafraîchi plus
    # haut : sans ce second refresh, la sérialisation de la réponse tombe
    # sur un objet expiré une fois la session fermée par la dépendance.
    session.refresh(db_character)
    return db_character


@app.get("/campaigns/{campaign_id}/characters", response_model=List[Character])
def list_characters(campaign_id: int, session: Session = Depends(get_session)):
    statement = select(Character).where(Character.campaign_id == campaign_id)
    return session.exec(statement).all()


@app.get("/characters/{character_id}", response_model=Character)
def get_character(character_id: int, session: Session = Depends(get_session)):
    character = session.get(Character, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    return character


@app.put("/characters/{character_id}", response_model=Character)
def update_character(
    character_id: int,
    character: CharacterCreate,
    session: Session = Depends(get_session),
):
    db_character = session.get(Character, character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Personnage introuvable")
    for key, value in character.model_dump(exclude_unset=True).items():
        setattr(db_character, key, value)
    session.add(db_character)
    session.commit()
    session.refresh(db_character)
    return db_character


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


# ---------------------------------------------------------------------------
# Listes de la fiche de personnage rattachées à Character.
# ---------------------------------------------------------------------------

register_character_child_crud(
    app, path_segment="minor-skills",
    model=CharacterMinorSkill, create_model=CharacterMinorSkillCreate,
)
register_character_child_crud(
    app, path_segment="magic-schools",
    model=CharacterMagicSchool, create_model=CharacterMagicSchoolCreate,
)
register_character_child_crud(
    app, path_segment="special-skills",
    model=CharacterSpecialSkill, create_model=CharacterSpecialSkillCreate,
)
register_character_child_crud(
    app, path_segment="spells",
    model=CharacterSpell, create_model=CharacterSpellCreate,
)
register_character_child_crud(
    app, path_segment="inventory",
    model=CharacterInventoryItem, create_model=CharacterInventoryItemCreate,
)
register_character_child_crud(
    app, path_segment="companions",
    model=CharacterCompanion, create_model=CharacterCompanionCreate,
)
register_character_child_crud(
    app, path_segment="contacts",
    model=CharacterContact, create_model=CharacterContactCreate,
)

# ---------------------------------------------------------------------------
# Listes de la fiche de personnage rattachées à CombatSheet (détail combat).
# weapons et weapon-masteries déclenchent la synchro vers les champs simples
# du CombatSheet (arme équipée, maîtrise effective) à chaque mutation.
# ---------------------------------------------------------------------------

register_combatsheet_child_crud(
    app, path_segment="weapons",
    model=CharacterWeapon, create_model=CharacterWeaponCreate,
    on_change=sync_combat_sheet_from_character,
)
register_combatsheet_child_crud(
    app, path_segment="weapon-masteries",
    model=CharacterWeaponMastery, create_model=CharacterWeaponMasteryCreate,
    on_change=sync_combat_sheet_from_character,
)
register_combatsheet_child_crud(
    app, path_segment="armor-pieces",
    model=CharacterArmorPiece, create_model=CharacterArmorPieceCreate,
)
