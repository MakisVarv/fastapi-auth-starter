import hashlib

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.infrastructure.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    in_memory_fallback_enabled=True,
)


async def prepare_email_rate_limit(request: Request):
    req = await request.json()

    email = req.get("email") if isinstance(req, dict) else None

    if not isinstance(email, str):
        email = None
    key = email_rate_limit_key(email)
    request.state.email_limit_key = key


def get_email_rate_limit_key(request: Request):
    key = getattr(request.state, "email_limit_key", "unknown-email")
    return key


def email_rate_limit_key(email: str | None) -> str:
    if email is None or email.strip() == "":
        return "unknown-email"
    normalized_email = email.strip().lower()
    hashed = hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
    return hashed
