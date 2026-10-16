"""Validações exigidas pela Meta: token de verificação e assinatura HMAC do webhook."""

import hashlib
import hmac

SIGNATURE_PREFIX = "sha256="


def is_valid_signature(raw_body: bytes, signature_header: str | None, app_secret: str) -> bool:
    """Confere o cabeçalho X-Hub-Signature-256 (HMAC-SHA256 do corpo com a App Secret)."""
    if not app_secret or not signature_header or not signature_header.startswith(SIGNATURE_PREFIX):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix(SIGNATURE_PREFIX)
    return hmac.compare_digest(expected, received)


def is_valid_verify_token(received: str | None, expected: str) -> bool:
    if not expected or received is None:
        return False
    return hmac.compare_digest(received.encode(), expected.encode())
