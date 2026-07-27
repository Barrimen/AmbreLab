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
| R2 | Bucket `ambrelab-fichiers`, accès public désactivé | ✅ créé, vide |
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

## 4. Points de vigilance / dette technique mineure

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

- **Elenior** — premier développement entamé (pas encore de page en
  ligne à la date de rédaction).

## 7. Prochaine étape planifiée (Phase 2)

Première page de campagne connectée à l'API (fetch réel vers
`api.ambrelab.com`), à traiter dans une conversation dédiée du projet,
pas dans celle-ci.
