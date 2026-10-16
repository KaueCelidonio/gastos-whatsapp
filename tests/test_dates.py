from datetime import date

import pytest

from app.interpretation.dates import parse_date_token

TODAY = date(2025, 10, 16)


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("hoje", date(2025, 10, 16)),
        ("ontem", date(2025, 10, 15)),
        ("anteontem", date(2025, 10, 14)),
        ("12/10", date(2025, 10, 12)),
        ("1/10", date(2025, 10, 1)),
        ("16/10", date(2025, 10, 16)),
        ("20/12", date(2024, 12, 20)),  # no futuro -> ano anterior
        ("05/03/2024", date(2024, 3, 5)),
        ("05/03/24", date(2024, 3, 5)),
    ],
)
def test_parse_date_token(token, expected):
    assert parse_date_token(token, TODAY) == expected


@pytest.mark.parametrize("token", ["amanha", "31/02", "13/13", "uber", "12-10", "32"])
def test_parse_date_token_rejects_invalid(token):
    assert parse_date_token(token, TODAY) is None


def test_relative_days_cross_month_boundary():
    assert parse_date_token("anteontem", date(2025, 3, 1)) == date(2025, 2, 27)
