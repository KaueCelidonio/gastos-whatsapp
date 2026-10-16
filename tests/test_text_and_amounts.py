import pytest

from app.interpretation.amounts import parse_amount_cents
from app.interpretation.text import normalize


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Almoço", "almoco"),
        ("FARMÁCIA", "farmacia"),
        ("  ônibus   da  manhã ", "onibus da manha"),
        ("Atacadão", "atacadao"),
        ("Água", "agua"),
    ],
)
def test_normalize(raw, expected):
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    ("token", "cents"),
    [
        ("32", 3200),
        ("18,50", 1850),
        ("18.50", 1850),
        ("32,5", 3250),
        ("120,90", 12090),
        ("1.234,56", 123456),
        ("1.234", 123400),
        ("R$32", 3200),
        ("r$18,50", 1850),
        ("0,99", 99),
    ],
)
def test_parse_amount(token, cents):
    assert parse_amount_cents(token) == cents


@pytest.mark.parametrize("token", ["almoço", "12/10", "18,505", "1,2,3", "", "R$", "-5", "1.23.4"])
def test_parse_amount_rejects_non_amounts(token):
    assert parse_amount_cents(token) is None
