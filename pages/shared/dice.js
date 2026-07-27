/**
 * pages/shared/dice.js
 * Moteur de dé générique, réutilisable par tout outil de la plateforme
 * AmbreLab : jets de d100 sous seuil pour la fiche de personnage Elénior,
 * pools de dés variables pour le Cadran des Trente Temps, etc.
 * Ne contient aucune règle spécifique à un système de jeu — juste les
 * primitives (lancer, comparer à un seuil, afficher, effacer).
 */

/**
 * Lance nbDes dés à nbFaces faces.
 * @param {number} nbDes
 * @param {number} nbFaces
 * @returns {{ des: number[], total: number }}
 */
function rollDice(nbDes, nbFaces) {
  const des = Array.from(
    { length: nbDes },
    () => 1 + Math.floor(Math.random() * nbFaces)
  );
  return { des, total: des.reduce((a, b) => a + b, 0) };
}

/**
 * Jet "sous seuil" — mécanique par défaut de la fiche Elénior
 * (Seuil = ⌊Majeure/2⌋ + valeur, jet de d100 sous ce seuil pour réussir).
 * faces=100 par défaut mais paramétrable si un autre système utilise une
 * autre base de dé.
 *
 * Critiques (règle simple retenue pour l'instant, à revoir si Elise donne
 * une règle plus précise) : un jet < 5 est une réussite critique, un jet
 * > 95 est un échec critique, dans les deux cas indépendamment du seuil.
 * @param {number} seuil
 * @param {number} [faces=100]
 * @returns {{ valeur: number, seuil: number, reussite: boolean, critique: "reussite"|"echec"|null }}
 */
function rollUnderThreshold(seuil, faces = 100) {
  const { total: valeur } = rollDice(1, faces);

  let critique = null;
  if (valeur < 5) critique = "reussite";
  else if (valeur > 95) critique = "echec";

  const reussite =
    critique === "reussite" ? true : critique === "echec" ? false : valeur <= seuil;

  return { valeur, seuil, reussite, critique };
}

/**
 * Affiche un résultat de jet dans un élément du DOM.
 * L'élément est marqué data-roll-result="true" pour que clearAllRolls()
 * puisse le retrouver sans connaître chaque champ à l'avance.
 * @param {HTMLElement} element
 * @param {{des?: number[], total?: number, valeur?: number, seuil?: number, reussite?: boolean}} resultat
 */
function renderRollResult(element, resultat) {
  element.dataset.rollResult = "true";

  if ("reussite" in resultat) {
    const label = resultat.critique === "reussite"
      ? "Réussite critique"
      : resultat.critique === "echec"
      ? "Échec critique"
      : resultat.reussite
      ? "Réussite"
      : "Échec";
    element.textContent = `${resultat.valeur} / ${resultat.seuil} — ${label}`;
    element.classList.toggle("jet-reussite", resultat.reussite);
    element.classList.toggle("jet-echec", !resultat.reussite);
    element.classList.toggle("jet-critique", Boolean(resultat.critique));
  } else {
    element.textContent = `${resultat.des.join(" + ")} = ${resultat.total}`;
  }
}

/**
 * "Effacer les jets" : vide tous les résultats affichés dans un conteneur
 * donné (un onglet, une page entière...), sans avoir besoin de connaître
 * chaque champ à l'avance — il suffit qu'ils portent data-roll-result.
 * @param {HTMLElement} container
 */
function clearAllRolls(container) {
  container.querySelectorAll("[data-roll-result]").forEach((el) => {
    el.textContent = "";
    el.classList.remove("jet-reussite", "jet-echec");
    delete el.dataset.rollResult;
  });
}

window.AmbreDice = {
  rollDice,
  rollUnderThreshold,
  renderRollResult,
  clearAllRolls,
};
