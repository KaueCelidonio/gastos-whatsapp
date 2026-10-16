"""Regras de negócio dos gastos: períodos (mês, semana), totais, resumo e remoção."""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date, timedelta

from app.clock import Clock
from app.domain import Expense
from app.repositories.base import ExpenseRepository

LATEST_LIMIT = 5


@dataclass(frozen=True)
class PeriodTotal:
    start: date
    end: date
    total_cents: int
    category: str | None = None


@dataclass(frozen=True)
class WeeklyReport:
    start: date
    end: date
    total_cents: int
    previous_start: date
    previous_end: date
    previous_total_cents: int
    by_category: dict[str, int] = field(default_factory=dict)

    @property
    def change_percent(self) -> float | None:
        """Variação em relação à semana anterior; None se a semana anterior foi zero."""
        if self.previous_total_cents == 0:
            return None
        diff = self.total_cents - self.previous_total_cents
        return diff / self.previous_total_cents * 100


class ExpenseService:
    def __init__(self, repository: ExpenseRepository, clock: Clock) -> None:
        self.repository = repository
        self.clock = clock

    def register(
        self, user_id: str, *, description: str, amount_cents: int, category: str, spent_on: date
    ) -> Expense:
        if amount_cents <= 0:
            raise ValueError("O valor do gasto precisa ser positivo")
        return self.repository.add(
            user_id=user_id,
            description=description.strip(),
            amount_cents=amount_cents,
            category=category,
            spent_on=spent_on,
            created_at=self.clock.now(),
        )

    def month_total(self, user_id: str, category: str | None = None) -> PeriodTotal:
        today = self.clock.today()
        start = today.replace(day=1)
        end = today.replace(day=calendar.monthrange(today.year, today.month)[1])
        total = self.repository.total(user_id, start, end, category=category)
        return PeriodTotal(start=start, end=end, total_cents=total, category=category)

    def weekly_summary(self, user_id: str) -> WeeklyReport:
        """Semana atual (segunda até hoje) comparada com o mesmo trecho da semana anterior."""
        today = self.clock.today()
        start = today - timedelta(days=today.weekday())
        previous_start, previous_end = start - timedelta(days=7), today - timedelta(days=7)
        return WeeklyReport(
            start=start,
            end=today,
            total_cents=self.repository.total(user_id, start, today),
            previous_start=previous_start,
            previous_end=previous_end,
            previous_total_cents=self.repository.total(user_id, previous_start, previous_end),
            by_category=self.repository.totals_by_category(user_id, start, today),
        )

    def latest(self, user_id: str, limit: int = LATEST_LIMIT) -> list[Expense]:
        return self.repository.latest(user_id, limit)

    def delete_last(self, user_id: str) -> Expense | None:
        latest = self.repository.latest(user_id, 1)
        if not latest:
            return None
        self.repository.delete(user_id, latest[0].id)
        return latest[0]
