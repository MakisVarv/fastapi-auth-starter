from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    ProtectedRoleModificationError,
    RoleAlreadyExist,
    RoleNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.roles.update_role import UpdateRole
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeRoleRepository:
    def __init__(
        self,
        *,
        role: Role | None,
        existing_by_name: Role | None = None,
    ) -> None:
        self.role = role
        self.existing_by_name = existing_by_name
        self.requested_id: UUID | None = None
        self.requested_name: str | None = None
        self.updated_role: Role | None = None

    def get_by_id(self, role_id: UUID) -> Role | None:
        self.requested_id = role_id

        if self.role is not None and self.role.id == role_id:
            return self.role

        return None

    def get_by_name(self, name: str) -> Role | None:
        self.requested_name = name

        if self.existing_by_name is not None and self.existing_by_name.name == name:
            return self.existing_by_name

        return None

    def update(self, role: Role) -> None:
        self.updated_role = role


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        role: Role | None,
        existing_by_name: Role | None = None,
    ) -> None:
        self.roles = FakeRoleRepository(
            role=role,
            existing_by_name=existing_by_name,
        )
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


def make_actor(level: int = 80) -> User:
    return User(
        first_name="Actor",
        last_name="User",
        email="actor@example.com",
        password_hash="hash",
        role=Role(name="Manager", level=level),
    )


def test_update_role_updates_fields_and_commits() -> None:
    actor = make_actor()

    role = Role(
        name="Support",
        description="Old description",
        level=40,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        role_id=role.id,
        updates={
            "name": "Senior Support",
            "description": "Updated description",
            "level": 60,
        },
    )

    assert result is role
    assert result.name == "Senior Support"
    assert result.description == "Updated description"
    assert result.level == 60

    assert uow.roles.requested_name == "Senior Support"
    assert uow.roles.updated_role is role
    assert uow.committed is True


def test_update_role_rejects_missing_role() -> None:
    actor = make_actor()
    missing_id = uuid4()

    uow = FakeUnitOfWork(role=None)

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(RoleNotFoundError):
        use_case.execute(
            actor=actor,
            role_id=missing_id,
            updates={"description": "Updated"},
        )

    assert uow.roles.updated_role is None
    assert uow.committed is False


def test_update_role_rejects_actor_who_cannot_manage_role() -> None:
    actor = make_actor(level=50)

    role = Role(
        name="Support",
        level=50,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            role_id=role.id,
            updates={"description": "Updated"},
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_ROLE
    assert uow.roles.updated_role is None
    assert uow.committed is False


@pytest.mark.parametrize(
    "updates",
    [
        {"name": "Super Admin"},
        {"level": 90},
    ],
)
def test_update_role_rejects_protected_role_name_or_level_changes(
    updates,
) -> None:
    actor = make_actor(level=100)

    role = Role(
        name="Admin",
        description="Administrator",
        level=100,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(ProtectedRoleModificationError):
        use_case.execute(
            actor=actor,
            role_id=role.id,
            updates=updates,
        )

    assert uow.roles.updated_role is None
    assert uow.committed is False


def test_update_role_allows_protected_role_description_change() -> None:
    actor = make_actor(level=100)

    role = Role(
        name="Admin",
        description="Old description",
        level=100,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        role_id=role.id,
        updates={"description": "Updated administrator role"},
    )

    assert result.description == "Updated administrator role"
    assert result.name == "Admin"
    assert result.level == 100

    assert uow.roles.updated_role is role
    assert uow.committed is True


def test_update_role_rejects_level_actor_cannot_set() -> None:
    actor = make_actor(level=80)

    role = Role(
        name="Support",
        level=40,
    )

    uow = FakeUnitOfWork(role=role)

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            role_id=role.id,
            updates={"level": 80},
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_SET_ROLE_LEVEL
    assert role.level == 40
    assert uow.roles.updated_role is None
    assert uow.committed is False


def test_update_role_rejects_duplicate_name() -> None:
    actor = make_actor()

    role = Role(
        name="Support",
        level=40,
    )

    existing = Role(
        name="Manager",
        level=50,
    )

    uow = FakeUnitOfWork(
        role=role,
        existing_by_name=existing,
    )

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(RoleAlreadyExist):
        use_case.execute(
            actor=actor,
            role_id=role.id,
            updates={"name": "Manager"},
        )

    assert role.name == "Support"
    assert uow.roles.updated_role is None
    assert uow.committed is False


def test_update_role_allows_keeping_same_name() -> None:
    actor = make_actor()

    role = Role(
        name="Support",
        description="Old description",
        level=40,
    )

    uow = FakeUnitOfWork(
        role=role,
        existing_by_name=role,
    )

    use_case = UpdateRole(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        role_id=role.id,
        updates={
            "name": "Support",
            "description": "New description",
        },
    )

    assert result.name == "Support"
    assert result.description == "New description"

    assert uow.roles.updated_role is role
    assert uow.committed is True
