"""Textos de resposta do bot, no formato brasileiro (R$ 1.234,56 e datas dd/mm)."""

from __future__ import annotations

from datetime import date

from app.domain import Expense
from app.interpretation.categorizer import Categorizer
from app.services.expense_service import PeriodTotal, WeeklyReport

MONTHS = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)  # fmt: skip

_RELATIVE_DAY_NAMES = {0: "hoje", 1: "ontem", 2: "anteontem"}


def format_brl(cents: int) -> str:
    reais, centavos = divmod(abs(cents), 100)
    sign = "-" if cents < 0 else ""
    return f"{sign}R$ {reais:,}".replace(",", ".") + f",{centavos:02d}"


def format_day(day: date, today: date) -> str:
    delta = (today - day).days
    if delta in _RELATIVE_DAY_NAMES:
        return _RELATIVE_DAY_NAMES[delta]
    if day.year == today.year:
        return day.strftime("%d/%m")
    return day.strftime("%d/%m/%Y")


def expense_registered(expense: Expense, today: date) -> str:
    when = format_day(expense.spent_on, today)
    return f"✅ {format_brl(expense.amount_cents)} em {expense.category} ({when})"


def month_total(result: PeriodTotal) -> str:
    month = MONTHS[result.start.month - 1]
    if result.category:
        return f"📂 {result.category} em {month}: *{format_brl(result.total_cents)}*"
    return f"💰 Total de {month}: *{format_brl(result.total_cents)}*"


def unknown_category(name: str, categorizer: Categorizer) -> str:
    options = ", ".join(categorizer.categories)
    return f"🤔 Não conheço a categoria “{name}”.\nCategorias disponíveis: {options}."


def weekly_summary(report: WeeklyReport) -> str:
    period = f"{report.start:%d/%m} a {report.end:%d/%m}"
    if report.start == report.end:
        period = f"{report.start:%d/%m}"
    lines = [f"📊 *Resumo da semana* ({period})"]

    if report.total_cents == 0:
        lines.append("Nenhum gasto nesta semana ainda.")
    else:
        lines.append(f"Total: *{format_brl(report.total_cents)}*")
        lines.append("")
        lines.append("Por categoria:")
        lines.extend(
            f"• {category}: {format_brl(cents)}" for category, cents in report.by_category.items()
        )

    lines.append("")
    lines.append(_comparison(report))
    return "\n".join(lines)


def _comparison(report: WeeklyReport) -> str:
    previous = format_brl(report.previous_total_cents)
    change = report.change_percent
    if change is None:
        return "Sem gastos no mesmo período da semana passada."
    if round(change) == 0:
        return f"➖ Praticamente igual ao mesmo período da semana passada ({previous})."
    direction, emoji = ("a mais", "📈") if change > 0 else ("a menos", "📉")
    percent = f"{abs(change):.0f}%"
    return f"{emoji} {percent} {direction} que no mesmo período da semana passada ({previous})."


def latest(expenses: list[Expense], today: date) -> str:
    if not expenses:
        return "Você ainda não registrou nenhum gasto. Experimente: *almoço 32*"
    lines = ["🧾 *Últimos gastos*"]
    for i, expense in enumerate(expenses, start=1):
        lines.append(
            f"{i}. {format_day(expense.spent_on, today)} · {expense.description} · "
            f"{format_brl(expense.amount_cents)} ({expense.category})"
        )
    return "\n".join(lines)


def deleted(expense: Expense | None, today: date) -> str:
    if expense is None:
        return "Não há gastos para apagar."
    return (
        f"🗑️ Apagado: {expense.description} · {format_brl(expense.amount_cents)} "
        f"({format_day(expense.spent_on, today)})"
    )


def categories(categorizer: Categorizer) -> str:
    lines = ["📂 *Categorias*"]
    for category in categorizer.categories:
        examples = categorizer.keywords(category)[:3]
        suffix = f" ({', '.join(examples)}...)" if examples else " (todo o resto)"
        lines.append(f"• {category}{suffix}")
    return "\n".join(lines)


HELP = """🤖 *Assistente de gastos*

*Registrar um gasto:* descrição e valor
• almoço 32
• uber 18,50 ontem
• 120,90 mercado
• farmácia 40 12/10

*Consultar:*
• *total*: total do mês
• *total alimentação*: total de uma categoria no mês
• *resumo*: resumo da semana
• *últimos*: últimos 5 gastos
• *apagar último*: desfaz o último registro
• *categorias*: lista as categorias
• *ajuda*: mostra esta mensagem"""

UNRECOGNIZED = (
    "🤔 Não entendi. Para registrar um gasto, mande descrição e valor, "
    "por exemplo *almoço 32* ou *uber 18,50 ontem*.\n"
    "Digite *ajuda* para ver todos os comandos."
)
