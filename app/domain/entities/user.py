from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.entities.role import Role


@dataclass
class User:
    first_name: str
    last_name: str
    email: str
    password_hash: str
    role: Role
    phone: str | None = None
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
