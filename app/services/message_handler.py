"""Orquestra uma mensagem: interpreta o texto, aciona o serviço e monta a resposta.

Não conhece WhatsApp nem banco de dados: recebe texto e devolve texto.
"""

from __future__ import annotations

from app.clock import Clock
from app.interpretation.base import MessageInterpreter
from app.interpretation.categorizer import Categorizer
from app.interpretation.intents import (
    CategoryTotal,
    DeleteLast,
    Help,
    LastExpenses,
    ListCategories,
    MonthTotal,
    RegisterExpense,
    UnknownCategory,
    Unrecognized,
    WeeklySummary,
)
from app.services import replies
from app.services.expense_service import ExpenseService


class MessageHandler:
    def __init__(
        self,
        interpreter: MessageInterpreter,
        service: ExpenseService,
        categorizer: Categorizer,
        clock: Clock,
    ) -> None:
        self.interpreter = interpreter
        self.service = service
        self.categorizer = categorizer
        self.clock = clock

    def handle(self, user_id: str, text: str) -> str:
        intent = self.interpreter.interpret(text)
        today = self.clock.today()

        match intent:
            case RegisterExpense(description, amount_cents, spent_on, category):
                expense = self.service.register(
                    user_id,
                    description=description,
                    amount_cents=amount_cents,
                    category=category,
                    spent_on=spent_on,
                )
                return replies.expense_registered(expense, today)
            case MonthTotal():
                return replies.month_total(self.service.month_total(user_id))
            case CategoryTotal(category):
                return replies.month_total(self.service.month_total(user_id, category))
            case UnknownCategory(name):
                return replies.unknown_category(name, self.categorizer)
            case WeeklySummary():
                return replies.weekly_summary(self.service.weekly_summary(user_id))
            case LastExpenses():
                return replies.latest(self.service.latest(user_id), today)
            case DeleteLast():
                return replies.deleted(self.service.delete_last(user_id), today)
            case ListCategories():
                return replies.categories(self.categorizer)
            case Help():
                return replies.HELP
            case Unrecognized():
                return replies.UNRECOGNIZED
