"""Rotas do webhook do WhatsApp: verificação (GET) e recebimento de mensagens (POST)."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.channels.whatsapp.security import is_valid_signature, is_valid_verify_token
from app.dependencies import Container

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])


def _container(request: Request) -> Container:
    return request.app.state.container


@router.get("", response_class=PlainTextResponse)
def verify_webhook(
    request: Request,
    mode: str | None = Query(None, alias="hub.mode"),
    token: str | None = Query(None, alias="hub.verify_token"),
    challenge: str = Query("", alias="hub.challenge"),
) -> str:
    """A Meta chama esta rota uma vez, ao cadastrar o webhook, e espera o challenge de volta."""
    expected = _container(request).settings.whatsapp_verify_token
    if mode != "subscribe" or not is_valid_verify_token(token, expected):
        raise HTTPException(status_code=403, detail="Token de verificação inválido")
    return challenge


@router.post("")
async def receive_webhook(request: Request) -> dict[str, str]:
    container = _container(request)
    raw_body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256")
    if not is_valid_signature(raw_body, signature, container.settings.whatsapp_app_secret):
        logger.warning("Webhook rejeitado: assinatura inválida")
        raise HTTPException(status_code=403, detail="Assinatura inválida")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="JSON inválido") from exc

    channel = container.whatsapp
    messages = channel.parse_incoming(payload)
    if messages:
        with container.session_factory() as session:
            conversation = container.conversation(session)
            for message in messages:
                await conversation.process(message, channel)

    # Sempre 200 para eventos válidos; senão a Meta reenvia o mesmo evento várias vezes.
    return {"status": "ok"}
