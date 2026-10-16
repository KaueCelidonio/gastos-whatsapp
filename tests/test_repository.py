from datetime import date, datetime, timedelta

from tests.conftest import TZ

ALICE = "5511999990001"
BOB = "5511999990002"
BASE_TIME = datetime(2025, 10, 16, 12, 0, tzinfo=TZ)


def add(
    repo,
    user=ALICE,
    desc="almoço",
    cents=3200,
    category="Alimentação",
    spent_on=date(2025, 10, 16),
    minutes=0,
):
    return repo.add(
        user_id=user,
        description=desc,
        amount_cents=cents,
        category=category,
        spent_on=spent_on,
        created_at=BASE_TIME + timedelta(minutes=minutes),
    )


def test_add_returns_domain_expense(expense_repo):
    expense = add(expense_repo)
    assert expense.id is not None
    assert expense.user_id == ALICE
    assert expense.amount_cents == 3200


def test_total_respects_period_and_category(expense_repo):
    add(expense_repo, cents=1000, spent_on=date(2025, 10, 1))
    add(expense_repo, cents=2000, spent_on=date(2025, 10, 31), category="Lazer")
    add(expense_repo, cents=5000, spent_on=date(2025, 9, 30))  # fora do período

    start, end = date(2025, 10, 1), date(2025, 10, 31)
    assert expense_repo.total(ALICE, start, end) == 3000
    assert expense_repo.total(ALICE, start, end, category="Lazer") == 2000
    assert expense_repo.total(ALICE, start, end, category="Saúde") == 0


def test_totals_by_category_sorted_desc(expense_repo):
    add(expense_repo, cents=1000, category="Alimentação")
    add(expense_repo, cents=1500, category="Alimentação")
    add(expense_repo, cents=9000, category="Mercado")
    add(expense_repo, cents=500, category="Transporte")

    totals = expense_repo.totals_by_category(ALICE, date(2025, 10, 1), date(2025, 10, 31))
    assert list(totals.items()) == [("Mercado", 9000), ("Alimentação", 2500), ("Transporte", 500)]


def test_latest_uses_registration_order(expense_repo):
    add(expense_repo, desc="primeiro", spent_on=date(2025, 10, 16), minutes=0)
    add(expense_repo, desc="segundo (data antiga)", spent_on=date(2025, 10, 1), minutes=1)
    add(expense_repo, desc="terceiro", minutes=2)

    latest = expense_repo.latest(ALICE, limit=2)
    assert [e.description for e in latest] == ["terceiro", "segundo (data antiga)"]


def test_delete(expense_repo):
    expense = add(expense_repo)
    assert expense_repo.delete(ALICE, expense.id) is True
    assert expense_repo.latest(ALICE, 5) == []
    assert expense_repo.delete(ALICE, expense.id) is False


def test_users_are_isolated(expense_repo):
    alice_expense = add(expense_repo, user=ALICE, cents=1000)
    add(expense_repo, user=BOB, cents=7000)

    period = (date(2025, 10, 1), date(2025, 10, 31))
    assert expense_repo.total(ALICE, *period) == 1000
    assert expense_repo.total(BOB, *period) == 7000
    assert [e.user_id for e in expense_repo.latest(ALICE, 5)] == [ALICE]
    # Bob não consegue apagar o gasto da Alice
    assert expense_repo.delete(BOB, alice_expense.id) is False
    assert expense_repo.total(ALICE, *period) == 1000


def test_processed_messages_detects_duplicates(processed_repo):
    assert processed_repo.mark_processed("wamid.1", BASE_TIME) is True
    assert processed_repo.mark_processed("wamid.1", BASE_TIME) is False
    assert processed_repo.mark_processed("wamid.2", BASE_TIME) is True
