"""
Résolution des constantes de magie (C1-C7) depuis les tables de référence
Postgres, pour un sort donné (Type + Aspects + Écoles).

Séparé de app/utils_magie.py : ce module fait des requêtes BDD, alors que
utils_magie.py reste volontairement pur (aucune dépendance BDD, testable en
isolation). Convention de sobriété du projet : pas de duplication entre
calcul pur et accès aux données.

⚠️ CONVENTIONS NON CONFIRMÉES PAR LE LIVRE - à valider avec Elise avant mise
en prod si des sorts multi-aspects ET multi-écoles simultanément deviennent
courants :
  - Le livre (p.145) documente la règle du "maximum" pour C1 sur plusieurs
    Aspects, et séparément pour C1 sur plusieurs Écoles - mais ne dit rien
    du cas combiné (plusieurs Aspects ET plusieurs Écoles à la fois). Ici,
    on prend le maximum sur TOUTES les paires (Aspect,École) possibles du
    sort, ce qui redonne exactement la règle du livre quand une seule des
    deux dimensions varie, mais reste une extrapolation dans le cas combiné.
  - C3 sur plusieurs Écoles : le livre ne documente explicitement que le cas
    C1. La règle du maximum appliquée ici à C3 est une convention déduite du
    comportement observé dans le tableur (voir incoherences-livre-vs-tableur-
    EXHAUSTIF.md §"C2 et C3 cohérents avec la règle du max").
  - C6/C7 sur plusieurs Aspects : même situation, règle du maximum appliquée
    par convention, non explicitement confirmée par le livre (point resté
    ouvert dans recap-extraction-magie-elenior.md §6).
"""

from dataclasses import dataclass

import unicodedata

from sqlmodel import Session, select

from .models_magie import MagieC1, MagieC2, MagieC3, MagieC4C5, MagieC6C7


def _normaliser(texte: str) -> str:
    """Retire les accents et met en minuscule, pour comparer des noms
    d'Aspect/École/Type sans dépendre de leur orthographe exacte.

    BUG RÉEL trouvé en testant l'API de bout en bout (09/08/2026) : les
    tables de référence ont été importées avec des noms d'aspects SANS
    accent (ex. "Electricite", "Lumiere") suite à un choix de transcription
    initial, alors qu'un client enverra naturellement "Électricité",
    "Lumière" avec leurs accents. Plutôt que de ré-importer toutes les
    tables avec la bonne orthographe (risque de casser autre chose sans
    bénéfice réel), la comparaison est normalisée ici, à la frontière de
    la résolution - c'est aussi ce qui rend l'API tolérante si un futur
    client envoie une variante d'accentuation légèrement différente."""
    sans_accents = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("ascii")
    return sans_accents.strip().lower()


class ConstanteIntrouvableError(Exception):
    """Levée si une combinaison Type/Aspect/École n'existe pas dans les
    tables de référence - typiquement un nom mal orthographié envoyé par
    le client plutôt qu'une vraie absence de donnée (les tables sont
    complètes pour tous les Types/Aspects/Écoles officiels)."""
    pass


@dataclass
class ConstantesResolues:
    c1: float
    c2: float
    c3: float
    c4: float
    c5: float
    c6: float
    c7: float


# Tables de référence de petite taille (108 à 204 lignes max) : on charge
# tout en mémoire et on compare via _normaliser plutôt que de multiplier les
# allers-retours SQL avec des LOWER()/UNACCENT() dépendants du moteur BDD.
# Revoir cette approche si ces tables grossissent significativement.

def _get_c1(session: Session, aspect: str, ecole: str) -> float:
    a_norm, e_norm = _normaliser(aspect), _normaliser(ecole)
    for row in session.exec(select(MagieC1)).all():
        if _normaliser(row.aspect) == a_norm and _normaliser(row.ecole) == e_norm:
            return row.valeur
    raise ConstanteIntrouvableError(f"C1 introuvable pour Aspect={aspect!r} / École={ecole!r}")


def _get_c2(session: Session, type_magie: str, aspect: str) -> float:
    t_norm, a_norm = _normaliser(type_magie), _normaliser(aspect)
    for row in session.exec(select(MagieC2)).all():
        if _normaliser(row.type_magie) == t_norm and _normaliser(row.aspect) == a_norm:
            return row.valeur
    raise ConstanteIntrouvableError(f"C2 introuvable pour Type={type_magie!r} / Aspect={aspect!r}")


def _get_c3(session: Session, type_magie: str, ecole: str) -> float:
    t_norm, e_norm = _normaliser(type_magie), _normaliser(ecole)
    for row in session.exec(select(MagieC3)).all():
        if _normaliser(row.type_magie) == t_norm and _normaliser(row.ecole) == e_norm:
            return row.valeur
    raise ConstanteIntrouvableError(f"C3 introuvable pour Type={type_magie!r} / École={ecole!r}")


def _get_c4_c5(session: Session, type_magie: str) -> tuple[float, float]:
    t_norm = _normaliser(type_magie)
    for row in session.exec(select(MagieC4C5)).all():
        if _normaliser(row.type_magie) == t_norm:
            return row.c4_cout, row.c5_cast
    raise ConstanteIntrouvableError(f"C4/C5 introuvables pour Type={type_magie!r}")


def _get_c6_c7(session: Session, aspect: str) -> tuple[float, float]:
    a_norm = _normaliser(aspect)
    for row in session.exec(select(MagieC6C7)).all():
        if _normaliser(row.aspect) == a_norm:
            return row.c6_cout, row.c7_cast
    raise ConstanteIntrouvableError(f"C6/C7 introuvables pour Aspect={aspect!r}")


def resoudre_constantes(
    session: Session,
    type_magie: str,
    aspects: list[str],
    ecoles: list[str],
) -> ConstantesResolues:
    """Résout C1 à C7 pour un sort, en appliquant la règle du maximum sur
    toutes les combinaisons possibles quand le sort engage plusieurs
    Aspects et/ou plusieurs Écoles (voir avertissement en tête de fichier).
    """
    if not aspects:
        raise ValueError("Un sort doit engager au moins un Aspect")
    if not ecoles:
        raise ValueError("Un sort doit engager au moins une École")
    if len(aspects) > 3 or len(ecoles) > 3:
        raise ValueError("Un sort ne peut engager plus de 3 Aspects ou 3 Écoles (règle du livre)")

    # C1 : maximum sur toutes les paires (Aspect, École) du sort
    c1_candidats = [_get_c1(session, a, e) for a in aspects for e in ecoles]
    c1 = max(c1_candidats)

    # C2 : maximum sur les Aspects (le Type est fixe pour tout le sort)
    c2_candidats = [_get_c2(session, type_magie, a) for a in aspects]
    c2 = max(c2_candidats)

    # C3 : maximum sur les Écoles
    c3_candidats = [_get_c3(session, type_magie, e) for e in ecoles]
    c3 = max(c3_candidats)

    # C4/C5 : dépendent uniquement du Type, pas de combinaison à faire
    c4, c5 = _get_c4_c5(session, type_magie)

    # C6/C7 : maximum sur les Aspects
    c6_c7_candidats = [_get_c6_c7(session, a) for a in aspects]
    c6 = max(v[0] for v in c6_c7_candidats)
    c7 = max(v[1] for v in c6_c7_candidats)

    return ConstantesResolues(c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6, c7=c7)
