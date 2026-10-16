"""Criação do engine e das sessões a partir de DATABASE_URL (SQLite ou PostgreSQL)."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base


def build_engine(database_url: str) -> Engine:
    if not database_url.startswith("sqlite"):
        return create_engine(database_url, pool_pre_ping=True)

    kwargs: dict = {"connect_args": {"check_same_thread": False}}
    if database_url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool  # mantém o banco em memória vivo entre sessões
    return create_engine(database_url, **kwargs)


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)
