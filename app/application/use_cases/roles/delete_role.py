from uuid import UUID

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    DeleteRoleWithUsersError,
    ProtectedRoleDeletionError,
    RoleNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import PROTECTED_ROLE_NAMES, can_manage_role
from app.domain.entities.user import User


class DeleteRole:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, actor: User, role_id: UUID) -> None:
        with self.uow:
            role = self.uow.roles.get_by_id(role_id)
            if role is None:
                raise RoleNotFoundError
            if not can_manage_role(actor=actor, role=role):
                raise AuthorizationError(AuthorizationReason.CANNOT_MANAGE_ROLE)
            role_users = self.uow.users.count_by_role(role_id)
            if role.name in PROTECTED_ROLE_NAMES:
                raise ProtectedRoleDeletionError()
            if role_users > 0:
                raise DeleteRoleWithUsersError()
            self.uow.roles.delete(entity=role)
            self.uow.commit()
