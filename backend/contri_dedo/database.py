import os
from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/contridedo",
)


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


@lru_cache(maxsize=1)
def get_engine():
    return create_engine(normalize_database_url(DATABASE_URL), pool_pre_ping=True, pool_recycle=300)


def get_db() -> Generator[Session, None, None]:
    from sqlalchemy.orm import sessionmaker

    db = sessionmaker(bind=get_engine(), expire_on_commit=False)()
    try:
        yield db
    finally:
        db.close()