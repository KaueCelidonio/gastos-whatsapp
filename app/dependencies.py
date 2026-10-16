"""Montagem das peças da aplicação (injeção de dependências manual).

É aqui, e só aqui, que se escolhe qual interpretador, canal e banco usar.
Para trocar o RuleBasedInterpreter por um AIInterpreter, basta mudar `build_interpreter`.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.channels.whatsapp.channel import WhatsAppChannel
from app.clock import Clock
from app.config import Settings
from app.db.database import build_engine, build_session_factory, init_db
from app.interpretation.base import MessageInterpreter
from app.interpretation.categorizer import Categorizer
from app.interpretation.rule_based import RuleBasedInterpreter
from app.repositories.sqlalchemy_repository import (
    SqlAlchemyExpenseRepository,
    SqlAlchemyProcessedMessageRepository,
)
from app.services.conversation import ConversationService
from app.services.expense_service import ExpenseService
from app.services.message_handler import MessageHandler


@dataclass
class Container:
    settings: Settings
    clock: Clock
    categorizer: Categorizer
    interpreter: MessageInterpreter
    engine: Engine
    session_factory: sessionmaker[Session]
    http_client: httpx.AsyncClient
    whatsapp: WhatsAppChannel

    @classmethod
    def from_settings(cls, settings: Settings, clock: Clock | None = None) -> Container:
        clock = clock or Clock(settings.timezone)
        categorizer = Categorizer.from_json(settings.categories_file)
        engine = build_engine(settings.database_url)
        init_db(engine)
        http_client = httpx.AsyncClient(timeout=10)
        return cls(
            settings=settings,
            clock=clock,
            categorizer=categorizer,
            interpreter=build_interpreter(categorizer, clock),
            engine=engine,
            session_factory=build_session_factory(engine),
            http_client=http_client,
            whatsapp=WhatsAppChannel(
                access_token=settings.whatsapp_access_token,
                phone_number_id=settings.whatsapp_phone_number_id,
                api_version=settings.whatsapp_api_version,
                http_client=http_client,
            ),
        )

    def message_handler(self, session: Session) -> MessageHandler:
        service = ExpenseService(SqlAlchemyExpenseRepository(session), self.clock)
        return MessageHandler(self.interpreter, service, self.categorizer, self.clock)

    def conversation(self, session: Session) -> ConversationService:
        return ConversationService(
            self.message_handler(session),
            SqlAlchemyProcessedMessageRepository(session),
            self.clock,
        )

    async def aclose(self) -> None:
        await self.http_client.aclose()
        self.engine.dispose()


def build_interpreter(categorizer: Categorizer, clock: Clock) -> MessageInterpreter:
    return RuleBasedInterpreter(categorizer, clock)
