import pytest
from sqlalchemy.orm import Session

from app.application.errors import RoleNotFoundError
from app.domain.entities.role import Role
from app.infrastructure.repositories.permission_repository import (
    SqlAlchemyPermissionRepository,
)
from app.infrastructure.repositories.role_repository import SqlAlchemyRoleRepository


def test_add_and_get_by_name_persists_role(
    db_session: Session,
) -> None:
    repository = SqlAlchemyRoleRepository(db_session)

    role = Role(
        name="Manager",
        description="Management role",
        level=50,
    )

    repository.add(role)
    db_session.commit()
    db_session.expire_all()

    persisted_role = repository.get_by_name("Manager")

    assert persisted_role is not None
    assert persisted_role.id == role.id
    assert persisted_role.name == "Manager"
    assert persisted_role.description == "Management role"
    assert persisted_role.level == 50
    assert persisted_role.permissions == []


def test_list_all_returns_roles_with_permissions(
    db_session: Session,
) -> None:
    repository = SqlAlchemyRoleRepository(db_session)

    roles = repository.list_all()

    role_names = {role.name for role in roles}

    assert {"Admin", "User"} <= role_names

    admin_role = next(role for role in roles if role.name == "Admin")

    user_role = next(role for role in roles if role.name == "User")

    assert admin_role.permissions
    assert user_role.permissions == []

    admin_permission_names = {permission.name for permission in admin_role.permissions}

    assert "user.read" in admin_permission_names
    assert "role.assign_permission" in admin_permission_names
    assert "permission.read" in admin_permission_names


def test_update_persists_role_changes(
    db_session: Session,
) -> None:
    repository = SqlAlchemyRoleRepository(db_session)

    role = Role(
        name="Supervisor",
        description="Original description",
        level=40,
    )

    repository.add(role)
    db_session.commit()

    role.name = "Senior Supervisor"
    role.description = "Updated description"
    role.level = 60

    repository.update(role)
    db_session.commit()
    db_session.expire_all()

    persisted_role = repository.get_by_name("Senior Supervisor")

    assert persisted_role is not None
    assert persisted_role.id == role.id
    assert persisted_role.name == "Senior Supervisor"
    assert persisted_role.description == "Updated description"
    assert persisted_role.level == 60


def test_update_missing_role_raises_not_found(
    db_session: Session,
) -> None:
    repository = SqlAlchemyRoleRepository(db_session)

    missing_role = Role(
        name="Missing",
        description="Does not exist",
        level=25,
    )

    with pytest.raises(RoleNotFoundError):
        repository.update(missing_role)


def test_delete_persists_role_removal(
    db_session: Session,
) -> None:
    repository = SqlAlchemyRoleRepository(db_session)

    role = Role(
        name="Temporary",
        description="Temporary role",
        level=20,
    )

    repository.add(role)
    db_session.commit()

    assert repository.get_by_name("Temporary") is not None

    repository.delete(role)
    db_session.commit()
    db_session.expire_all()

    assert repository.get_by_name("Temporary") is None


def test_assign_permission_persists_relationship(
    db_session: Session,
) -> None:
    role_repository = SqlAlchemyRoleRepository(db_session)
    permission_repository = SqlAlchemyPermissionRepository(db_session)

    role = role_repository.get_by_name("User")
    assert role is not None

    permission = next(
        (
            permission
            for permission in permission_repository.list_all()
            if permission.name == "user.read"
        ),
        None,
    )
    assert permission is not None

    assert all(
        existing_permission.id != permission.id
        for existing_permission in role.permissions
    )

    role_repository.assign_permission(role, permission)
    db_session.commit()
    db_session.expire_all()

    reloaded_role = role_repository.get_by_name("User")
    assert reloaded_role is not None

    assert any(
        existing_permission.id == permission.id
        for existing_permission in reloaded_role.permissions
    )


def test_remove_permission_persists_relationship(
    db_session: Session,
) -> None:
    role_repository = SqlAlchemyRoleRepository(db_session)
    permission_repository = SqlAlchemyPermissionRepository(db_session)

    role = role_repository.get_by_name("User")
    assert role is not None

    permission = next(
        (
            permission
            for permission in permission_repository.list_all()
            if permission.name == "user.read"
        ),
        None,
    )
    assert permission is not None

    assert all(
        existing_permission.id != permission.id
        for existing_permission in role.permissions
    )

    role_repository.assign_permission(role, permission)
    db_session.commit()
    db_session.expire_all()

    role_with_permission = role_repository.get_by_name("User")
    assert role_with_permission is not None

    assert any(
        existing_permission.id == permission.id
        for existing_permission in role_with_permission.permissions
    )

    role_repository.remove_permission(
        role_with_permission,
        permission,
    )
    db_session.commit()
    db_session.expire_all()

    reloaded_role = role_repository.get_by_name("User")
    assert reloaded_role is not None

    assert all(
        existing_permission.id != permission.id
        for existing_permission in reloaded_role.permissions
    )
