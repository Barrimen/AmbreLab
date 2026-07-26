import os

from sqlmodel import SQLModel, Session, create_engine

# Railway injecte automatiquement DATABASE_URL quand tu attaches un service
# PostgreSQL au même projet. En local, utilise .env.example comme modèle.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./local.db")

# Railway fournit parfois une URL commençant par "postgres://" (ancien format)
# alors que SQLAlchemy/SQLModel attend "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
