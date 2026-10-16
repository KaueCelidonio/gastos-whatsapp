from datetime import date, datetime

import pytest

from app.clock import FixedClock
from app.services.expense_service import ExpenseService, WeeklyReport
from tests.conftest import TZ

USER = "5511999990001"
OTHER = "5511999990002"


@pytest.fixture
def service(expense_repo, clock) -> ExpenseService:
    # clock: quinta-feira, 16/10/2025
    return ExpenseService(expense_repo, clock)


def register(service, cents, spent_on, category="Alimentação", user=USER, desc="gasto"):
    return service.register(
        user, description=desc, amount_cents=cents, category=category, spent_on=spent_on
    )


def test_register_strips_description_and_sets_created_at(service, clock):
    expense = register(service, 3200, date(2025, 10, 16), desc="  almoço ")
    assert expense.description == "almoço"
    assert expense.created_at == clock.now()


def test_register_rejects_non_positive_amount(service):
    with pytest.raises(ValueError):
        register(service, 0, date(2025, 10, 16))


def test_month_total_covers_whole_current_month(service):
    register(service, 1000, date(2025, 10, 1))
    register(service, 2000, date(2025, 10, 16), category="Transporte")
    register(service, 9999, date(2025, 9, 30))
    register(service, 7777, date(2025, 10, 10), user=OTHER)

    result = service.month_total(USER)
    assert (result.start, result.end) == (date(2025, 10, 1), date(2025, 10, 31))
    assert result.total_cents == 3000
    assert service.month_total(USER, "Transporte").total_cents == 2000


def test_month_total_handles_february_in_leap_year(expense_repo):
    service = ExpenseService(expense_repo, FixedClock(datetime(2024, 2, 10, tzinfo=TZ)))
    assert service.month_total(USER).end == date(2024, 2, 29)


def test_weekly_summary_compares_with_same_span_of_previous_week(service):
    # Semana atual: seg 13/10 a qui 16/10. Mesmo trecho anterior: seg 06/10 a qui 09/10.
    register(service, 3000, date(2025, 10, 13), category="Alimentação")
    register(service, 2000, date(2025, 10, 16), category="Transporte")
    register(service, 1000, date(2025, 10, 15), category="Alimentação")
    register(service, 4000, date(2025, 10, 6))
    register(service, 9999, date(2025, 10, 10))  # sexta anterior: fora da comparação
    register(service, 9999, date(2025, 10, 12))  # domingo: semana anterior

    report = service.weekly_summary(USER)

    assert (report.start, report.end) == (date(2025, 10, 13), date(2025, 10, 16))
    assert (report.previous_start, report.previous_end) == (date(2025, 10, 6), date(2025, 10, 9))
    assert report.total_cents == 6000
    assert report.previous_total_cents == 4000
    assert report.by_category == {"Alimentação": 4000, "Transporte": 2000}
    assert report.change_percent == pytest.approx(50.0)


def test_weekly_summary_on_monday_is_single_day(expense_repo):
    monday = FixedClock(datetime(2025, 10, 13, 9, tzinfo=TZ))
    report = ExpenseService(expense_repo, monday).weekly_summary(USER)
    assert report.start == report.end == date(2025, 10, 13)
    assert report.previous_start == report.previous_end == date(2025, 10, 6)


def test_change_percent_is_none_without_previous_spending():
    report = WeeklyReport(
        start=date(2025, 10, 13),
        end=date(2025, 10, 16),
        total_cents=100,
        previous_start=date(2025, 10, 6),
        previous_end=date(2025, 10, 9),
        previous_total_cents=0,
    )
    assert report.change_percent is None


def test_latest_and_delete_last(service):
    for i in range(7):
        register(service, 100 * (i + 1), date(2025, 10, 16), desc=f"gasto {i}")

    assert [e.description for e in service.latest(USER)] == [
        "gasto 6",
        "gasto 5",
        "gasto 4",
        "gasto 3",
        "gasto 2",
    ]

    removed = service.delete_last(USER)
    assert removed.description == "gasto 6"
    assert service.latest(USER, 1)[0].description == "gasto 5"


def test_delete_last_without_expenses_returns_none(service):
    assert service.delete_last(USER) is None


def test_delete_last_does_not_touch_other_users(service):
    register(service, 100, date(2025, 10, 16), user=OTHER)
    assert service.delete_last(USER) is None
    assert service.month_total(OTHER).total_cents == 100
