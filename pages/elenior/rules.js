/**
 * pages/elenior/rules.js
 * Données de règles propres à l'univers Elénior — partagées par tout outil
 * de cette campagne (fiche de personnage, futurs outils). Portées fidèlement
 * depuis la fiche d'origine (Fiches_de_personnage_3_5.html, v1.4.0) fournie
 * par l'autrice, pour ne pas ré-inventer ces tables ni les dupliquer.
 *
 * Le Cadran des Trente Temps (pages/elenior/cadran/index.html) contient sa
 * propre copie de la table des tranches de Temps d'Action (nécessaire à son
 * moteur de combat en direct) : elle n'a pas été retouchée dans cette
 * conversation (une conversation = une tâche). Une factorisation vers ce
 * fichier est une piste de nettoyage future, pas faite ici pour ne pas
 * toucher un outil déjà testé en production.
 *
 * Ne contient QUE des données et des fonctions pures (aucun accès DOM,
 * aucun fetch) — reste utilisable par n'importe quel outil sans dépendance.
 */

// ---------------------------------------------------------------------------
// Majeures (6)
// ---------------------------------------------------------------------------

const MAJEURES_NOMS = ["Force", "Agilite", "Perception", "Intellect", "Charisme", "Foi"];
// Libellés d'affichage (accents) — MAJEURES_NOMS reste la forme "code" utilisée
// comme clé partout (cohérent avec pages/elenior/cadran/index.html, CARACS).
const MAJEURES_LABELS = {
  Force: "Force", Agilite: "Agilité", Perception: "Perception",
  Intellect: "Intellect", Charisme: "Charisme", Foi: "Foi",
};

// ---------------------------------------------------------------------------
// Catalogue des mineures (41) — deux groupes d'affichage (colonnes), une
// seule notion de "mineures" (le découpage en deux n'est qu'une mise en
// page, pas deux tables distinctes).
// ---------------------------------------------------------------------------

const MINEURES_COL1 = [
  "Acrobatie", "Aplomb", "Artisanat", "Artiste", "Autorité", "Charme", "Combat",
  "Commérages", "Concentration", "Constitution", "Course", "Dévotion", "Dextérité",
  "Discrétion", "Duperie", "Écrit", "Équitation", "Escalade", "Esquive", "Géographie",
];
const MINEURES_COL2 = [
  "Histoire", "Improvisation", "Ingénierie", "Investigation", "Lancer", "Langue",
  "Marchandage", "Médecine", "Mémoire", "Mental", "Natation", "Nature", "Orientation",
  "Parade", "Pilotage", "Pistage", "Présence", "Rapidité", "Société", "Vigilance", "Volonté",
];
const MINEURES_CATALOGUE = [...MINEURES_COL1, ...MINEURES_COL2]; // 41

// ---------------------------------------------------------------------------
// Catalogue des écoles de magie (9) — noms officiels, cf. app/models.py
// CharacterMagicSchoolBase.
// ---------------------------------------------------------------------------

const ECOLES_CATALOGUE = [
  "Abjuration", "Altération", "Animation", "Destruction", "Divination",
  "Guérison", "Illusion", "Invocation", "Transmutation",
];

// ---------------------------------------------------------------------------
// Catalogue des maîtrises d'armes (13) — mêmes catégories que le Cadran
// (pages/elenior/cadran/index.html, CATEGORIES_TA / CARAC_RULES), pas
// l'ancien catalogue "2M/1M" de la fiche d'origine : ce sont ces catégories
// qui doivent circuler entre CharacterWeapon.category et
// CharacterWeaponMastery.category pour que la synchro "arme équipée"
// (app/utils.py::sync_combat_sheet_from_character) et le Cadran fonctionnent.
// ---------------------------------------------------------------------------

const CATEGORIES_ARMES = [
  "Armes d'hast lourde", "Armes d'hast légère", "Armes contondantes", "Haches",
  "Armes de taille", "Armes d'estoc", "Armes de contact", "Sans armes (Agilité)",
  "Sans armes (Force)", "Boucliers", "Arbalètes", "Armes à feu", "Armes de trait",
];

// ---------------------------------------------------------------------------
// Contribution PV/PP au palier "Fort" (≥30) — page 23 du livre de règles.
// Table fidèle à la fiche d'origine pour les mineures et les écoles.
// Pour les maîtrises d'armes, l'ancien catalogue ("Arme d'hast", "Bouclier"...)
// ne correspond plus aux 13 catégories du Cadran : remappage 1:1 direct pour
// la plupart, à confirmer avec Elise pour "Haches" et "Arbalètes" qui
// n'avaient pas d'équivalent exact dans l'ancienne fiche (contribution
// affectée par analogie avec la famille d'arme la plus proche).
// ---------------------------------------------------------------------------

const TABLE_PV_PP_MINEURE = {
  "Acrobatie": [1, 2], "Aplomb": [2, 1], "Artisanat": [1, 2], "Artiste": [0, 3], "Autorité": [2, 1],
  "Charme": [0, 3], "Combat": [2, 1], "Commérages": [0, 3], "Concentration": [0, 3], "Constitution": [3, 0],
  "Course": [1, 2], "Dévotion": [0, 3], "Dextérité": [1, 2], "Discrétion": [0, 3], "Duperie": [0, 3],
  "Écrit": [0, 3], "Équitation": [3, 0], "Escalade": [1, 2], "Esquive": [1, 2], "Géographie": [1, 2],
  "Histoire": [1, 2], "Improvisation": [1, 2], "Ingénierie": [1, 2], "Investigation": [1, 2], "Lancer": [3, 0],
  "Langue": [0, 3], "Marchandage": [1, 2], "Médecine": [0, 3], "Mémoire": [1, 2], "Mental": [0, 3],
  "Natation": [2, 1], "Nature": [2, 1], "Orientation": [1, 2], "Parade": [3, 0], "Pilotage": [1, 2],
  // "Pistage" : absent de la table dans la fiche d'origine (contribution 0/0
  // silencieuse) — fidèlement reproduit tel quel, pas corrigé de mon
  // initiative. À confirmer avec Elise si c'est un oubli.
  "Présence": [2, 1], "Rapidité": [1, 2], "Société": [1, 2], "Vigilance": [1, 2], "Volonté": [2, 1],
};

const TABLE_PV_PP_ECOLE = Object.fromEntries(ECOLES_CATALOGUE.map((n) => [n, [0, 3]]));

const TABLE_PV_PP_ARME = {
  "Armes d'hast lourde": [3, 0], "Armes d'hast légère": [3, 0], "Armes contondantes": [3, 0],
  "Haches": [3, 0], // à confirmer (pas d'équivalent exact dans l'ancienne fiche)
  "Armes de taille": [3, 0], "Armes d'estoc": [2, 1], "Armes de contact": [2, 1],
  "Sans armes (Agilité)": [2, 1], "Sans armes (Force)": [2, 1], "Boucliers": [2, 1],
  "Arbalètes": [2, 1], // à confirmer (rapproché de la famille "arme de trait")
  "Armes à feu": [2, 1], "Armes de trait": [2, 1],
};

function palierMineure(valeur) {
  const v = Number(valeur) || 0;
  if (v >= 30) return "Fort";
  if (v >= 20) return "Medium";
  return "Faible";
}

// ---------------------------------------------------------------------------
// Quotas de répartition (mineures + armes + écoles confondues) — un même
// palier de valeur (35/30/25/.../0) partage un quota global de créneaux,
// toutes catégories mélangées. Indépendant du niveau du personnage.
// ---------------------------------------------------------------------------

const QUOTAS_PALIERS = [
  { valeur: 35, nb: 2 }, { valeur: 30, nb: 6 }, { valeur: 25, nb: 10 }, { valeur: 20, nb: 12 },
  { valeur: 15, nb: 10 }, { valeur: 10, nb: 8 }, { valeur: 5, nb: 6 }, { valeur: 0, nb: 6 },
];

function compterUtilisationQuotas(listes) {
  // listes = tableau de tableaux d'items {valeur|value}
  const compte = {};
  QUOTAS_PALIERS.forEach((q) => { compte[q.valeur] = 0; });
  listes.forEach((liste) => {
    liste.forEach((item) => {
      const v = Number(item.value ?? item.valeur) || 0;
      if (compte[v] !== undefined) compte[v]++;
    });
  });
  return compte;
}

// ---------------------------------------------------------------------------
// Localisation des coups (jet de d20) — page 1 du PDF original.
// ---------------------------------------------------------------------------

const LOCALISATION_COUPS = [
  [1, "Torse"], [2, "Bras gauche"], [3, "Épaule droite"], [4, "Jambe gauche"], [5, "Bassin"],
  [6, "Pied gauche"], [7, "Bras droit"], [8, "Épaule gauche"], [9, "Jambe droite"], [10, "Torse"],
  [11, "Jambe droite"], [12, "Épaule droite"], [13, "Bras droit"], [14, "Torse"], [15, "Bassin"],
  [16, "Jambe gauche"], [17, "Épaule droite"], [18, "Bras gauche"], [19, "Pied droit"], [20, "Tête"],
];

// ---------------------------------------------------------------------------
// États du personnage selon % de PV actuel/max.
// ---------------------------------------------------------------------------

const ETATS_PERSONNAGE = [
  { seuil: 100, nom: "Normal" }, { seuil: 80, nom: "Étourdi" }, { seuil: 60, nom: "Blessé" },
  { seuil: 40, nom: "Diminué" }, { seuil: 20, nom: "Mutilé" }, { seuil: 10, nom: "Neutralisé" },
  { seuil: 0, nom: "Agonisant" },
];
function etatSelonRatio(ratioPourcent) {
  for (const e of ETATS_PERSONNAGE) { if (ratioPourcent >= e.seuil) return e.seuil; }
  return 0;
}

// ---------------------------------------------------------------------------
// Réduction de l'encombrement selon Force (armures lourdes/intermédiaires)
// ou Agilité (légères/médium) — page 68.
// ---------------------------------------------------------------------------

const REDUCTION_FORCE = [
  { min: 1, max: 30, type: "fixe", valeur: 0 }, { min: 31, max: 35, type: "fixe", valeur: -1 },
  { min: 36, max: 40, type: "pourcent", valeur: -0.05 }, { min: 41, max: 45, type: "pourcent", valeur: -0.10 },
  { min: 46, max: 50, type: "pourcent", valeur: -0.175 }, { min: 51, max: 55, type: "pourcent", valeur: -0.25 },
  { min: 56, max: 60, type: "pourcent", valeur: -0.325 }, { min: 61, max: 65, type: "pourcent", valeur: -0.40 },
  { min: 66, max: 70, type: "pourcent", valeur: -0.45 }, { min: 71, max: 75, type: "pourcent", valeur: -0.50 },
  { min: 76, max: 80, type: "pourcent", valeur: -0.55 }, { min: 81, max: 85, type: "pourcent", valeur: -0.60 },
  { min: 86, max: 90, type: "pourcent", valeur: -0.65 }, { min: 91, max: 95, type: "pourcent", valeur: -0.675 },
  { min: 96, max: 100, type: "pourcent", valeur: -0.70 },
];
const REDUCTION_AGILITE = [
  { min: 1, max: 30, type: "fixe", valeur: 0 }, { min: 31, max: 35, type: "fixe", valeur: -1 },
  { min: 36, max: 40, type: "pourcent", valeur: -0.05 }, { min: 41, max: 45, type: "pourcent", valeur: -0.075 },
  { min: 46, max: 50, type: "pourcent", valeur: -0.10 }, { min: 51, max: 55, type: "pourcent", valeur: -0.125 },
  { min: 56, max: 60, type: "pourcent", valeur: -0.15 }, { min: 61, max: 65, type: "pourcent", valeur: -0.20 },
  { min: 66, max: 70, type: "pourcent", valeur: -0.25 }, { min: 71, max: 75, type: "pourcent", valeur: -0.30 },
  { min: 76, max: 80, type: "pourcent", valeur: -0.35 }, { min: 81, max: 85, type: "pourcent", valeur: -0.40 },
  { min: 86, max: 90, type: "pourcent", valeur: -0.475 }, { min: 91, max: 95, type: "pourcent", valeur: -0.55 },
  { min: 96, max: 100, type: "pourcent", valeur: -0.65 },
];
function appliquerReductionEncombrement(totalBrut, statValeur, table) {
  const t = table.find((x) => statValeur >= x.min && statValeur <= x.max) || table[table.length - 1];
  return t.type === "fixe" ? Math.max(0, totalBrut + t.valeur) : totalBrut * (1 + t.valeur);
}

// ---------------------------------------------------------------------------
// Tranches de Temps d'Action (pages 85-88) — mêmes valeurs que le Cadran
// (LEVEL_TABLE), portées ici pour le calculateur "à froid" de la fiche.
// ---------------------------------------------------------------------------

const TRANCHES_TA = [
  { min: 1, max: 10, nom: "Première (1-10)", d: { "Armes d'hast lourde": [1, 1], "Armes d'hast légère": [2, 1], "Armes contondantes": [1, 1], "Haches": [1, 1], "Armes de taille": [2, 1], "Armes d'estoc": [2, 1], "Armes de contact": [4, 2], "Sans armes (Agilité)": [4, 2], "Sans armes (Force)": [2, 1], "Boucliers": [1, 1], "Arbalètes": [1, 1], "Armes à feu": [1, 1], "Armes de trait": [1, 1] } },
  { min: 11, max: 20, nom: "Deuxième (11-20)", d: { "Armes d'hast lourde": [2, 1], "Armes d'hast légère": [2, 2], "Armes contondantes": [1, 1], "Haches": [2, 1], "Armes de taille": [2, 2], "Armes d'estoc": [2, 2], "Armes de contact": [4, 3], "Sans armes (Agilité)": [4, 3], "Sans armes (Force)": [2, 2], "Boucliers": [1, 1], "Arbalètes": [1, 1], "Armes à feu": [1, 1], "Armes de trait": [2, 1] } },
  { min: 21, max: 30, nom: "Troisième (21-30)", d: { "Armes d'hast lourde": [2, 2], "Armes d'hast légère": [3, 2], "Armes contondantes": [2, 1], "Haches": [2, 2], "Armes de taille": [3, 2], "Armes d'estoc": [3, 2], "Armes de contact": [5, 3], "Sans armes (Agilité)": [5, 3], "Sans armes (Force)": [3, 2], "Boucliers": [2, 1], "Arbalètes": [2, 1], "Armes à feu": [2, 1], "Armes de trait": [2, 2] } },
  { min: 31, max: 40, nom: "Quatrième (31-40)", d: { "Armes d'hast lourde": [3, 2], "Armes d'hast légère": [3, 3], "Armes contondantes": [2, 2], "Haches": [3, 2], "Armes de taille": [3, 3], "Armes d'estoc": [3, 3], "Armes de contact": [5, 4], "Sans armes (Agilité)": [5, 4], "Sans armes (Force)": [3, 3], "Boucliers": [2, 2], "Arbalètes": [2, 2], "Armes à feu": [2, 2], "Armes de trait": [3, 2] } },
  { min: 41, max: 50, nom: "Cinquième (41-50)", d: { "Armes d'hast lourde": [3, 3], "Armes d'hast légère": [4, 3], "Armes contondantes": [3, 2], "Haches": [3, 3], "Armes de taille": [4, 3], "Armes d'estoc": [4, 3], "Armes de contact": [6, 4], "Sans armes (Agilité)": [6, 4], "Sans armes (Force)": [4, 3], "Boucliers": [3, 2], "Arbalètes": [3, 2], "Armes à feu": [3, 2], "Armes de trait": [3, 3] } },
  { min: 51, max: 60, nom: "Sixième (51-60)", d: { "Armes d'hast lourde": [4, 3], "Armes d'hast légère": [4, 4], "Armes contondantes": [3, 3], "Haches": [4, 3], "Armes de taille": [4, 4], "Armes d'estoc": [4, 4], "Armes de contact": [6, 5], "Sans armes (Agilité)": [6, 5], "Sans armes (Force)": [4, 4], "Boucliers": [3, 3], "Arbalètes": [3, 3], "Armes à feu": [3, 3], "Armes de trait": [4, 3] } },
  { min: 61, max: 70, nom: "Septième (61-70)", d: { "Armes d'hast lourde": [4, 4], "Armes d'hast légère": [5, 4], "Armes contondantes": [4, 3], "Haches": [4, 4], "Armes de taille": [5, 4], "Armes d'estoc": [5, 4], "Armes de contact": [7, 5], "Sans armes (Agilité)": [7, 5], "Sans armes (Force)": [5, 4], "Boucliers": [4, 3], "Arbalètes": [4, 3], "Armes à feu": [4, 3], "Armes de trait": [4, 4] } },
  { min: 71, max: 80, nom: "Huitième (71-80)", d: { "Armes d'hast lourde": [5, 4], "Armes d'hast légère": [5, 5], "Armes contondantes": [4, 4], "Haches": [5, 4], "Armes de taille": [5, 5], "Armes d'estoc": [5, 5], "Armes de contact": [8, 6], "Sans armes (Agilité)": [8, 6], "Sans armes (Force)": [6, 5], "Boucliers": [4, 4], "Arbalètes": [4, 4], "Armes à feu": [4, 4], "Armes de trait": [5, 4] } },
  { min: 81, max: 90, nom: "Neuvième (81-90)", d: { "Armes d'hast lourde": [5, 5], "Armes d'hast légère": [6, 5], "Armes contondantes": [5, 4], "Haches": [5, 5], "Armes de taille": [6, 5], "Armes d'estoc": [6, 5], "Armes de contact": [8, 7], "Sans armes (Agilité)": [8, 7], "Sans armes (Force)": [6, 6], "Boucliers": [5, 4], "Arbalètes": [5, 4], "Armes à feu": [5, 4], "Armes de trait": [5, 5] } },
  { min: 91, max: 100, nom: "Dixième (91-100)", d: { "Armes d'hast lourde": [6, 5], "Armes d'hast légère": [6, 6], "Armes contondantes": [5, 5], "Haches": [6, 5], "Armes de taille": [6, 6], "Armes d'estoc": [6, 6], "Armes de contact": [9, 8], "Sans armes (Agilité)": [9, 8], "Sans armes (Force)": [7, 6], "Boucliers": [5, 5], "Arbalètes": [5, 5], "Armes à feu": [5, 5], "Armes de trait": [6, 5] } },
];
function trouverTranche(score) {
  if (score < 1) return TRANCHES_TA[0];
  if (score > 100) return TRANCHES_TA[TRANCHES_TA.length - 1];
  return TRANCHES_TA.find((t) => score >= t.min && score <= t.max);
}

// ---------------------------------------------------------------------------
// Seuil de jet générique (mineures / maîtrises d'armes / écoles de magie) :
// Seuil = floor(Majeure/2) + valeur de la compétence.
// ---------------------------------------------------------------------------

function calculerSeuil(valeurMajeure, valeurCompetence) {
  return Math.floor((Number(valeurMajeure) || 0) / 2) + (Number(valeurCompetence) || 0);
}

window.AmbreRules = {
  MAJEURES_NOMS, MAJEURES_LABELS,
  MINEURES_COL1, MINEURES_COL2, MINEURES_CATALOGUE,
  ECOLES_CATALOGUE, CATEGORIES_ARMES,
  TABLE_PV_PP_MINEURE, TABLE_PV_PP_ECOLE, TABLE_PV_PP_ARME,
  palierMineure,
  QUOTAS_PALIERS, compterUtilisationQuotas,
  LOCALISATION_COUPS,
  ETATS_PERSONNAGE, etatSelonRatio,
  REDUCTION_FORCE, REDUCTION_AGILITE, appliquerReductionEncombrement,
  TRANCHES_TA, trouverTranche,
  calculerSeuil,
};
