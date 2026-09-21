from uuid import UUID

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    RoleNotFoundError,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import can_assign_role, can_manage_user
from app.domain.entities.user import User


class ChangeUserRole:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, actor: User, user_id: UUID, role_id: UUID) -> User:
        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            if not can_manage_user(actor=actor, target=user):
                raise AuthorizationError(AuthorizationReason.CANNOT_MANAGE_USER)
            role = self.uow.roles.get_by_id(role_id)
            if role is None:
                raise RoleNotFoundError()
            if not can_assign_role(actor=actor, role=role):
                raise AuthorizationError(AuthorizationReason.CANNOT_ASSIGN_ROLE)
            user.role = role
            self.uow.users.update(user)
            self.uow.commit()
            return user
