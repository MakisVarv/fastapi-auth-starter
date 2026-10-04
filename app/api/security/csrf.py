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
