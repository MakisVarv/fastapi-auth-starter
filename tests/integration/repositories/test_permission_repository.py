from sqlalchemy.orm import Session

from app.domain.entities.permission import Permission
from app.infrastructure.repositories.permission_repository import (
    SqlAlchemyPermissionRepository,
)


def test_list_all_returns_seeded_permissions_as_domain_entities(
    db_session: Session,
) -> None:
    repository = SqlAlchemyPermissionRepository(db_session)

    permissions = repository.list_all()

    assert permissions

    assert all(isinstance(permission, Permission) for permission in permissions)

    permission_names = {permission.name for permission in permissions}

    assert {
        "user.read",
        "user.create",
        "user.update",
        "user.delete",
        "user.change_role",
        "role.read",
        "role.create",
        "role.update",
        "role.delete",
        "role.assign_permission",
        "permission.read",
        "dashboard.read",
    } <= permission_names


def test_get_by_id_returns_mapped_permission(
    db_session: Session,
) -> None:
    repository = SqlAlchemyPermissionRepository(db_session)

    permissions = repository.list_all()

    target = next(
        permission for permission in permissions if permission.name == "user.read"
    )

    reloaded_permission = repository.get_by_id(target.id)

    assert reloaded_permission is not None
    assert reloaded_permission.id == target.id
    assert reloaded_permission.name == "user.read"
    assert reloaded_permission.description == target.description
