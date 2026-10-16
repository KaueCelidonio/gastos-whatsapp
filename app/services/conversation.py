"""Fluxo de uma mensagem recebida, válido para qualquer canal.

1. Ignora mensagens repetidas (a Meta reenvia o webhook quando há falha).
2. Gera a resposta com o MessageHandler.
3. Só responde dentro da janela de 24h aberta pela mensagem do usuário,
   que é quando a resposta é permitida e gratuita na API do WhatsApp.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from app.channels.base import IncomingMessage, MessageChannel
from app.clock import Clock
from app.repositories.base import ProcessedMessageRepository
from app.services.message_handler import MessageHandler

logger = logging.getLogger(__name__)

REPLY_WINDOW = timedelta(hours=24)
NON_TEXT_REPLY = "Por enquanto eu só entendo mensagens de texto. Digite *ajuda* para ver exemplos."


class ConversationService:
    def __init__(
        self,
        handler: MessageHandler,
        processed: ProcessedMessageRepository,
        clock: Clock,
    ) -> None:
        self.handler = handler
        self.processed = processed
        self.clock = clock

    async def process(self, message: IncomingMessage, channel: MessageChannel) -> str | None:
        """Processa a mensagem e devolve a resposta enviada (ou None se nada foi enviado)."""
        now = self.clock.now()
        if not self.processed.mark_processed(f"{channel.name}:{message.message_id}", now):
            logger.info("Mensagem %s repetida, ignorada", message.message_id)
            return None

        if message.text is None:
            reply = NON_TEXT_REPLY
        else:
            reply = self.handler.handle(message.user_id, message.text)

        if now - message.sent_at > REPLY_WINDOW:
            logger.info("Mensagem %s fora da janela de 24h: sem resposta", message.message_id)
            return None

        try:
            await channel.send_text(message.user_id, reply)
        except Exception:
            logger.exception("Falha ao enviar resposta pelo canal %s", channel.name)
            return None
        return reply
