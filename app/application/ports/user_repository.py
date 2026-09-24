from typing import Protocol
from uuid import UUID

from app.application.common.pagination import Page
from app.application.common.sorting import SortOptions
from app.domain.entities.user import User


class UserRepository(Protocol):

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        sort_options: SortOptions,
        search: str | None,
        role: str | None,
        is_active: bool | None,
    ) -> Page[User]: ...

    def get_by_id(self, user_id: UUID, /) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None: ...

    def update(self, user: User) -> None: ...

    def delete(self, entity: User) -> None: ...

    def count_by_role(self, role_id: UUID) -> int: ...
