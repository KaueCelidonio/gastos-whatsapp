from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.clock import FixedClock
from app.config import BASE_DIR
from app.db.database import build_engine, build_session_factory, init_db
from app.interpretation.categorizer import Categorizer
from app.interpretation.rule_based import RuleBasedInterpreter
from app.repositories.sqlalchemy_repository import (
    SqlAlchemyExpenseRepository,
    SqlAlchemyProcessedMessageRepository,
)

TZ = ZoneInfo("America/Sao_Paulo")


@pytest.fixture
def session_factory():
    engine = build_engine("sqlite://")
    init_db(engine)
    yield build_session_factory(engine)
    engine.dispose()


@pytest.fixture
def session(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture
def expense_repo(session) -> SqlAlchemyExpenseRepository:
    return SqlAlchemyExpenseRepository(session)


@pytest.fixture
def processed_repo(session) -> SqlAlchemyProcessedMessageRepository:
    return SqlAlchemyProcessedMessageRepository(session)


@pytest.fixture
def clock() -> FixedClock:
    # Quinta-feira, 16/10/2025, 14h em São Paulo
    return FixedClock(datetime(2025, 10, 16, 14, 0, tzinfo=TZ))


@pytest.fixture
def categorizer() -> Categorizer:
    return Categorizer.from_json(BASE_DIR / "config" / "categorias.json")


@pytest.fixture
def interpreter(categorizer, clock) -> RuleBasedInterpreter:
    return RuleBasedInterpreter(categorizer, clock)
