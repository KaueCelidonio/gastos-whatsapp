from datetime import date

import pytest

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

TODAY = date(2025, 10, 16)  # mesma data do FixedClock em conftest.py


@pytest.mark.parametrize(
    ("message", "description", "cents", "spent_on", "category"),
    [
        ("almoço 32", "almoço", 3200, TODAY, "Alimentação"),
        ("uber 18,50", "uber", 1850, TODAY, "Transporte"),
        ("32 almoço", "almoço", 3200, TODAY, "Alimentação"),
        ("mercado 120,90", "mercado", 12090, TODAY, "Mercado"),
        ("uber 18.50", "uber", 1850, TODAY, "Transporte"),
        ("Almoço 32", "Almoço", 3200, TODAY, "Alimentação"),
        ("ALMOCO 32", "ALMOCO", 3200, TODAY, "Alimentação"),
        ("  almoço    32  ", "almoço", 3200, TODAY, "Alimentação"),
        ("almoço R$ 32", "almoço", 3200, TODAY, "Alimentação"),
        ("almoço R$32,90", "almoço", 3290, TODAY, "Alimentação"),
        ("aluguel 1.500,00", "aluguel", 150000, TODAY, "Moradia"),
        ("janta com a família 210", "janta com a família", 21000, TODAY, "Alimentação"),
        ("presente 50", "presente", 5000, TODAY, "Outros"),
        # datas
        ("uber 18,50 ontem", "uber", 1850, date(2025, 10, 15), "Transporte"),
        ("farmácia 40 12/10", "farmácia", 4000, date(2025, 10, 12), "Saúde"),
        ("cinema 60 anteontem", "cinema", 6000, date(2025, 10, 14), "Lazer"),
        ("ontem uber 18,50", "uber", 1850, date(2025, 10, 15), "Transporte"),
        ("40 farmácia 12/10", "farmácia", 4000, date(2025, 10, 12), "Saúde"),
        ("netflix 55,90 hoje", "netflix", 5590, TODAY, "Assinaturas"),
        ("luz 180 20/12", "luz", 18000, date(2024, 12, 20), "Moradia"),
        # número como descrição (palavra-chave "99")
        ("99 25", "99", 2500, TODAY, "Transporte"),
        ("25 99", "99", 2500, TODAY, "Transporte"),
        ("uber 99", "uber", 9900, TODAY, "Transporte"),
    ],
)
def test_register_expense(interpreter, message, description, cents, spent_on, category):
    assert interpreter.interpret(message) == RegisterExpense(
        description=description, amount_cents=cents, spent_on=spent_on, category=category
    )


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("total", MonthTotal()),
        ("Total", MonthTotal()),
        ("total do mês", MonthTotal()),
        ("total alimentação", CategoryTotal("Alimentação")),
        ("total alimentacao", CategoryTotal("Alimentação")),
        ("Total de Saúde", CategoryTotal("Saúde")),
        ("total outros", CategoryTotal("Outros")),
        ("total viagens", UnknownCategory("viagens")),
        ("resumo", WeeklySummary()),
        ("Resumo!", WeeklySummary()),
        ("últimos", LastExpenses()),
        ("ultimos", LastExpenses()),
        ("apagar último", DeleteLast()),
        ("apagar ultimo", DeleteLast()),
        ("desfazer", DeleteLast()),
        ("categorias", ListCategories()),
        ("ajuda", Help()),
        ("Ajuda?", Help()),
        ("oi", Help()),
        ("", Help()),
    ],
)
def test_commands(interpreter, message, intent):
    assert interpreter.interpret(message) == intent


@pytest.mark.parametrize(
    "message",
    [
        "almoço",  # sem valor
        "32",  # sem descrição
        "quanto gastei?",
        "almoço 0",  # valor zero
        "almoço 32 ontem 12/10",  # duas datas
        "10 20",  # dois números sem palavra-chave
        "almoço 32 com amigos",  # valor no meio
        "almoço 99999999999",  # valor absurdo
    ],
)
def test_unrecognized(interpreter, message):
    assert interpreter.interpret(message) == Unrecognized(message)
