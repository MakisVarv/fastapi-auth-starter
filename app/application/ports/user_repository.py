from typing import Protocol

from app.domain.entities.user import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None: ...
