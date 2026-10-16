"""Testes de ponta a ponta dos comandos: texto do usuário -> texto de resposta."""

from datetime import date

import pytest

from app.services import replies
from app.services.expense_service import ExpenseService
from app.services.message_handler import MessageHandler

USER = "5511999990001"
OTHER = "5511999990002"


@pytest.fixture
def handler(interpreter, expense_repo, categorizer, clock) -> MessageHandler:
    # clock: quinta-feira, 16/10/2025
    return MessageHandler(interpreter, ExpenseService(expense_repo, clock), categorizer, clock)


def send(handler, *messages, user=USER):
    return [handler.handle(user, m) for m in messages][-1]


def test_register_expense_reply(handler):
    assert send(handler, "almoço 32") == "✅ R$ 32,00 em Alimentação (hoje)"
    assert send(handler, "uber 18,50 ontem") == "✅ R$ 18,50 em Transporte (ontem)"
    assert send(handler, "farmácia 40 02/10") == "✅ R$ 40,00 em Saúde (02/10)"
    assert send(handler, "presente 50") == "✅ R$ 50,00 em Outros (hoje)"


def test_month_total(handler):
    reply = send(handler, "almoço 32", "uber 18,50", "mercado 120,90 20/09", "total")
    assert reply == "💰 Total de outubro: *R$ 50,50*"


def test_category_total(handler):
    reply = send(handler, "almoço 32", "janta 40,50", "uber 18", "total alimentação")
    assert reply == "📂 Alimentação em outubro: *R$ 72,50*"


def test_category_total_unknown_category(handler):
    reply = send(handler, "total viagens")
    assert "viagens" in reply
    assert "Alimentação" in reply and "Outros" in reply


def test_weekly_summary(handler):
    reply = send(
        handler,
        "almoço 30 13/10",  # segunda desta semana
        "uber 20",
        "janta 10 ontem",
        "mercado 40 06/10",  # segunda da semana passada
        "resumo",
    )
    assert reply == (
        "📊 *Resumo da semana* (13/10 a 16/10)\n"
        "Total: *R$ 60,00*\n"
        "\n"
        "Por categoria:\n"
        "• Alimentação: R$ 40,00\n"
        "• Transporte: R$ 20,00\n"
        "\n"
        "📈 50% a mais que no mesmo período da semana passada (R$ 40,00)."
    )


def test_weekly_summary_spending_less(handler):
    reply = send(handler, "almoço 10", "mercado 40 06/10", "resumo")
    assert reply.endswith("📉 75% a menos que no mesmo período da semana passada (R$ 40,00).")


def test_weekly_summary_empty(handler):
    reply = send(handler, "resumo")
    assert "Nenhum gasto nesta semana ainda." in reply
    assert "Sem gastos no mesmo período da semana passada." in reply


def test_latest(handler):
    for message in ["a 1", "b 2", "c 3", "d 4", "e 5", "almoço 32", "uber 18,50 ontem"]:
        handler.handle(USER, message)

    reply = send(handler, "últimos")
    lines = reply.splitlines()
    assert lines[0] == "🧾 *Últimos gastos*"
    assert lines[1] == "1. ontem · uber · R$ 18,50 (Transporte)"
    assert lines[2] == "2. hoje · almoço · R$ 32,00 (Alimentação)"
    assert len(lines) == 6


def test_latest_empty(handler):
    assert "ainda não registrou" in send(handler, "ultimos")


def test_delete_last(handler):
    reply = send(handler, "almoço 32", "uber 18,50", "apagar último")
    assert reply == "🗑️ Apagado: uber · R$ 18,50 (hoje)"
    assert send(handler, "total") == "💰 Total de outubro: *R$ 32,00*"


def test_delete_last_without_expenses(handler):
    assert send(handler, "apagar ultimo") == "Não há gastos para apagar."


def test_categories(handler):
    reply = send(handler, "categorias")
    assert reply.startswith("📂 *Categorias*")
    assert "• Alimentação (almoço, janta, jantar...)" in reply
    assert reply.splitlines()[-1] == "• Outros (todo o resto)"


def test_help_and_unrecognized(handler):
    assert send(handler, "ajuda") == replies.HELP
    assert send(handler, "quanto gastei com o carro?") == replies.UNRECOGNIZED


def test_users_do_not_see_each_other(handler):
    handler.handle(USER, "almoço 32")
    handler.handle(OTHER, "aluguel 1500")

    assert send(handler, "total", user=USER) == "💰 Total de outubro: *R$ 32,00*"
    assert send(handler, "total", user=OTHER) == "💰 Total de outubro: *R$ 1.500,00*"
    assert send(handler, "apagar último", user=OTHER).startswith("🗑️ Apagado: aluguel")
    assert send(handler, "total", user=USER) == "💰 Total de outubro: *R$ 32,00*"


def test_unrecognized_message_does_not_register_anything(handler, expense_repo):
    handler.handle(USER, "almoço")
    assert expense_repo.total(USER, date(2025, 1, 1), date(2025, 12, 31)) == 0
