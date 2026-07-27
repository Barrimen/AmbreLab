/**
 * pages/shared/lock.js
 * Mode "verrouillage" générique pour les fiches de la plateforme AmbreLab.
 *
 * Principe (décision 5.5 du cahier des charges fiche de personnage
 * Elénior) : verrouiller protège les VALEURS d'une fiche contre une
 * modification involontaire, mais ne doit jamais empêcher de JOUER —
 * les boutons de jet de dé restent toujours actifs, même verrouillé.
 *
 * Convention par attribut, à poser une fois dans le HTML :
 * - data-lockable        : ce champ est concerné par le verrouillage
 * - data-editable-locked : ce champ reste modifiable même verrouillé
 *                          (ex: PV/PP actuels, états en cours)
 * - data-dice-button     : ce bouton n'est JAMAIS désactivé par ce
 *                          module, quel que soit l'état de verrouillage
 */

const LOCK_ATTR = "data-locked";

/**
 * @param {HTMLElement} root
 * @returns {boolean}
 */
function isLocked(root) {
  return root.getAttribute(LOCK_ATTR) === "true";
}

/**
 * Applique un état de verrouillage donné à un conteneur (idempotent,
 * utile pour restaurer un état au chargement de la page).
 * @param {HTMLElement} root
 * @param {boolean} locked
 */
function applyLockState(root, locked) {
  root.setAttribute(LOCK_ATTR, locked ? "true" : "false");

  root.querySelectorAll("[data-lockable]").forEach((el) => {
    if (el.hasAttribute("data-dice-button")) return; // jamais désactivé
    const resteEditable = el.hasAttribute("data-editable-locked");
    el.disabled = locked && !resteEditable;
  });
}

/**
 * Bascule l'état de verrouillage d'un conteneur (une page, un onglet...).
 * @param {HTMLElement} root
 * @returns {boolean} le nouvel état (true = verrouillé)
 */
function toggleLock(root) {
  const nouvelEtat = !isLocked(root);
  applyLockState(root, nouvelEtat);
  return nouvelEtat;
}

window.AmbreLock = { isLocked, applyLockState, toggleLock };
