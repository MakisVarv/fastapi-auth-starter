from typing import Protocol, Self

from app.application.ports.user_repository import UserRepository


class UnitOfWork(Protocol):
    users: UserRepository

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
