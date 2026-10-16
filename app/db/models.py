"""Tabelas do banco (SQLAlchemy ORM)."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ExpenseRow(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(255))
    amount_cents: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(64))
    spent_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_expenses_user_spent_on", "user_id", "spent_on"),)


class ProcessedMessageRow(Base):
    """IDs de mensagens já tratadas, para ignorar reenvios do webhook."""

    __tablename__ = "processed_messages"

    message_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
