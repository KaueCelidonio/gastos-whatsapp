"""Canal WhatsApp via Cloud API oficial da Meta."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.channels.base import IncomingMessage, MessageChannel

logger = logging.getLogger(__name__)

GRAPH_API_URL = "https://graph.facebook.com"


class WhatsAppChannel(MessageChannel):
    name = "whatsapp"

    def __init__(
        self,
        *,
        access_token: str,
        phone_number_id: str,
        api_version: str,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._access_token = access_token
        self._messages_url = f"{GRAPH_API_URL}/{api_version}/{phone_number_id}/messages"
        self._http = http_client

    def parse_incoming(self, payload: dict[str, Any]) -> list[IncomingMessage]:
        """Lê só eventos de mensagens recebidas; status de entrega/leitura são ignorados."""
        if payload.get("object") != "whatsapp_business_account":
            return []

        messages = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") != "messages":
                    continue
                for message in change.get("value", {}).get("messages", []):
                    parsed = self._parse_message(message)
                    if parsed:
                        messages.append(parsed)
        return messages

    @staticmethod
    def _parse_message(message: dict[str, Any]) -> IncomingMessage | None:
        try:
            text = message["text"]["body"] if message.get("type") == "text" else None
            return IncomingMessage(
                message_id=message["id"],
                user_id=message["from"],
                text=text,
                sent_at=datetime.fromtimestamp(int(message["timestamp"]), tz=UTC),
            )
        except (KeyError, TypeError, ValueError):
            logger.warning("Mensagem do WhatsApp em formato inesperado foi ignorada")
            return None

    async def send_text(self, user_id: str, text: str) -> None:
        response = await self._http.post(
            self._messages_url,
            headers={"Authorization": f"Bearer {self._access_token}"},
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": user_id,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            },
        )
        response.raise_for_status()
