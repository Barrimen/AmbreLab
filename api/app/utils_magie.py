"""
Calcul du Coût (PP) et du Cast (temps de lancement) d'un sort d'Elénior.

DÉCISION DU 09/08/2026 : implémentation basée sur les équations du LIVRE de règles
("Les Compagnons de l'Infortune 2026", chapitre IV, page 126), PAS sur celles du
tableur d'Elise. Décision prise par Obe suite au retour d'Elise elle-même (Discord,
09/08/2026) : les décalages +0,45/+1/+0,9 du tableur sur C1/C2/C3 sont bien réels et
volontaires, mais Elise n'avait pas mesuré leur impact réel sur le résultat final
(facteur ~7x observé lors des tests de comparaison) et envisage de revenir à une
version plus proche du livre. Le code suit donc le livre tel quel, sans décalage ni
plancher artificiel.

Si Elise confirme plus tard vouloir les décalages du tableur, ils se rajoutent
simplement en +0.45/+1/+0.9 sur c1/c2/c3 avant l'appel à ces fonctions - voir
recap-extraction-magie-elenior.md et incoherences-livre-vs-tableur-EXHAUSTIF.md pour
le détail de ce qui a été comparé.

Sources des valeurs C1 à C7 : tables extraites et validées visuellement depuis le
livre (voir constantes-magie-json.zip). Aucune valeur ici n'est codée en dur : ces
fonctions prennent les constantes déjà résolues en paramètre, à charge de l'appelant
(route API) d'aller les chercher dans les tables Postgres de référence
(magie_c1_aspect_ecole, magie_c2_type_aspect, etc. - voir models_magie.py).
"""

from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Combinaison des constantes pour les sorts à Aspects ou Écoles multiples
# (règles du livre, page 145 - "Sorts aux multiples écoles" / "Sorts aux
# multiples aspects")
# ---------------------------------------------------------------------------

def resoudre_c1_multi_aspect(c1_par_aspect: list[float]) -> float:
    """C1 pour un sort à plusieurs Aspects : le livre dit de prendre la valeur
    la plus haute parmi les Aspects engagés (pas une moyenne).
    c1_par_aspect : la valeur C1 (Aspect x École du sort) pour chaque Aspect
    engagé par le sort (1 à 3 valeurs)."""
    if not c1_par_aspect:
        raise ValueError("Un sort doit engager au moins un Aspect")
    return max(c1_par_aspect)


def resoudre_c1_multi_ecole(c1_par_ecole: list[float]) -> float:
    """C1 pour un sort à plusieurs Écoles : même règle que pour les Aspects,
    la valeur la plus haute parmi les Écoles engagées (livre p.145)."""
    if not c1_par_ecole:
        raise ValueError("Un sort doit engager au moins une École")
    return max(c1_par_ecole)


def resoudre_c2_multi_aspect(c2_par_aspect: list[float]) -> float:
    """C2 pour un sort à plusieurs Aspects : même règle, valeur la plus haute
    (livre p.145 : "nous prenons la valeur la plus haute des constantes
    C1 et C2")."""
    if not c2_par_aspect:
        raise ValueError("Un sort doit engager au moins un Aspect")
    return max(c2_par_aspect)


def moyenne_niveau_aspect(niveaux_aspect: list[float]) -> float:
    """Moyenne des Niveaux d'Aspect engagés par le sort, avant de la
    moyenner à son tour avec le Niveau de Type pour obtenir Nv
    (livre p.145 : "nous faisons en effet la moyenne du niveau d'aspect
    entre ces différents aspects")."""
    if not niveaux_aspect:
        raise ValueError("Un sort doit engager au moins un Aspect")
    return sum(niveaux_aspect) / len(niveaux_aspect)


def calculer_nv(niveau_aspect_moyen: float, niveau_type: float) -> float:
    """Nv = moyenne du Niveau d'Aspect (déjà moyenné si plusieurs Aspects,
    voir moyenne_niveau_aspect) et du Niveau de Type engagés dans le sort."""
    return (niveau_aspect_moyen + niveau_type) / 2


# ---------------------------------------------------------------------------
# Équations principales - Coût et Cast d'un sort
# ---------------------------------------------------------------------------

@dataclass
class ComposantsSort:
    """Regroupe toutes les variables brutes nécessaires au calcul d'un sort,
    telles que définies par le livre p.126. Un sort n'utilise jamais toutes
    les variables à la fois (ex: un sort sans entrave a en=0) - les valeurs
    par défaut à 0 couvrent ce cas sans complexifier l'appel."""
    pi: float = 0.0    # Puissance immédiate (somme des effets instantanés)
    pd: float = 0.0    # Puissance dans la durée (somme des effets prolongés)
    en: float = 0.0    # Entrave - voir note ci-dessous
    ex: float = 0.0    # Multiplicateur d'effets exceptionnels (contrôle d'action)
    nb: float = 1.0    # Nombre de cibles touchées
    tz: float = 0.0    # Taille de la zone (0 si le sort ne cible pas une zone)
    z: float = 1.0     # Forme de la zone (multiplicateur, 1 par défaut = Zone 1)
    po: float = 0.0    # Portée (uniquement utilisée dans le Cast, pas le Coût)
    cm: float = 0.0    # Caractéristique magique utilisée, déjà divisée par 10
    nv: float = 0.0    # Niveau moyen (voir calculer_nv)


def calculer_cout_sort(
    c: ComposantsSort,
    c1: float, c2: float, c3: float, c4: float, c6: float,
) -> float:
    """Coût du sort en PP, formule du livre p.126 :

        (((Pi×1,2 + Pd + En) × (Ex+1)) × C1) × ((Nb + (Tz×Z)×1,5) × (C2×0,5))
        × C3 × (C4+C6) / (Nv×1,5 + Cm×3)

    NOTE sur En : le livre ajoute En une fois ici, alors qu'En intervient
    déjà dans le calcul de Pd lui-même (Pd = (Ed+En)×(D+Napp+F)÷2, voir le
    tableau des abréviations p.126). C'est bien ce que dit le livre tel
    quel : on l'implémente sans le "corriger", conformément à la décision
    du 09/08/2026 de suivre le livre à la lettre plutôt que d'interpréter.
    Si un sort n'a pas d'entrave, en=0 et ce terme ne change rien au calcul.

    Le livre indique un minimum de 1 PP pour le coût final - ce plancher
    n'est PAS appliqué ici (garder la fonction pure), il doit être appliqué
    par l'appelant : max(1, calculer_cout_sort(...)).
    """
    if c4 + c6 == 0 and (c.nv * 1.5 + c.cm * 3) == 0:
        raise ValueError("Diviseur nul : Nv et Cm ne peuvent pas être tous deux à 0")

    facteur_puissance = (c.pi * 1.2 + c.pd + c.en) * (c.ex + 1) * c1
    facteur_cibles = (c.nb + (c.tz * c.z) * 1.5) * (c2 * 0.5)
    numerateur = facteur_puissance * facteur_cibles * c3 * (c4 + c6)
    denominateur = c.nv * 1.5 + c.cm * 3

    return numerateur / denominateur


def calculer_cast_sort(
    c: ComposantsSort,
    c1: float, c2: float, c3: float, c5: float, c7: float,
) -> float:
    """Cast du sort (temps de lancement), formule du livre p.126 :

        (((Pi÷2 + Pd×2 + En) × (Ex+1)) × C1) × ((Nb×1,5 + (Tz×Z)) × C2)
        × Po × C3 × (C5+C7) / (Nv×4 + Cm)

    Le livre indique que le minimum de temps de Cast est de 0 (le sort part
    au moment même où le lanceur commence à le lancer) - contrairement au
    Coût, aucun plancher à appliquer ici.

    Pour l'Alchimie (et tout Type utilisant un Long-sort), cette fonction
    NE S'APPLIQUE PAS : le Long-sort est une valeur de palier choisie
    directement dans sa propre table (magie_generic_long_sort), pas un
    résultat de cette équation. Voir SortBase.est_long_sort dans
    models_magie.py.
    """
    if (c.nv * 4 + c.cm) == 0:
        raise ValueError("Diviseur nul : Nv et Cm ne peuvent pas être tous deux à 0")

    facteur_puissance = (c.pi / 2 + c.pd * 2 + c.en) * (c.ex + 1) * c1
    facteur_cibles = (c.nb * 1.5 + (c.tz * c.z)) * c2
    numerateur = facteur_puissance * facteur_cibles * c.po * c3 * (c5 + c7)
    denominateur = c.nv * 4 + c.cm

    return numerateur / denominateur


# ---------------------------------------------------------------------------
# Auto-test - vérifie la non-régression sur un sort connu
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # "Peau d'emprunt" (Alchimie / Chair / Transmutation), sort de contrôle
    # utilisé pendant les tests de comparaison livre/tableur du 09/08/2026.
    # Constantes issues des tables extraites du LIVRE (pas du tableur).
    composants = ComposantsSort(
        pi=15, pd=0, en=0, ex=0,
        nb=1, tz=0, z=1, po=0.3,
        cm=3, nv=5.25,
    )
    # Chair x Transmutation (C1), Alchimie x Chair (C2), Alchimie x Transmutation (C3)
    # Alchimie (C4, C5), Chair (C6, C7)
    c1, c2, c3, c4, c5, c6, c7 = 1.5, 1, 0.5, 1, 2, 0.95, 1.25

    cout = calculer_cout_sort(composants, c1, c2, c3, c4, c6)
    cast = calculer_cast_sort(composants, c1, c2, c3, c5, c7)

    print(f"Coût (livre) : {cout:.4f}  (attendu ~0.78)")
    print(f"Cast (livre) : {cast:.4f}  (attendu ~0.3428)")

    assert abs(cout - 0.78) < 0.001, "Régression détectée sur le calcul du Coût"
    assert abs(cast - 0.3428) < 0.001, "Régression détectée sur le calcul du Cast"
    print("OK - auto-test passé")
