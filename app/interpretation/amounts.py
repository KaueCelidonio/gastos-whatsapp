"""Leitura de valores em reais escritos de formas variadas: 32, 18,50, 18.50, 1.234,56, R$32."""

from __future__ import annotations

import re
from decimal import Decimal

_WITH_THOUSANDS = re.compile(r"^\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?$")
_PLAIN = re.compile(r"^\d+(?:[.,]\d{1,2})?$")


def parse_amount_cents(token: str) -> int | None:
    """Converte um token em centavos, ou devolve None se não for um valor monetário."""
    token = token.lower().removeprefix("r$")
    if _WITH_THOUSANDS.match(token):
        number = token.replace(".", "").replace(",", ".")
    elif _PLAIN.match(token):
        number = token.replace(",", ".")
    else:
        return None
    return int(Decimal(number) * 100)
