# API JDR — commune à tes outils

API FastAPI + PostgreSQL, pensée pour être partagée par plusieurs
apps/artefacts (fiches, campagnes, etc.). Deux tables d'exemple
(`Campaign`, `Character`) pour te montrer le pattern — étends-les ou
ajoute-en de nouvelles dans `app/models.py`.

## Déploiement sur Railway

1. Pousse ce dossier `api/` sur GitHub (dans ton repo `jdr-plateforme`).
2. Sur Railway : **New Project → Deploy from GitHub repo**, sélectionne
   ce repo, et indique `api` comme *root directory* si tu es en
   monorepo (Settings → Root Directory).
3. Railway détecte le `Dockerfile` automatiquement et build dessus.
4. Ajoute un service PostgreSQL au même projet : **New → Database →
   PostgreSQL**. Railway relie automatiquement `DATABASE_URL` au
   service API — tu n'as rien à configurer manuellement.
5. Une fois déployé, va dans **Settings → Networking → Generate
   Domain** pour obtenir une URL publique, ou attache ton propre
   sous-domaine (`api.tondomaine.fr`) en CNAME depuis Cloudflare DNS
   vers l'URL Railway fournie.
6. Vérifie que ça tourne : `https://<ton-url>/health` doit répondre
   `{"status": "ok"}`. La doc interactive Swagger est disponible sur
   `https://<ton-url>/docs`.

## Développement local

```bash
cd api
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Sans `DATABASE_URL` défini, l'API utilise un fichier SQLite local
(`local.db`) — pratique pour tester sans dépendre de Railway.

## Ajouter une nouvelle table

1. Ajoute le modèle dans `app/models.py` (suit le pattern
   `XxxBase` / `Xxx(table=True)` / `XxxCreate`).
2. Ajoute les routes correspondantes dans `app/main.py`.
3. `create_db_and_tables()` crée la table automatiquement au prochain
   déploiement — pas de migration à écrire tant que le schéma reste
   simple. Si tu commences à faire des `ALTER TABLE` fréquents sur des
   données existantes importantes, passe à Alembic pour des
   migrations versionnées.

## Prochaine étape naturelle

Une fois cette API en place, tes apps statiques sur Cloudflare Pages
peuvent l'appeler directement (fetch vers `https://api.tondomaine.fr`)
plutôt que de dupliquer une base par outil.
