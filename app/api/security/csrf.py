import hashlib
import hmac
import secrets

from app.infrastructure.config import settings


def generate_csrf_token(refresh_token: str) -> str:
    nonce = secrets.token_urlsafe(32)
    message = f"{refresh_token}.{nonce}"
    key = settings.CSRF_SECRET_KEY.encode()
    message_bytes = message.encode()
    signature = hmac.new(
        key=key,
        msg=message_bytes,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return f"{nonce}.{signature}"


def verify_csrf_token(
    refresh_token: str,
    csrf_token: str,
) -> bool:
    parts = csrf_token.rsplit(".", 1)

    if len(parts) != 2:
        return False

    nonce, provided_signature = parts

    message = f"{refresh_token}.{nonce}"
    expected_signature = hmac.new(
        key=settings.CSRF_SECRET_KEY.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        provided_signature,
        expected_signature,
    )
