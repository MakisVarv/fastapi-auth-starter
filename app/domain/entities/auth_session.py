from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.entities.base_entity import BaseEntity


@dataclass
class AuthSession(BaseEntity):
    user_id: UUID
    current_refresh_jti: str
    expires_at: datetime

    revoked_at: datetime | None = None
