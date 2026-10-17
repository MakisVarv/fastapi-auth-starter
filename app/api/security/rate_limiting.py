from slowapi import Limiter
from slowapi.util import get_remote_address

from app.infrastructure.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    in_memory_fallback_enabled=True,
)
