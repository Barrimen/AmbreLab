# État des lieux — AmbreLab

Dernière mise à jour : 27 juillet 2026

Ce fichier documente l'état **réel** de l'infrastructure, les décisions
prises (et pourquoi), et les points de vigilance. À la différence des
instructions du projet (les règles permanentes), ce fichier évolue à
chaque changement d'infra — à mettre à jour après chaque étape notable.

---

## 1. Vue d'ensemble

```
                    joueurs et MJ
                          │
                    ambrelab.com
                          │
                    Cloudflare DNS
                          │
        ┌─────────────────┴──────────────────┐
        │                                    │
   pages statiques                    API + BDD
 Cloudflare Pages                       Railway
        │                                    │
        │                           ┌────────┴────────┐
        │                           │                 │
        │                       FastAPI          PostgreSQL
        │
        └────────────── Cloudflare R2
                  (bucket ambrelab-fichiers)
```

## 2. Éléments en place

| Élément | Détail | Statut |
|---|---|---|
| Domaine | `ambrelab.com`, acheté via Cloudflare Registrar | ✅ actif |
| Repo GitHub | `Barrimen/AmbreLab` | ✅ |
| Cloudflare Pages | Projet nommé `ambrelab` en interne (legacy : nom de domaine par défaut `jdr-plateforme.pages.dev` toujours actif en parallèle) | ✅ |
| Custom domain Pages | `ambrelab.com` → Cloudflare Pages | ✅ |
| Railway — service API | Nom interne `jdr-plateforme` (legacy, cosmétique uniquement) | ✅ Online |
| Railway — Postgres | Attaché au même projet, réseau interne privé | ✅ Online |
| Custom domain API | `api.ambrelab.com` → Railway, port 8080, proxy Cloudflare actif | ✅ certificat valide |
| Domaine Railway par défaut | `jdr-plateforme-production.up.railway.app` — toujours actif en parallèle | ✅ (peut être supprimé plus tard si inutile) |
| R2 | Bucket `ambrelab-fichiers`, accès public désactivé, CORS configuré (PUT depuis `https://ambrelab.com`) | ✅ opérationnel, testé de bout en bout (upload + lecture via URL présignée) |
| Alerte de dépense Railway | Fixée à 20€ | ✅ |

## 3. Décisions prises et pourquoi

- **Railway plutôt que Cloudflare Workers seul** pour la partie
  dynamique : besoin identifié de supporter potentiellement plusieurs
  langages (Python/Flask/Django, PHP, .NET), incompatible avec le
  runtime JS/edge de Workers.
- **FastAPI + SQLModel** choisi pour l'API commune : cohérent avec
  l'aisance en Python, documentation Swagger auto-générée, ORM léger.
- **Une seule instance Postgres, cloisonnement logique par
  `campaign_id`** plutôt qu'une instance par jeu : évite le coût d'un
  service Railway supplémentaire par jeu (contredirait la sobriété
  recherchée). Isolation physique réservée à un futur besoin de
  sécurité réel (accès externe à cloisonner strictement).
- **Pas de connexion directe à Postgres depuis un outil tiers** : tout
  passe par l'API HTTP commune, y compris pour les futurs outils.
- **TCP Proxy Postgres non activé** : la base n'est joignable que via
  le réseau privé Railway (API ↔ Postgres). À activer ponctuellement
  seulement si besoin d'explorer la base à la main (TablePlus, DBeaver,
  pgAdmin).
- **Budget révisé de 2-3€ à 5-15€/mois**, puis nuancé à 15-25€
  réalistes une fois la facturation Railway (RAM+CPU+stockage,
  usage réel) mieux comprise. Alerte de dépense posée en filet de
  sécurité.
- **Upload de fichiers vers R2 par URL présignée** (PUT direct navigateur→R2,
  GET présigné pour l'affichage) plutôt qu'un proxy binaire par l'API : le
  bucket reste privé, et l'API ne fait jamais transiter les octets d'un
  fichier (sobriété Railway). Implémenté pour le portrait de personnage,
  réutilisable tel quel pour tout futur fichier.
- **Migration de schéma faite à la main (`ALTER TABLE` direct en base)**
  pour ajouter les colonnes `Character`/`CharacterWeaponMastery`/
  `CharacterMagicSchool` manquantes, plutôt que de passer à Alembic tout
  de suite : ponctuel, la base ne contenait pas encore de données réelles
  à préserver. Voir point de vigilance ci-dessous — ce n'est plus
  vraiment "le cas simple" que `create_db_and_tables()` couvre seul.

## 4. Points de vigilance / dette technique mineure

- **Schéma en base désormais en avance sur `create_db_and_tables()`** :
  plusieurs `ALTER TABLE` manuels ont été nécessaires cette session
  (colonnes ajoutées à `Character` et consorts absentes en base malgré
  leur présence dans `models.py`). Si de nouvelles colonnes doivent
  être ajoutées, il faudra soit refaire un `ALTER TABLE` manuel à
  chaque fois, soit passer à Alembic maintenant que ce cas n'est plus
  isolé — à trancher dans une conversation dédiée si ça se reproduit.
- Noms internes "jdr-plateforme" (Cloudflare Pages, service Railway,
  domaine `.up.railway.app`) hérités du nom de projet initial, avant
  le renommage en `AmbreLab`. Cosmétique, aucun impact fonctionnel.
  Pas de renommage prévu pour l'instant.
- Pas encore d'accès de Claude aux données de facturation Railway
  (alertes, réglages de sleep/veille) — évoqué, à revoir plus tard.

## 5. Conventions actives (résumé — détail complet dans les instructions du projet)

- Une conversation = une tâche précise. Cette conversation-ci est
  dédiée au **débogage/incidents** de l'infra existante.
- Cloisonnement par jeu : préfixe R2 (`elenior/...`), sous-dossier
  `pages/elenior/`, `campaign_id` en base.
- Fonctions transverses dans `app/utils.py` (API) ou `pages/shared/`
  (statique), jamais dupliquées.
- Délégation possible à GPT pour tâches isolées et auto-suffisantes
  (voir instructions du projet pour le critère précis).

## 6. Historique des campagnes/jeux connus

- **Elenior** — `pages/elenior/cadran/index.html` (Cadran des Trente
  Temps) et `pages/elenior/personnage/index.html` (fiche de personnage)
  poussés sur GitHub. `pages/elenior/rules.js` centralise les tables de
  règles partagées (quotas, tranches de Temps d'Action, encombrement,
  localisation des coups) — portées depuis la fiche d'origine, pas
  encore factorisées dans le Cadran lui-même (qui garde sa propre copie
  pour l'instant, voir commentaire en tête de `rules.js`).

## 7. Prochaine étape planifiée

La fiche de personnage Elénior est en ligne et branchée à l'API (schéma,
routes CRUD, upload R2 du portrait) — testé de bout en bout cette
session. Prochaines pistes possibles, chacune dans sa propre
conversation : nettoyer la colonne orpheline `sheet_file_url` sur
`Character`, factoriser les tables de règles dupliquées entre le Cadran
et `rules.js`, ou avancer sur une nouvelle fonctionnalité côté
personnage.
