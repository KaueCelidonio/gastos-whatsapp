"""Reconhecimento de datas relativas ("hoje", "ontem", "anteontem") e no formato dd/mm."""

from __future__ import annotations

import re
from datetime import date, timedelta

_RELATIVE_DAYS = {"hoje": 0, "ontem": 1, "anteontem": 2}
_DATE_PATTERN = re.compile(r"^(\d{1,2})/(\d{1,2})(?:/(\d{2}|\d{4}))?$")


def parse_date_token(token: str, today: date) -> date | None:
    """Converte um token (já normalizado) em data, ou devolve None se não for uma data.

    "dd/mm" sem ano usa o ano atual; se cair no futuro, assume o ano anterior,
    já que um gasto não acontece no futuro.
    """
    if token in _RELATIVE_DAYS:
        return today - timedelta(days=_RELATIVE_DAYS[token])

    match = _DATE_PATTERN.match(token)
    if not match:
        return None

    day, month, year = int(match[1]), int(match[2]), match[3]
    try:
        if year is not None:
            full_year = int(year) + 2000 if len(year) == 2 else int(year)
            return date(full_year, month, day)
        parsed = date(today.year, month, day)
        if parsed > today:
            parsed = date(today.year - 1, month, day)
        return parsed
    except ValueError:
        return None
