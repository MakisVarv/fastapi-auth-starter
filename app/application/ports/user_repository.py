import uuid
from typing import Protocol

from app.domain.entities.user import User


class UserRepository(Protocol):

    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None: ...
