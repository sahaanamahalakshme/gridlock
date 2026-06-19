"""

Single source of truth for the DB connection. Local dev uses a SQLite file

with zero setup. Deployment points DATABASE_URL at Supabase (or any managed

Postgres) - same models.py, same code in memory_store.py, nothing else changes.

"""

import os

from pathlib import Path

from dotenv import load_dotenv

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from models import Base


load_dotenv(dotenv_path=Path(__file__).parent / ".env")


DEFAULT_LOCAL_URL = "sqlite:///./memory.db"


DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_LOCAL_URL)


connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}


engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    """Create the events table (and indexes) if it doesn't exist yet."""

    Base.metadata.create_all(engine)


def get_session():
    """FastAPI dependency: yields a session, closes it after the request."""

    session = SessionLocal()

    try:

        yield session

    finally:

        session.close()
