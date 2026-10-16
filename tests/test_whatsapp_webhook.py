"""Testes do webhook do WhatsApp com a Graph API da Meta mockada (respx)."""

import hashlib
import hmac
import json
from datetime import timedelta

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from app.channels.whatsapp.security import is_valid_signature, is_valid_verify_token
from app.config import BASE_DIR, Settings
from app.dependencies import Container
from app.main import create_app
from tests.conftest import TZ

APP_SECRET = "segredo-de-teste"
VERIFY_TOKEN = "token-de-verificacao"
PHONE_NUMBER_ID = "123456789"
GRAPH_URL = f"https://graph.facebook.com/v23.0/{PHONE_NUMBER_ID}/messages"
USER = "5511999990001"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url="sqlite://",
        timezone=TZ,
        categories_file=BASE_DIR / "config" / "categorias.json",
        whatsapp_access_token="token-de-acesso",
        whatsapp_phone_number_id=PHONE_NUMBER_ID,
        whatsapp_app_secret=APP_SECRET,
        whatsapp_verify_token=VERIFY_TOKEN,
        whatsapp_api_version="v23.0",
    )


@pytest.fixture
def client(settings, clock):
    container = Container.from_settings(settings, clock=clock)
    with TestClient(create_app(container)) as test_client:
        yield test_client


@pytest.fixture
def graph_api():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.post(GRAPH_URL).mock(
            return_value=httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})
        )
        yield route


def sign(body: bytes, secret: str = APP_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def text_message(text, message_id="wamid.1", user=USER, sent_at=None):
    return {
        "from": user,
        "id": message_id,
        "timestamp": str(int(sent_at.timestamp())) if sent_at else "{now}",
        "type": "text",
        "text": {"body": text},
    }


def webhook_payload(*messages, clock):
    for message in messages:
        if message["timestamp"] == "{now}":
            message["timestamp"] = str(int(clock.now().timestamp()))
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"phone_number_id": PHONE_NUMBER_ID},
                            "contacts": [{"profile": {"name": "Teste"}, "wa_id": USER}],
                            "messages": list(messages),
                        },
                    }
                ],
            }
        ],
    }


def post(client, payload, signature=None):
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json"}
    headers["X-Hub-Signature-256"] = signature if signature is not None else sign(body)
    return client.post("/webhooks/whatsapp", content=body, headers=headers)


def sent_bodies(route):
    return [json.loads(call.request.content) for call in route.calls]


# --- segurança ---------------------------------------------------------------


def test_signature_validation():
    body = b'{"a": 1}'
    assert is_valid_signature(body, sign(body), APP_SECRET)
    assert not is_valid_signature(body, sign(body, "outro-segredo"), APP_SECRET)
    assert not is_valid_signature(body + b" ", sign(body), APP_SECRET)
    assert not is_valid_signature(body, None, APP_SECRET)
    assert not is_valid_signature(body, sign(body).removeprefix("sha256="), APP_SECRET)
    assert not is_valid_signature(body, sign(body, ""), "")  # sem segredo configurado


def test_verify_token_validation():
    assert is_valid_verify_token("abc", "abc")
    assert not is_valid_verify_token("abc", "xyz")
    assert not is_valid_verify_token(None, "abc")
    assert not is_valid_verify_token("", "")


def test_webhook_verification_returns_challenge(client):
    response = client.get(
        "/webhooks/whatsapp",
        params={"hub.mode": "subscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "42"},
    )
    assert response.status_code == 200
    assert response.text == "42"


@pytest.mark.parametrize(
    "params",
    [
        {"hub.mode": "subscribe", "hub.verify_token": "errado", "hub.challenge": "42"},
        {"hub.mode": "unsubscribe", "hub.verify_token": VERIFY_TOKEN, "hub.challenge": "42"},
        {"hub.challenge": "42"},
    ],
)
def test_webhook_verification_rejects_invalid(client, params):
    assert client.get("/webhooks/whatsapp", params=params).status_code == 403


def test_post_with_invalid_signature_is_rejected(client, graph_api, clock):
    payload = webhook_payload(text_message("almoço 32"), clock=clock)
    response = post(client, payload, signature="sha256=" + "0" * 64)
    assert response.status_code == 403
    assert not graph_api.called


def test_post_without_signature_is_rejected(client, graph_api, clock):
    body = json.dumps(webhook_payload(text_message("almoço 32"), clock=clock)).encode()
    response = client.post("/webhooks/whatsapp", content=body)
    assert response.status_code == 403


# --- fluxo de mensagens --------------------------------------------------------


def test_text_message_registers_expense_and_replies(client, graph_api, clock):
    response = post(client, webhook_payload(text_message("almoço 32"), clock=clock))

    assert response.status_code == 200
    assert graph_api.call_count == 1
    request = graph_api.calls.last.request
    assert request.headers["Authorization"] == "Bearer token-de-acesso"
    assert json.loads(request.content) == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": USER,
        "type": "text",
        "text": {"preview_url": False, "body": "✅ R$ 32,00 em Alimentação (hoje)"},
    }


def test_full_conversation(client, graph_api, clock):
    post(client, webhook_payload(text_message("almoço 32", "wamid.1"), clock=clock))
    post(client, webhook_payload(text_message("uber 18,50", "wamid.2"), clock=clock))
    post(client, webhook_payload(text_message("total", "wamid.3"), clock=clock))

    replies = [body["text"]["body"] for body in sent_bodies(graph_api)]
    assert replies[-1] == "💰 Total de outubro: *R$ 50,50*"


def test_duplicate_delivery_is_processed_once(client, graph_api, clock):
    payload = webhook_payload(text_message("almoço 32", "wamid.dup"), clock=clock)
    post(client, payload)
    post(client, payload)
    post(client, webhook_payload(text_message("total", "wamid.total"), clock=clock))

    replies = [body["text"]["body"] for body in sent_bodies(graph_api)]
    assert len(replies) == 2
    assert replies[-1] == "💰 Total de outubro: *R$ 32,00*"


def test_status_events_are_ignored(client, graph_api):
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {"statuses": [{"id": "wamid.out", "status": "delivered"}]},
                    }
                ]
            }
        ],
    }
    assert post(client, payload).status_code == 200
    assert not graph_api.called


def test_non_text_message_gets_friendly_reply(client, graph_api, clock):
    audio = {
        "from": USER,
        "id": "wamid.audio",
        "timestamp": str(int(clock.now().timestamp())),
        "type": "audio",
        "audio": {"id": "media-id"},
    }
    post(client, webhook_payload(audio, clock=clock))
    assert "só entendo mensagens de texto" in sent_bodies(graph_api)[0]["text"]["body"]


def test_message_older_than_24h_is_saved_but_not_answered(client, graph_api, clock):
    old = clock.now() - timedelta(hours=25)
    post(client, webhook_payload(text_message("almoço 32", "wamid.old", sent_at=old), clock=clock))
    assert not graph_api.called

    post(client, webhook_payload(text_message("total", "wamid.new"), clock=clock))
    assert sent_bodies(graph_api)[-1]["text"]["body"] == "💰 Total de outubro: *R$ 32,00*"


def test_graph_api_failure_does_not_break_webhook(client, graph_api, clock):
    graph_api.mock(return_value=httpx.Response(400, json={"error": {"code": 131030}}))
    response = post(client, webhook_payload(text_message("almoço 32"), clock=clock))
    assert response.status_code == 200


def test_invalid_json_with_valid_signature(client):
    body = b"isto nao e json"
    response = client.post(
        "/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": sign(body)}
    )
    assert response.status_code == 400


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
