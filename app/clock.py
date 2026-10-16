"""Relógio injetável: o código pede a data/hora aqui, e os testes usam um relógio fixo."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo


class Clock:
    def __init__(self, timezone: ZoneInfo) -> None:
        self.timezone = timezone

    def now(self) -> datetime:
        return datetime.now(self.timezone)

    def today(self) -> date:
        return self.now().date()


class FixedClock(Clock):
    def __init__(self, fixed: datetime) -> None:
        if fixed.tzinfo is None:
            raise ValueError("FixedClock precisa de um datetime com fuso horário")
        super().__init__(fixed.tzinfo)  # type: ignore[arg-type]
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed
