from uuid import UUID

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    PermissionAlreadyInRoleError,
    PermissionNotFoundError,
    RoleNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import can_manage_role
from app.domain.entities.role import Role
from app.domain.entities.user import User


class AssignPermission:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, actor: User, role_id: UUID, permission_id: UUID) -> Role:

        with self.uow:
            role = self.uow.roles.get_by_id(role_id)
            if role is None:
                raise RoleNotFoundError()
            if not can_manage_role(actor=actor, role=role):
                raise AuthorizationError(AuthorizationReason.CANNOT_MANAGE_ROLE)
            permission = self.uow.permissions.get_by_id(permission_id)
            if permission is None:
                raise PermissionNotFoundError()
            if any(existing.id == permission.id for existing in role.permissions):
                raise PermissionAlreadyInRoleError()
            role.permissions.append(permission)
            self.uow.roles.assign_permission(role=role, permission=permission)
            self.uow.commit()
            return role
