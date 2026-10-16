"""Interpretador baseado em regras: comandos fixos + regex para registrar gastos. Sem IA."""

from __future__ import annotations

from app.clock import Clock
from app.interpretation.amounts import parse_amount_cents
from app.interpretation.base import MessageInterpreter
from app.interpretation.categorizer import Categorizer
from app.interpretation.dates import parse_date_token
from app.interpretation.intents import (
    CategoryTotal,
    DeleteLast,
    Help,
    Intent,
    LastExpenses,
    ListCategories,
    MonthTotal,
    RegisterExpense,
    UnknownCategory,
    Unrecognized,
    WeeklySummary,
)
from app.interpretation.text import normalize

MAX_AMOUNT_CENTS = 10_000_000_00  # R$ 10 milhões: acima disso é quase certamente erro de digitação

_COMMANDS: dict[str, type[Intent]] = {
    "total": MonthTotal,
    "total do mes": MonthTotal,
    "total mes": MonthTotal,
    "resumo": WeeklySummary,
    "resumo semanal": WeeklySummary,
    "semana": WeeklySummary,
    "ultimos": LastExpenses,
    "ultimos gastos": LastExpenses,
    "extrato": LastExpenses,
    "apagar ultimo": DeleteLast,
    "apagar o ultimo": DeleteLast,
    "excluir ultimo": DeleteLast,
    "desfazer": DeleteLast,
    "categorias": ListCategories,
    "ajuda": Help,
    "help": Help,
    "menu": Help,
    "comandos": Help,
    "oi": Help,
    "ola": Help,
    "bom dia": Help,
    "boa tarde": Help,
    "boa noite": Help,
}

_CATEGORY_TOTAL_PREFIX = "total "
_CONNECTORS = ("de ", "da ", "do ", "em ")


class RuleBasedInterpreter(MessageInterpreter):
    def __init__(self, categorizer: Categorizer, clock: Clock) -> None:
        self.categorizer = categorizer
        self.clock = clock

    def interpret(self, text: str) -> Intent:
        normalized = normalize(text).strip(" .!?")
        if not normalized:
            return Help()

        command = self._match_command(normalized)
        if command is not None:
            return command

        expense = self._match_expense(text)
        if expense is not None:
            return expense

        return Unrecognized(text)

    def _match_command(self, normalized: str) -> Intent | None:
        if normalized in _COMMANDS:
            return _COMMANDS[normalized]()

        if normalized.startswith(_CATEGORY_TOTAL_PREFIX):
            name = normalized.removeprefix(_CATEGORY_TOTAL_PREFIX)
            for connector in _CONNECTORS:
                name = name.removeprefix(connector)
            category = self.categorizer.find_category(name)
            return CategoryTotal(category) if category else UnknownCategory(name)

        return None

    def _match_expense(self, text: str) -> RegisterExpense | None:
        """Aceita "descrição valor" ou "valor descrição", com data opcional em qualquer posição."""
        tokens = [t for t in text.split() if normalize(t) != "r$"]

        today = self.clock.today()
        spent_on = today
        dates = [(i, parse_date_token(normalize(t), today)) for i, t in enumerate(tokens)]
        dates = [(i, d) for i, d in dates if d is not None]
        if len(dates) > 1:
            return None
        if dates:
            index, spent_on = dates[0]
            tokens.pop(index)

        if len(tokens) < 2:
            return None

        candidates = []
        for amount_index, rest in ((len(tokens) - 1, tokens[:-1]), (0, tokens[1:])):
            amount = parse_amount_cents(tokens[amount_index])
            description = " ".join(rest)
            if amount is not None and self._is_valid_description(description):
                candidates.append((amount, description))

        if len(candidates) == 2:
            # Ex.: "99 25" -> ambos são números; vale a leitura cuja descrição é palavra-chave.
            with_keyword = [c for c in candidates if self.categorizer.has_keyword(c[1])]
            candidates = with_keyword if len(with_keyword) == 1 else []

        if len(candidates) != 1:
            return None

        amount, description = candidates[0]
        if not 0 < amount <= MAX_AMOUNT_CENTS:
            return None

        return RegisterExpense(
            description=description,
            amount_cents=amount,
            spent_on=spent_on,
            category=self.categorizer.categorize(description),
        )

    def _is_valid_description(self, description: str) -> bool:
        has_letter = any(ch.isalpha() for ch in description)
        return has_letter or self.categorizer.has_keyword(description)
