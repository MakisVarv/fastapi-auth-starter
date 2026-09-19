from app.application.common.pagination import Page
from app.application.common.sorting import SortOptions
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User


class ListUsers:

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(
        self,
        *,
        page: int,
        page_size: int,
        sort_options: SortOptions,
        search: str | None,
        role: str | None,
        is_active: bool | None
    ) -> Page[User]:
        with self.uow:
            users = self.uow.users.list_paginated(
                page=page,
                page_size=page_size,
                sort_options=sort_options,
                search=search,
                role=role,
                is_active=is_active,
            )
            return users
