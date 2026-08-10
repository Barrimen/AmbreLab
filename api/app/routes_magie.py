"""
Routes API de l'outil de magie d'Elenior.

A inclure dans app/main.py via :
    from app.routes_magie import router as magie_router
    app.include_router(magie_router)

Deux familles de routes :
  - POST /magie/calculer : calcul à la volée (Coût/Cast), sans écriture en
    base. Utile pour l'interface de creation de sort (aperçu en direct
    avant sauvegarde).
  - /magie/sorts/* : CRUD de la bibliotheque de sorts, persistee en base,
    filtree par campaign_id. Pas de filtrage par personnage/joueur pour la
    v1 (decision Obe du 09/08/2026, alignee sur l'acces aux personnages) :
    tout le monde dans une campagne voit tous les sorts de cette campagne.

Source de verite pour les equations : LE LIVRE (voir app/utils_magie.py
pour le detail de cette decision du 09/08/2026).
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from .database import get_session
from .models_magie import Sort, SortCreate
from .utils_magie import ComposantsSort, calculer_cout_sort, calculer_cast_sort
from .resolution_magie import resoudre_constantes, ConstanteIntrouvableError
from sqlmodel import SQLModel


router = APIRouter(prefix="/magie", tags=["magie"])


# ---------------------------------------------------------------------------
# Schéma de requête pour le calcul à la volée - pas une table, juste un
# schéma de validation d'entrée/sortie (SQLModel sans table=True)
# ---------------------------------------------------------------------------

class SortCalculRequest(SQLModel):
    type_magie: str
    aspects: list[str]          # 1 à 3 aspects
    ecoles: list[str]           # 1 à 3 écoles

    # Composants bruts du sort (voir ComposantsSort dans utils_magie.py)
    pi: float = 0.0
    pd: float = 0.0
    en: float = 0.0
    ex: float = 0.0
    nb: float = 1.0
    tz: float = 0.0
    z: float = 1.0
    po: float = 0.0

    # Caractéristique et niveaux du personnage - fournis par l'appelant
    # (dépendent du personnage, pas des tables de référence de la magie)
    cm: float                     # caractéristique magique déjà divisée par 10
    niveau_aspects: list[float]   # un Niveau d'Aspect par aspect engagé
    niveau_type: float

    # true pour l'Alchimie ou tout Type utilisant un Long-sort à la place
    # du Cast classique - dans ce cas cast_ou_long_sort n'est PAS calculé
    # ici : il doit être choisi directement dans la table
    # magie_generic_long_sort par l'appelant (palier au choix du joueur/MJ)
    est_long_sort: bool = False


class SortCalculResponse(SQLModel):
    cout_pp: float
    cast: Optional[float]  # null si est_long_sort=true (voir note ci-dessus)
    constantes_utilisees: dict  # transparence : quelles valeurs C1-C7 ont servi


@router.get("/health")
def health_magie():
    """Health check dédié à ce module, conforme à la convention du projet
    (chaque route API exposée avec un health check)."""
    return {"status": "ok", "module": "magie"}


@router.post("/calculer", response_model=SortCalculResponse)
def calculer_sort(requete: SortCalculRequest, session: Session = Depends(get_session)):
    """Calcule le Coût (et le Cast, sauf Long-sort) d'un sort à la volée,
    sans le sauvegarder. Utilisé pour l'aperçu en direct côté interface."""
    try:
        constantes = resoudre_constantes(session, requete.type_magie, requete.aspects, requete.ecoles)
    except ConstanteIntrouvableError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not requete.niveau_aspects:
        raise HTTPException(status_code=422, detail="niveau_aspects ne peut pas être vide")

    niveau_aspect_moyen = sum(requete.niveau_aspects) / len(requete.niveau_aspects)
    nv = (niveau_aspect_moyen + requete.niveau_type) / 2

    composants = ComposantsSort(
        pi=requete.pi, pd=requete.pd, en=requete.en, ex=requete.ex,
        nb=requete.nb, tz=requete.tz, z=requete.z, po=requete.po,
        cm=requete.cm, nv=nv,
    )

    # Le livre indique un minimum de 1 PP pour le Coût - appliqué ici, à la
    # frontière de l'API (calculer_cout_sort reste pur, voir utils_magie.py)
    cout = max(1.0, calculer_cout_sort(composants, constantes.c1, constantes.c2, constantes.c3, constantes.c4, constantes.c6))

    cast = None
    if not requete.est_long_sort:
        cast = calculer_cast_sort(composants, constantes.c1, constantes.c2, constantes.c3, constantes.c5, constantes.c7)

    return SortCalculResponse(
        cout_pp=cout,
        cast=cast,
        constantes_utilisees=vars(constantes),
    )


# ---------------------------------------------------------------------------
# Bibliothèque de sorts - CRUD filtré par campaign_id
# ---------------------------------------------------------------------------

@router.get("/sorts", response_model=list[Sort])
def lister_sorts(campaign_id: int, session: Session = Depends(get_session)):
    """Liste tous les sorts d'une campagne, tous personnages confondus
    (pas de filtrage par joueur pour la v1, voir en-tête de fichier)."""
    return session.exec(select(Sort).where(Sort.campaign_id == campaign_id)).all()


@router.get("/sorts/{sort_id}", response_model=Sort)
def obtenir_sort(sort_id: int, session: Session = Depends(get_session)):
    sort = session.get(Sort, sort_id)
    if sort is None:
        raise HTTPException(status_code=404, detail="Sort introuvable")
    return sort


@router.post("/sorts", response_model=Sort)
def creer_sort(sort_create: SortCreate, session: Session = Depends(get_session)):
    """Crée un sort. Les champs cout_pp/cast_ou_long_sort doivent déjà être
    calculés côté client via /magie/calculer avant l'envoi - cette route ne
    recalcule pas automatiquement (garder une frontière claire entre calcul
    et persistance, cohérent avec le choix de cache décidé le 09/08/2026)."""
    sort = Sort.model_validate(sort_create)
    session.add(sort)
    session.commit()
    session.refresh(sort)  # évite le bug d'expiration SQLAlchemy sur double-commit
    return sort


@router.put("/sorts/{sort_id}", response_model=Sort)
def modifier_sort(sort_id: int, sort_create: SortCreate, session: Session = Depends(get_session)):
    sort = session.get(Sort, sort_id)
    if sort is None:
        raise HTTPException(status_code=404, detail="Sort introuvable")
    for champ, valeur in sort_create.model_dump().items():
        setattr(sort, champ, valeur)
    session.add(sort)
    session.commit()
    session.refresh(sort)
    return sort


@router.delete("/sorts/{sort_id}")
def supprimer_sort(sort_id: int, session: Session = Depends(get_session)):
    sort = session.get(Sort, sort_id)
    if sort is None:
        raise HTTPException(status_code=404, detail="Sort introuvable")
    session.delete(sort)
    session.commit()
    return {"ok": True}
