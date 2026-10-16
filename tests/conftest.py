from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.clock import FixedClock
from app.config import BASE_DIR
from app.interpretation.categorizer import Categorizer
from app.interpretation.rule_based import RuleBasedInterpreter

TZ = ZoneInfo("America/Sao_Paulo")


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
