"""Contratos de acesso a dados. A regra de negócio depende destas interfaces, não do banco."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime

from app.domain import Expense


class ExpenseRepository(ABC):
    @abstractmethod
    def add(
        self,
        *,
        user_id: str,
        description: str,
        amount_cents: int,
        category: str,
        spent_on: date,
        created_at: datetime,
    ) -> Expense: ...

    @abstractmethod
    def total(self, user_id: str, start: date, end: date, category: str | None = None) -> int:
        """Soma em centavos dos gastos com data entre start e end (inclusive)."""

    @abstractmethod
    def totals_by_category(self, user_id: str, start: date, end: date) -> dict[str, int]:
        """Soma por categoria, da maior para a menor."""

    @abstractmethod
    def latest(self, user_id: str, limit: int) -> list[Expense]:
        """Gastos registrados mais recentemente (ordem de registro, não de data do gasto)."""

    @abstractmethod
    def delete(self, user_id: str, expense_id: int) -> bool: ...


class ProcessedMessageRepository(ABC):
    @abstractmethod
    def mark_processed(self, message_id: str, received_at: datetime) -> bool:
        """Registra a mensagem. Devolve False se ela já tinha sido processada."""
