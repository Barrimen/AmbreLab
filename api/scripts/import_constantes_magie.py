"""
Import des constantes de magie d'Elenior vers Postgres (Railway).

DECISION DU 09/08/2026 : source de verite = LIVRE de regles, pas le tableur
d'Elise (voir app/utils.py pour le detail de cette decision). Les fichiers
JSON lus ici ont ete transcrits et valides visuellement depuis le livre
"Les Compagnons de l'Infortune 2026" (chapitre IV), PAS extraits du tableur.

Usage :
    python scripts/import_constantes_magie.py --database-url postgresql://...
    python scripts/import_constantes_magie.py --dry-run   # verification locale sans ecrire en base

Le script est idempotent : il vide chaque table de reference avant de la
repeupler (DELETE puis INSERT), pour pouvoir etre relance sans dupliquer les
lignes si une correction de valeur doit etre appliquee plus tard suite a un
retour d'Elise.

Ce script ne touche a aucune donnee de jeu (table `sort`) - uniquement aux
tables de reference (magie_c1_aspect_ecole, magie_generic_*, etc.).
"""

import argparse
import json
import sys
from pathlib import Path

from sqlmodel import SQLModel, Session, create_engine, delete

# Ce script est pensé pour vivre dans api/scripts/, à côté de son dossier
# data_magie/. Il est lancé en autonome (pas via uvicorn), donc le package
# "app" (qui vit dans api/app/) doit être ajouté au path explicitement.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models_magie import (
    MagieC1, MagieC2, MagieC3, MagieC4C5, MagieC6C7,
    MagieEntraveResistancePhysique, MagieEntraveCarac, MagieEntravePartieCorps,
    MagieFrequenceApplication, MagieBonusCaracteristique,
    # Les 24 tables generiques (une classe par fichier JSON, meme nommage)
    MagieGenericNb, MagieGenericTz, MagieGenericFormeZone,
    MagieGenericDureeCombat, MagieGenericDureeHorsCombat,
    MagieGenericPorteeCombat, MagieGenericPorteeHorsCombat,
    MagieGenericControleActionCombat, MagieGenericControleActionHorsCombat,
    MagieGenericControleActionRuniqueEnchant,
    MagieGenericPiegeRuniqueCombat, MagieGenericPiegeRuniqueHorsCombat,
    MagieGenericDeEffet, MagieGenericBaseEffet, MagieGenericPaliersEffet13,
    MagieGenericResistanceDegats, MagieGenericResistanceMagique,
    MagieGenericReinitImmediate, MagieGenericSolidificationPermanente,
    MagieGenericDureeConservationAlchimie, MagieGenericLongSort,
    MagieGenericActionPhysiqueEx, MagieGenericArretCast,
    MagieGenericNiveauAspectTypePrix,
)

DATA_DIR = Path(__file__).parent / "data_magie"


def charger_json(nom_fichier: str) -> dict:
    """Charge un fichier JSON de constantes, avec message d'erreur clair
    si le fichier attendu est absent (plutot qu'une KeyError opaque plus
    loin dans le script)."""
    chemin = DATA_DIR / nom_fichier
    if not chemin.exists():
        raise FileNotFoundError(
            f"Fichier de constantes introuvable : {chemin}\n"
            f"Verifier que le zip constantes-magie-json.zip a bien ete "
            f"decompresse dans {DATA_DIR}"
        )
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def importer_c1(session: Session):
    """C1 : Aspect x Ecole (108 valeurs attendues, 12 aspects x 9 ecoles)."""
    data = charger_json("c1_aspect_ecole.json")
    session.exec(delete(MagieC1))
    n = 0
    for aspect, ecoles in data.items():
        for ecole, valeur in ecoles.items():
            session.add(MagieC1(aspect=aspect, ecole=ecole, valeur=valeur))
            n += 1
    assert n == 108, f"C1 : {n} valeurs importees, 108 attendues - verifier la source"
    print(f"  C1 : {n} valeurs importees")


def importer_c2(session: Session):
    """C2 : Type x Aspect (204 valeurs attendues, 17 types x 12 aspects)."""
    data = charger_json("c2_type_aspect.json")
    session.exec(delete(MagieC2))
    n = 0
    for type_magie, aspects in data.items():
        for aspect, valeur in aspects.items():
            session.add(MagieC2(type_magie=type_magie, aspect=aspect, valeur=valeur))
            n += 1
    assert n == 204, f"C2 : {n} valeurs importees, 204 attendues - verifier la source"
    print(f"  C2 : {n} valeurs importees")


def importer_c3(session: Session):
    """C3 : Type x Ecole (153 valeurs attendues, 17 types x 9 ecoles)."""
    data = charger_json("c3_type_ecole.json")
    session.exec(delete(MagieC3))
    n = 0
    for type_magie, ecoles in data.items():
        for ecole, valeur in ecoles.items():
            session.add(MagieC3(type_magie=type_magie, ecole=ecole, valeur=valeur))
            n += 1
    assert n == 153, f"C3 : {n} valeurs importees, 153 attendues - verifier la source"
    print(f"  C3 : {n} valeurs importees")


def importer_c4_c5(session: Session):
    """C4/C5 : par Type (34 valeurs attendues, 17 types x 2)."""
    data = charger_json("c4_c5_type.json")
    session.exec(delete(MagieC4C5))
    n = 0
    for type_magie, valeurs in data.items():
        session.add(MagieC4C5(
            type_magie=type_magie,
            c4_cout=valeurs["C4"],
            c5_cast=valeurs["C5"],
        ))
        n += 1
    assert n == 17, f"C4/C5 : {n} types importes, 17 attendus - verifier la source"
    print(f"  C4/C5 : {n} types importes")


def importer_c6_c7(session: Session):
    """C6/C7 : par Aspect (24 valeurs attendues, 12 aspects x 2)."""
    data = charger_json("c6_c7_aspect.json")
    session.exec(delete(MagieC6C7))
    n = 0
    for aspect, valeurs in data.items():
        session.add(MagieC6C7(
            aspect=aspect,
            c6_cout=valeurs["C6"],
            c7_cast=valeurs["C7"],
        ))
        n += 1
    assert n == 12, f"C6/C7 : {n} aspects importes, 12 attendus - verifier la source"
    print(f"  C6/C7 : {n} aspects importes")


def importer_entrave(session: Session):
    """4 tables d'entrave - forme un peu differente du pattern generique."""
    data = charger_json("generic_entrave_resistance_physique.json")
    session.exec(delete(MagieEntraveResistancePhysique))
    for points_vie, valeur in data.items():
        session.add(MagieEntraveResistancePhysique(points_vie=int(points_vie), valeur=valeur))
    print(f"  Entrave resistance physique : {len(data)} valeurs")

    session.exec(delete(MagieEntraveCarac))
    n = 0
    for type_entrave, fichier in [("physique", "generic_entrave_carac_physique.json"),
                                    ("mentale", "generic_entrave_carac_mentale.json")]:
        data = charger_json(fichier)
        for pourcentage, valeur in data.items():
            session.add(MagieEntraveCarac(type_entrave=type_entrave, pourcentage=pourcentage, valeur=valeur))
            n += 1
    print(f"  Entrave carac (physique+mentale) : {n} valeurs")

    data = charger_json("generic_entrave_partie_corps.json")
    session.exec(delete(MagieEntravePartieCorps))
    for partie, valeur in data.items():
        session.add(MagieEntravePartieCorps(partie=partie, valeur=valeur))
    print(f"  Entrave partie du corps : {len(data)} valeurs")

    session.exec(delete(MagieFrequenceApplication))
    n = 0
    for type_constante, fichier in [("nombre_application", "generic_nombre_application.json"),
                                      ("frequence", "generic_frequence_application.json")]:
        data = charger_json(fichier)
        for palier, valeur in data.items():
            session.add(MagieFrequenceApplication(type_constante=type_constante, palier=palier, valeur=valeur))
            n += 1
    print(f"  Frequence/Nombre application : {n} valeurs")


def importer_bonus_caracteristique(session: Session):
    data = charger_json("generic_bonus_caracteristique.json")
    session.exec(delete(MagieBonusCaracteristique))
    n = 0
    for categorie, paliers in data.items():
        for palier, valeur in paliers.items():
            session.add(MagieBonusCaracteristique(categorie=categorie, palier=palier, valeur=valeur))
            n += 1
    print(f"  Bonus caracteristique : {n} valeurs")


# Tables generiques : (nom du fichier JSON, classe SQLModel correspondante)
# Meme liste que GENERIC_TABLE_NAMES dans models_magie.py, associee a sa classe.
TABLES_GENERIQUES = [
    ("generic_nb.json", MagieGenericNb),
    ("generic_tz.json", MagieGenericTz),
    ("generic_forme_zone.json", MagieGenericFormeZone),
    ("generic_duree.json", MagieGenericDureeCombat),
    ("generic_duree_hc.json", MagieGenericDureeHorsCombat),
    ("generic_portee.json", MagieGenericPorteeCombat),
    ("generic_portee_hc.json", MagieGenericPorteeHorsCombat),
    ("generic_controle_action_ex_combat.json", MagieGenericControleActionCombat),
    ("generic_controle_action_ex_horscombat.json", MagieGenericControleActionHorsCombat),
    ("generic_controle_action_runique_enchant.json", MagieGenericControleActionRuniqueEnchant),
    ("generic_piege_runique_combat.json", MagieGenericPiegeRuniqueCombat),
    ("generic_piege_runique_horscombat.json", MagieGenericPiegeRuniqueHorsCombat),
    ("generic_de_effet.json", MagieGenericDeEffet),
    ("generic_base_effet.json", MagieGenericBaseEffet),
    ("generic_paliers_effet_13.json", MagieGenericPaliersEffet13),
    ("generic_resistance_degats.json", MagieGenericResistanceDegats),
    ("generic_resistance_magique_Rm.json", MagieGenericResistanceMagique),
    ("generic_reinit_immediate.json", MagieGenericReinitImmediate),
    ("generic_solidification_permanente.json", MagieGenericSolidificationPermanente),
    ("generic_duree_conservation_alchimie.json", MagieGenericDureeConservationAlchimie),
    ("generic_long_sort.json", MagieGenericLongSort),
    ("generic_action_physique_ex.json", MagieGenericActionPhysiqueEx),
    ("generic_arret_cast.json", MagieGenericArretCast),
    ("niveau_aspect_type_prix.json", MagieGenericNiveauAspectTypePrix),
]


def importer_tables_generiques(session: Session):
    for nom_fichier, modele in TABLES_GENERIQUES:
        data = charger_json(nom_fichier)
        session.exec(delete(modele))
        n = 0
        for palier, valeur in data.items():
            session.add(modele(palier=palier, valeur=valeur))
            n += 1
        print(f"  {modele.__tablename__} : {n} valeurs")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", help="URL Postgres complete (Railway)")
    parser.add_argument("--dry-run", action="store_true",
                         help="Charge et valide les JSON sans se connecter a une base "
                              "(verifie les comptes attendus, utile avant un import reel)")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN - verification des fichiers source uniquement ===")
        for nom in ["c1_aspect_ecole.json", "c2_type_aspect.json", "c3_type_ecole.json",
                    "c4_c5_type.json", "c6_c7_aspect.json"] + [f for f, _ in TABLES_GENERIQUES]:
            data = charger_json(nom)
            print(f"  OK - {nom} lisible ({len(data)} entrees de premier niveau)")
        print("Dry run termine sans erreur.")
        return

    if not args.database_url:
        print("Erreur : --database-url requis (ou utiliser --dry-run)", file=sys.stderr)
        sys.exit(1)

    engine = create_engine(args.database_url)
    # Pas de SQLModel.metadata.create_all() ici volontairement : ce script
    # n'importe que les modèles de magie, donc sa propre métadonnée ne
    # connaît pas Campaign/Character (définis dans app/models.py) et un
    # create_all() local échouerait à résoudre la clé étrangère de Sort
    # vers character.id (trouvé en testant l'installation le 09/08/2026).
    # Les tables sont déjà créées par le démarrage normal de l'API
    # (lifespan -> create_db_and_tables() dans app/main.py, qui importe
    # tous les modèles réels) - lancer ce script APRÈS avoir démarré l'API
    # au moins une fois.

    with Session(engine) as session:
        print("Import des constantes de magie (source : livre de regles)...")
        importer_c1(session)
        importer_c2(session)
        importer_c3(session)
        importer_c4_c5(session)
        importer_c6_c7(session)
        importer_entrave(session)
        importer_bonus_caracteristique(session)
        importer_tables_generiques(session)
        session.commit()
        print("Import termine avec succes.")


if __name__ == "__main__":
    main()
