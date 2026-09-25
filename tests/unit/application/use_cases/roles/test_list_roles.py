from collections.abc import Sequence
from typing import cast

from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.roles.list_roles import ListRoles
from app.domain.entities.role import Role


class FakeRoleRepository:
    def __init__(self, roles: Sequence[Role]) -> None:
        self.roles = roles
        self.list_called = False

    def list_all(self) -> Sequence[Role]:
        self.list_called = True
        return self.roles


class FakeUnitOfWork:
    def __init__(self, roles: Sequence[Role]) -> None:
        self.roles = FakeRoleRepository(roles)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass


def test_list_roles_returns_repository_roles() -> None:
    roles = [
        Role(name="Admin", level=100),
        Role(name="User", level=10),
    ]

    uow = FakeUnitOfWork(roles)

    use_case = ListRoles(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result is roles
    assert uow.roles.list_called is True


def test_list_roles_returns_empty_sequence() -> None:
    roles: list[Role] = []

    uow = FakeUnitOfWork(roles)

    use_case = ListRoles(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute()

    assert result == []
    assert uow.roles.list_called is True
