"""Intenções: o que o usuário quer fazer, independente de como escreveu a mensagem."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RegisterExpense:
    description: str
    amount_cents: int
    spent_on: date
    category: str


@dataclass(frozen=True)
class MonthTotal:
    pass


@dataclass(frozen=True)
class CategoryTotal:
    category: str


@dataclass(frozen=True)
class UnknownCategory:
    name: str


@dataclass(frozen=True)
class WeeklySummary:
    pass


@dataclass(frozen=True)
class LastExpenses:
    pass


@dataclass(frozen=True)
class DeleteLast:
    pass


@dataclass(frozen=True)
class ListCategories:
    pass


@dataclass(frozen=True)
class Help:
    pass


@dataclass(frozen=True)
class Unrecognized:
    text: str


Intent = (
    RegisterExpense
    | MonthTotal
    | CategoryTotal
    | UnknownCategory
    | WeeklySummary
    | LastExpenses
    | DeleteLast
    | ListCategories
    | Help
    | Unrecognized
)
