from typing import cast

from app.application.common.pagination import Page
from app.application.common.sorting import SortOptions
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.list_users import ListUsers
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(self, result: Page[User]) -> None:
        self.result = result
        self.received_args: dict | None = None

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
        sort_options: SortOptions,
        search: str | None,
        role: str | None,
        is_active: bool | None,
    ) -> Page[User]:
        self.received_args = {
            "page": page,
            "page_size": page_size,
            "sort_options": sort_options,
            "search": search,
            "role": role,
            "is_active": is_active,
        }

        return self.result


class FakeUnitOfWork:
    def __init__(self, result: Page[User]) -> None:
        self.users = FakeUserRepository(result)

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass


def make_user() -> User:
    return User(
        first_name="Alice",
        last_name="Stone",
        email="alice@example.com",
        password_hash="hash",
        role=Role(
            name="User",
            level=10,
        ),
    )


def test_list_users_forwards_query_options_and_returns_page() -> None:
    user = make_user()

    expected_page = Page(
        items=[user],
        page=2,
        page_size=10,
        total=15,
        total_pages=2,
        has_next=False,
        has_previous=True,
    )

    uow = FakeUnitOfWork(expected_page)

    use_case = ListUsers(
        uow=cast(UnitOfWork, uow),
    )

    sort_options = SortOptions(
        field="email",
        descending=True,
    )

    result = use_case.execute(
        page=2,
        page_size=10,
        sort_options=sort_options,
        search="alice",
        role="User",
        is_active=True,
    )

    assert result is expected_page

    assert uow.users.received_args == {
        "page": 2,
        "page_size": 10,
        "sort_options": sort_options,
        "search": "alice",
        "role": "User",
        "is_active": True,
    }
