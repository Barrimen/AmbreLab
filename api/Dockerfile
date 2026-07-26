FROM python:3.12-slim

WORKDIR /app

# Installe les dépendances d'abord pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway fournit la variable PORT au runtime ; on l'utilise plutôt
# qu'un port codé en dur.
ENV PORT=8000
EXPOSE 8000

CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
