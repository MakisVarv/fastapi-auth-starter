from typing import cast
from uuid import UUID, uuid4

import pytest

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    EmailAlreadyRegisteredError,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.use_cases.users.update_user import UpdateUser
from app.domain.entities.role import Role
from app.domain.entities.user import User


class FakeUserRepository:
    def __init__(
        self,
        *,
        user: User | None,
        existing_by_email: User | None = None,
    ) -> None:
        self.user = user
        self.existing_by_email = existing_by_email

        self.requested_id: UUID | None = None
        self.requested_email: str | None = None
        self.updated_user: User | None = None

    def get_by_id(self, user_id: UUID) -> User | None:
        self.requested_id = user_id

        if self.user is not None and self.user.id == user_id:
            return self.user

        return None

    def get_by_email(self, email: str) -> User | None:
        self.requested_email = email

        if self.existing_by_email is not None and self.existing_by_email.email == email:
            return self.existing_by_email

        return None

    def update(self, user: User) -> None:
        self.updated_user = user


class FakeUnitOfWork:
    def __init__(
        self,
        *,
        user: User | None,
        existing_by_email: User | None = None,
    ) -> None:
        self.users = FakeUserRepository(
            user=user,
            existing_by_email=existing_by_email,
        )
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass

    def commit(self) -> None:
        self.committed = True


def make_user(
    *,
    role_level: int,
    role_name: str = "User",
    email: str = "user@example.com",
) -> User:
    return User(
        first_name="Before",
        last_name="User",
        email=email,
        phone=None,
        password_hash="hashed-password",
        role=Role(
            name=role_name,
            level=role_level,
        ),
    )


def test_update_user_updates_allowed_fields_and_commits() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
        email="actor@example.com",
    )

    target = make_user(
        role_level=20,
        email="target@example.com",
    )

    uow = FakeUnitOfWork(user=target)

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        updates={
            "first_name": "After",
            "last_name": "Updated",
            "phone": "+30-123456789",
        },
    )

    assert result is target

    assert result.first_name == "After"
    assert result.last_name == "Updated"
    assert result.phone == "+30-123456789"

    assert uow.users.updated_user is target
    assert uow.committed is True


def test_update_user_normalizes_email() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
        email="actor@example.com",
    )

    target = make_user(
        role_level=20,
        email="old@example.com",
    )

    uow = FakeUnitOfWork(user=target)

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        updates={
            "email": "  NEW@EXAMPLE.COM  ",
        },
    )

    assert uow.users.requested_email == "new@example.com"
    assert result.email == "new@example.com"

    assert uow.users.updated_user is target
    assert uow.committed is True


def test_update_user_allows_keeping_same_email() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
        email="actor@example.com",
    )

    target = make_user(
        role_level=20,
        email="target@example.com",
    )

    uow = FakeUnitOfWork(
        user=target,
        existing_by_email=target,
    )

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        updates={
            "email": " TARGET@EXAMPLE.COM ",
            "first_name": "Updated",
        },
    )

    assert result.email == "target@example.com"
    assert result.first_name == "Updated"

    assert uow.users.updated_user is target
    assert uow.committed is True


def test_update_user_rejects_duplicate_email() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
        email="actor@example.com",
    )

    target = make_user(
        role_level=20,
        email="target@example.com",
    )

    existing_user = make_user(
        role_level=20,
        email="existing@example.com",
    )

    uow = FakeUnitOfWork(
        user=target,
        existing_by_email=existing_user,
    )

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        use_case.execute(
            actor=actor,
            user_id=target.id,
            updates={
                "email": "  EXISTING@EXAMPLE.COM ",
            },
        )

    assert target.email == "target@example.com"
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_update_user_rejects_missing_user() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
        email="actor@example.com",
    )

    missing_id = uuid4()

    uow = FakeUnitOfWork(user=None)

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(UserNotFoundError):
        use_case.execute(
            actor=actor,
            user_id=missing_id,
            updates={"first_name": "Changed"},
        )

    assert uow.users.requested_id == missing_id
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_update_user_rejects_actor_who_cannot_manage_user() -> None:
    actor = make_user(
        role_level=50,
        role_name="Manager",
        email="actor@example.com",
    )

    target = make_user(
        role_level=50,
        role_name="Peer",
        email="target@example.com",
    )

    uow = FakeUnitOfWork(user=target)

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    with pytest.raises(AuthorizationError) as exc_info:
        use_case.execute(
            actor=actor,
            user_id=target.id,
            updates={"first_name": "Changed"},
        )

    assert exc_info.value.reason == AuthorizationReason.CANNOT_MANAGE_USER

    assert target.first_name == "Before"
    assert uow.users.updated_user is None
    assert uow.committed is False


def test_update_user_ignores_disallowed_fields() -> None:
    actor = make_user(
        role_level=80,
        role_name="Manager",
        email="actor@example.com",
    )

    target = make_user(
        role_level=20,
        email="target@example.com",
    )

    original_password_hash = target.password_hash
    original_role = target.role

    uow = FakeUnitOfWork(user=target)

    use_case = UpdateUser(
        uow=cast(UnitOfWork, uow),
    )

    result = use_case.execute(
        actor=actor,
        user_id=target.id,
        updates={
            "first_name": "Changed",
            "password_hash": "malicious-hash",
            "role": "Admin",
        },
    )

    assert result.first_name == "Changed"
    assert result.password_hash == original_password_hash
    assert result.role is original_role

    assert uow.users.updated_user is target
    assert uow.committed is True
