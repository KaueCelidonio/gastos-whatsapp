"""Converse com o bot no terminal, sem WhatsApp, Meta ou ngrok.

Uso:
    python -m scripts.chat_local                 # banco local em chat_local.db
    python -m scripts.chat_local --memoria       # banco em memória (some ao sair)
    python -m scripts.chat_local --usuario 5511999990001
"""

from __future__ import annotations

import argparse
import sys

from app.clock import Clock
from app.config import get_settings
from app.db.database import build_engine, build_session_factory, init_db
from app.dependencies import build_interpreter
from app.interpretation.categorizer import Categorizer
from app.repositories.sqlalchemy_repository import SqlAlchemyExpenseRepository
from app.services.expense_service import ExpenseService
from app.services.message_handler import MessageHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Chat local com o assistente de gastos")
    parser.add_argument("--memoria", action="store_true", help="usa banco em memória")
    parser.add_argument("--usuario", default="local", help="identificador do usuário")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # emojis no terminal do Windows

    settings = get_settings()
    clock = Clock(settings.timezone)
    categorizer = Categorizer.from_json(settings.categories_file)
    engine = build_engine("sqlite://" if args.memoria else "sqlite:///./chat_local.db")
    init_db(engine)

    with build_session_factory(engine)() as session:
        service = ExpenseService(SqlAlchemyExpenseRepository(session), clock)
        handler = MessageHandler(build_interpreter(categorizer, clock), service, categorizer, clock)

        print("💬 Chat local do assistente de gastos. Digite 'ajuda' ou 'sair'.\n")
        while True:
            try:
                text = input("você > ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if text.lower() in {"sair", "exit", "quit"}:
                break
            print(f"bot  > {handler.handle(args.usuario, text)}\n")

    engine.dispose()


if __name__ == "__main__":
    main()
