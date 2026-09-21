from dataclasses import dataclass

from app.domain.entities.base_entity import BaseEntity
from app.domain.entities.role import Role


@dataclass
class User(BaseEntity):
    first_name: str
    last_name: str
    email: str
    password_hash: str
    role: Role
    phone: str | None = None
    is_active: bool = True
