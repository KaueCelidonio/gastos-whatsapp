from datetime import date

import pytest

from app.services.replies import format_brl, format_day

TODAY = date(2025, 10, 16)


@pytest.mark.parametrize(
    ("cents", "expected"),
    [
        (0, "R$ 0,00"),
        (5, "R$ 0,05"),
        (3200, "R$ 32,00"),
        (1850, "R$ 18,50"),
        (123456, "R$ 1.234,56"),
        (123456789, "R$ 1.234.567,89"),
        (-1850, "-R$ 18,50"),
    ],
)
def test_format_brl(cents, expected):
    assert format_brl(cents) == expected


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2025, 10, 16), "hoje"),
        (date(2025, 10, 15), "ontem"),
        (date(2025, 10, 14), "anteontem"),
        (date(2025, 10, 2), "02/10"),
        (date(2024, 12, 20), "20/12/2024"),
    ],
)
def test_format_day(day, expected):
    assert format_day(day, TODAY) == expected
