"""Entidades do domínio, independentes de banco de dados e de canal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class Expense:
    id: int
    user_id: str
    description: str
    amount_cents: int
    category: str
    spent_on: date
    created_at: datetime
