"""Contrato de um canal de mensagens (WhatsApp hoje, Telegram amanhã)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class IncomingMessage:
    message_id: str
    user_id: str
    text: str | None  # None quando não é texto (áudio, imagem, figurinha...)
    sent_at: datetime


class MessageChannel(ABC):
    name: str

    @abstractmethod
    def parse_incoming(self, payload: dict[str, Any]) -> list[IncomingMessage]:
        """Extrai as mensagens enviadas por usuários do payload do webhook."""

    @abstractmethod
    async def send_text(self, user_id: str, text: str) -> None:
        """Envia uma resposta de texto ao usuário."""
