"""Implementação dos repositórios com SQLAlchemy (funciona com SQLite e PostgreSQL)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import ExpenseRow, ProcessedMessageRow
from app.domain import Expense
from app.repositories.base import ExpenseRepository, ProcessedMessageRepository


def _to_domain(row: ExpenseRow) -> Expense:
    return Expense(
        id=row.id,
        user_id=row.user_id,
        description=row.description,
        amount_cents=row.amount_cents,
        category=row.category,
        spent_on=row.spent_on,
        created_at=row.created_at,
    )


class SqlAlchemyExpenseRepository(ExpenseRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(
        self,
        *,
        user_id: str,
        description: str,
        amount_cents: int,
        category: str,
        spent_on: date,
        created_at: datetime,
    ) -> Expense:
        row = ExpenseRow(
            user_id=user_id,
            description=description,
            amount_cents=amount_cents,
            category=category,
            spent_on=spent_on,
            created_at=created_at,
        )
        self.session.add(row)
        self.session.commit()
        return _to_domain(row)

    def total(self, user_id: str, start: date, end: date, category: str | None = None) -> int:
        query = select(func.coalesce(func.sum(ExpenseRow.amount_cents), 0)).where(
            ExpenseRow.user_id == user_id,
            ExpenseRow.spent_on.between(start, end),
        )
        if category is not None:
            query = query.where(ExpenseRow.category == category)
        return int(self.session.scalar(query) or 0)

    def totals_by_category(self, user_id: str, start: date, end: date) -> dict[str, int]:
        total = func.sum(ExpenseRow.amount_cents).label("total")
        query = (
            select(ExpenseRow.category, total)
            .where(ExpenseRow.user_id == user_id, ExpenseRow.spent_on.between(start, end))
            .group_by(ExpenseRow.category)
            .order_by(total.desc(), ExpenseRow.category)
        )
        return {category: int(value) for category, value in self.session.execute(query)}

    def latest(self, user_id: str, limit: int) -> list[Expense]:
        query = (
            select(ExpenseRow)
            .where(ExpenseRow.user_id == user_id)
            .order_by(ExpenseRow.created_at.desc(), ExpenseRow.id.desc())
            .limit(limit)
        )
        return [_to_domain(row) for row in self.session.scalars(query)]

    def delete(self, user_id: str, expense_id: int) -> bool:
        result = self.session.execute(
            delete(ExpenseRow).where(ExpenseRow.id == expense_id, ExpenseRow.user_id == user_id)
        )
        self.session.commit()
        return result.rowcount > 0


class SqlAlchemyProcessedMessageRepository(ProcessedMessageRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def mark_processed(self, message_id: str, received_at: datetime) -> bool:
        self.session.add(ProcessedMessageRow(message_id=message_id, received_at=received_at))
        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            return False
        return True
