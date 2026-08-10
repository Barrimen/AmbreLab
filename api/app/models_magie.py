"""
Modeles de l'outil de magie d'Elenior (AmbreLab).

Ce module suit le pattern XxxBase / Xxx(table=True) / XxxCreate deja en place
dans app/models.py. A FUSIONNER dans app/models.py une fois valide (propose
comme fichier separe ici pour faciliter la relecture).

Deux familles de tables :
  1. Tables de REFERENCE (constantes de magie) : pas de campaign_id, ce sont
     des donnees systeme issues du livre de regles, ecrites une seule fois
     par le script d'import (scripts/import_constantes_magie.py, a venir)
     et non modifiees en jeu. Option 1 retenue avec Obe le 09/08/2026 :
     une ligne par valeur plutot qu'un blob JSON, pour rester requetable et
     corrigible en SQL depuis l'interface Data de Railway.
  2. Table de JEU (Sort) : campaign_id + character_id obligatoires, suit les
     conventions de cloisonnement d'AmbreLab. Pas de filtrage par joueur pour
     la v1 (decision Obe du 09/08/2026, alignee sur l'acces aux personnages) :
     toute route de listing renvoie tous les sorts de la campagne.

Sources : livre "Les Compagnons de l'Infortune 2026" (chapitre IV) et
Tableur_Jeff_Le_Corbeau.xlsx, croises - voir recap-extraction-magie-elenior.md
pour le detail de l'extraction et les points encore ouverts avec Elise
(decalages C1/C2/C3, terme +En, usage de la Resistance magique).
"""

from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


# ---------------------------------------------------------------------------
# 1. CONSTANTES C1 A C7 - coeur des deux equations (Cout et Cast)
# ---------------------------------------------------------------------------

class MagieC1Base(SQLModel):
    """C1 : constante Aspect x Ecole, partagee par tous les Types."""
    aspect: str
    ecole: str
    valeur: float


class MagieC1(MagieC1Base, table=True):
    __tablename__ = "magie_c1_aspect_ecole"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieC1Create(MagieC1Base):
    pass


class MagieC2Base(SQLModel):
    """C2 : constante Type x Aspect."""
    type_magie: str
    aspect: str
    valeur: float


class MagieC2(MagieC2Base, table=True):
    __tablename__ = "magie_c2_type_aspect"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieC2Create(MagieC2Base):
    pass


class MagieC3Base(SQLModel):
    """C3 : constante Type x Ecole."""
    type_magie: str
    ecole: str
    valeur: float


class MagieC3(MagieC3Base, table=True):
    __tablename__ = "magie_c3_type_ecole"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieC3Create(MagieC3Base):
    pass


class MagieC4C5Base(SQLModel):
    """C4 (Cout) et C5 (Cast), fixes par Type de magie."""
    type_magie: str
    c4_cout: float
    c5_cast: float


class MagieC4C5(MagieC4C5Base, table=True):
    __tablename__ = "magie_c4_c5_type"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieC4C5Create(MagieC4C5Base):
    pass


class MagieC6C7Base(SQLModel):
    """C6 (Cout) et C7 (Cast), fixes par Aspect de magie."""
    aspect: str
    c6_cout: float
    c7_cast: float


class MagieC6C7(MagieC6C7Base, table=True):
    __tablename__ = "magie_c6_c7_aspect"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieC6C7Create(MagieC6C7Base):
    pass


# ---------------------------------------------------------------------------
# 2. TABLES GENERIQUES - un groupe = une table, forme commune (palier, valeur)
#
# Ces tables partagent toutes la meme forme (une etiquette de palier + un
# cout en PP), mais restent des tables separees et explicitement nommees :
# elles decrivent des concepts distincts du systeme (duree, portee, nombre
# de cibles...) et les regrouper aurait pu recreer le risque de confusion
# rencontre pendant l'extraction (Resistance magique vs Resistance aux
# degats, deux tables au nom proche mais au role totalement different).
# ---------------------------------------------------------------------------

class MagieGenericNbBase(SQLModel):
    """Nombre de cibles touchées (Nb)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericNb(MagieGenericNbBase, table=True):
    __tablename__ = "magie_generic_nb"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericNbCreate(MagieGenericNbBase):
    pass


class MagieGenericTzBase(SQLModel):
    """Taille de la zone (Tz)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericTz(MagieGenericTzBase, table=True):
    __tablename__ = "magie_generic_tz"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericTzCreate(MagieGenericTzBase):
    pass


class MagieGenericFormeZoneBase(SQLModel):
    """Forme de la zone (Z) - 6 formes géométriques."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericFormeZone(MagieGenericFormeZoneBase, table=True):
    __tablename__ = "magie_generic_forme_zone"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericFormeZoneCreate(MagieGenericFormeZoneBase):
    pass


class MagieGenericDureeCombatBase(SQLModel):
    """Durée du sort (D) - combat, en temps/tours."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericDureeCombat(MagieGenericDureeCombatBase, table=True):
    __tablename__ = "magie_generic_duree_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericDureeCombatCreate(MagieGenericDureeCombatBase):
    pass


class MagieGenericDureeHorsCombatBase(SQLModel):
    """Durée du sort (D) - hors-combat, en secondes/minutes/heures."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericDureeHorsCombat(MagieGenericDureeHorsCombatBase, table=True):
    __tablename__ = "magie_generic_duree_hors_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericDureeHorsCombatCreate(MagieGenericDureeHorsCombatBase):
    pass


class MagieGenericPorteeCombatBase(SQLModel):
    """Portée (Po) - combat."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericPorteeCombat(MagieGenericPorteeCombatBase, table=True):
    __tablename__ = "magie_generic_portee_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericPorteeCombatCreate(MagieGenericPorteeCombatBase):
    pass


class MagieGenericPorteeHorsCombatBase(SQLModel):
    """Portée (Po) - hors-combat."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericPorteeHorsCombat(MagieGenericPorteeHorsCombatBase, table=True):
    __tablename__ = "magie_generic_portee_hors_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericPorteeHorsCombatCreate(MagieGenericPorteeHorsCombatBase):
    pass


class MagieGenericControleActionCombatBase(SQLModel):
    """Contrôle d'action (Ex) - combat."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericControleActionCombat(MagieGenericControleActionCombatBase, table=True):
    __tablename__ = "magie_generic_controle_action_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericControleActionCombatCreate(MagieGenericControleActionCombatBase):
    pass


class MagieGenericControleActionHorsCombatBase(SQLModel):
    """Contrôle d'action (Ex) - hors-combat."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericControleActionHorsCombat(MagieGenericControleActionHorsCombatBase, table=True):
    __tablename__ = "magie_generic_controle_action_hors_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericControleActionHorsCombatCreate(MagieGenericControleActionHorsCombatBase):
    pass


class MagieGenericControleActionRuniqueEnchantBase(SQLModel):
    """Contrôle d'action - spécial Runique et Enchantement."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericControleActionRuniqueEnchant(MagieGenericControleActionRuniqueEnchantBase, table=True):
    __tablename__ = "magie_generic_controle_action_runique_enchant"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericControleActionRuniqueEnchantCreate(MagieGenericControleActionRuniqueEnchantBase):
    pass


class MagieGenericPiegeRuniqueCombatBase(SQLModel):
    """Piège runique - combat."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericPiegeRuniqueCombat(MagieGenericPiegeRuniqueCombatBase, table=True):
    __tablename__ = "magie_generic_piege_runique_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericPiegeRuniqueCombatCreate(MagieGenericPiegeRuniqueCombatBase):
    pass


class MagieGenericPiegeRuniqueHorsCombatBase(SQLModel):
    """Piège runique - hors-combat."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericPiegeRuniqueHorsCombat(MagieGenericPiegeRuniqueHorsCombatBase, table=True):
    __tablename__ = "magie_generic_piege_runique_hors_combat"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericPiegeRuniqueHorsCombatCreate(MagieGenericPiegeRuniqueHorsCombatBase):
    pass


class MagieGenericDeEffetBase(SQLModel):
    """Dé d'effet (D2 à D20)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericDeEffet(MagieGenericDeEffetBase, table=True):
    __tablename__ = "magie_generic_de_effet"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericDeEffetCreate(MagieGenericDeEffetBase):
    pass


class MagieGenericBaseEffetBase(SQLModel):
    """Base d'effet (Base 2 à Base 6)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericBaseEffet(MagieGenericBaseEffetBase, table=True):
    __tablename__ = "magie_generic_base_effet"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericBaseEffetCreate(MagieGenericBaseEffetBase):
    pass


class MagieGenericPaliersEffet13Base(SQLModel):
    """Paliers d'"effets autres" à 13 niveaux (Nul à Divin) - réutilisée aussi pour Réinitialisation postérieure et Solidification temporaire."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericPaliersEffet13(MagieGenericPaliersEffet13Base, table=True):
    __tablename__ = "magie_generic_paliers_effet_13"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericPaliersEffet13Create(MagieGenericPaliersEffet13Base):
    pass


class MagieGenericResistanceDegatsBase(SQLModel):
    """Résistance aux dégâts (E) - effet sommé dans Pi/Pd."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericResistanceDegats(MagieGenericResistanceDegatsBase, table=True):
    __tablename__ = "magie_generic_resistance_degats"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericResistanceDegatsCreate(MagieGenericResistanceDegatsBase):
    pass


class MagieGenericResistanceMagiqueBase(SQLModel):
    """Résistance magique (Rm) - absente des variables de l'équation, usage exact à confirmer avec Elise."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericResistanceMagique(MagieGenericResistanceMagiqueBase, table=True):
    __tablename__ = "magie_generic_resistance_magique"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericResistanceMagiqueCreate(MagieGenericResistanceMagiqueBase):
    pass


class MagieGenericReinitImmediateBase(SQLModel):
    """Réinitialisation immédiate de la matière (Ex)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericReinitImmediate(MagieGenericReinitImmediateBase, table=True):
    __tablename__ = "magie_generic_reinit_immediate"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericReinitImmediateCreate(MagieGenericReinitImmediateBase):
    pass


class MagieGenericSolidificationPermanenteBase(SQLModel):
    """Solidification permanente de la matière (E)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericSolidificationPermanente(MagieGenericSolidificationPermanenteBase, table=True):
    __tablename__ = "magie_generic_solidification_permanente"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericSolidificationPermanenteCreate(MagieGenericSolidificationPermanenteBase):
    pass


class MagieGenericDureeConservationAlchimieBase(SQLModel):
    """Durée de conservation d'une potion - péremption (Alchimie)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericDureeConservationAlchimie(MagieGenericDureeConservationAlchimieBase, table=True):
    __tablename__ = "magie_generic_duree_conservation_alchimie"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericDureeConservationAlchimieCreate(MagieGenericDureeConservationAlchimieBase):
    pass


class MagieGenericLongSortBase(SQLModel):
    """Long-sort (E) - remplace le Cast pour l'Alchimie."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericLongSort(MagieGenericLongSortBase, table=True):
    __tablename__ = "magie_generic_long_sort"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericLongSortCreate(MagieGenericLongSortBase):
    pass


class MagieGenericActionPhysiqueExBase(SQLModel):
    """Action physique combinée à un sort (Ex), par arme/caractéristique."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericActionPhysiqueEx(MagieGenericActionPhysiqueExBase, table=True):
    __tablename__ = "magie_generic_action_physique_ex"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericActionPhysiqueExCreate(MagieGenericActionPhysiqueExBase):
    pass


class MagieGenericArretCastBase(SQLModel):
    """Arrêt du cast d'un sort (E)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericArretCast(MagieGenericArretCastBase, table=True):
    __tablename__ = "magie_generic_arret_cast"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericArretCastCreate(MagieGenericArretCastBase):
    pass


class MagieGenericNiveauAspectTypePrixBase(SQLModel):
    """Coût en points d'attribut par niveau d'Aspect/Type de magie (Nv 1 à 10)."""
    palier: str
    valeur: Optional[float] = None  # None = "Immédiat" ou "/" (pas de coût)


class MagieGenericNiveauAspectTypePrix(MagieGenericNiveauAspectTypePrixBase, table=True):
    __tablename__ = "magie_generic_niveau_aspect_type_prix"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieGenericNiveauAspectTypePrixCreate(MagieGenericNiveauAspectTypePrixBase):
    pass


# ---------------------------------------------------------------------------
# 2bis. Tables d'entrave - forme un peu differente (deux composantes en jeu),
# gardees explicites plutot que forcees dans le pattern generique ci-dessus.
# ---------------------------------------------------------------------------

class MagieEntraveResistancePhysiqueBase(SQLModel):
    """Entrave Physique - Resistance (EnPR), en points de vie de l'entrave
    (une coque de terre ou une liane a des PV et peut etre brisee)."""
    points_vie: int
    valeur: float


class MagieEntraveResistancePhysique(MagieEntraveResistancePhysiqueBase, table=True):
    __tablename__ = "magie_entrave_resistance_physique"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieEntraveResistancePhysiqueCreate(MagieEntraveResistancePhysiqueBase):
    pass


class MagieEntraveCaracBase(SQLModel):
    """Commune a EnPC (Entrave Physique - Carac.) et EnMC (Entrave Mentale -
    Carac.) : un pourcentage de malus/bonus au jet + son cout. Le champ
    type_entrave distingue les deux plutot que dupliquer la table."""
    type_entrave: str  # "physique" | "mentale"
    pourcentage: str    # ex. "+20%", "-90%", "Impossible"
    valeur: float


class MagieEntraveCarac(MagieEntraveCaracBase, table=True):
    __tablename__ = "magie_entrave_carac"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieEntraveCaracCreate(MagieEntraveCaracBase):
    pass


class MagieEntravePartieCorpsBase(SQLModel):
    """Partie du corps entravee (Pce)."""
    partie: str
    valeur: float


class MagieEntravePartieCorps(MagieEntravePartieCorpsBase, table=True):
    __tablename__ = "magie_entrave_partie_corps"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieEntravePartieCorpsCreate(MagieEntravePartieCorpsBase):
    pass


class MagieFrequenceApplicationBase(SQLModel):
    """Frequence d'application (F) et Nombre d'application (Napp) : meme
    forme, regroupees dans une table via type_constante car toujours
    utilisees ensemble dans le calcul de Pd."""
    type_constante: str  # "frequence" | "nombre_application"
    palier: str
    valeur: float


class MagieFrequenceApplication(MagieFrequenceApplicationBase, table=True):
    __tablename__ = "magie_frequence_application"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieFrequenceApplicationCreate(MagieFrequenceApplicationBase):
    pass


class MagieBonusCaracteristiqueBase(SQLModel):
    """Bonus de caracteristique (E) : categorie mineure/maitrise vs majeure,
    avec variantes critiques."""
    categorie: str  # "mineure_maitrise" | "majeure"
    palier: str      # ex. "+/-10%", "+/-5% Crit"
    valeur: float


class MagieBonusCaracteristique(MagieBonusCaracteristiqueBase, table=True):
    __tablename__ = "magie_bonus_caracteristique"
    id: Optional[int] = Field(default=None, primary_key=True)


class MagieBonusCaracteristiqueCreate(MagieBonusCaracteristiqueBase):
    pass


# ---------------------------------------------------------------------------
# 3. TABLE DE JEU - sorts crees par les joueurs/MJ
# ---------------------------------------------------------------------------

class SortBase(SQLModel):
    campaign_id: int = Field(foreign_key="campaign.id")
    character_id: int = Field(foreign_key="character.id")

    nom: str
    type_magie: str

    # Jusqu'a 3 aspects et 3 ecoles (regle des sorts complexes, voir recap §3)
    aspects: list[str] = Field(sa_column=Column(JSON))
    ecoles: list[str] = Field(sa_column=Column(JSON))

    # Composants bruts de calcul saisis par le joueur (des, base, effets,
    # duree, portee, nombre de cibles, zone, entrave, etc.) - stockes en JSON
    # plutot qu'en colonnes separees : ces composants varient selon le sort
    # (un sort n'utilise jamais tous les effets possibles a la fois), et la
    # liste des effets possibles est deja entierement decrite par les tables
    # de reference ci-dessus. Reproduire chaque colonne du tableur en colonne
    # SQL forcerait une table a des centaines de colonnes presque toutes
    # vides. Le detail attendu de ce JSON sera fixe au moment de coder les
    # fonctions de calcul dans app/utils.py.
    composants: dict = Field(sa_column=Column(JSON))

    # Resultats calcules et mis en cache (recalcules a chaque modification du
    # sort plutot qu'a la volee a chaque lecture, pour eviter de refaire le
    # calcul complet a chaque affichage de la bibliotheque)
    cout_pp: float
    cast_ou_long_sort: float
    est_long_sort: bool = False  # true pour l'Alchimie (remplace le cast)

    notes: Optional[str] = None


class Sort(SortBase, table=True):
    __tablename__ = "sort"
    id: Optional[int] = Field(default=None, primary_key=True)


class SortCreate(SortBase):
    pass
