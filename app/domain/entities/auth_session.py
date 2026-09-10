from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class AuthSession:
    user_id: UUID
    current_refresh_jti: str
    expires_at: datetime

    id: UUID = field(default_factory=uuid4)
    revoked_at: datetime | None = None
