from uuid import UUID

from app.application.errors import (
    ActiveUserDeletionError,
    AuthorizationError,
    AuthorizationReason,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import can_manage_user
from app.domain.entities.user import User


class DeleteUser:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, actor: User, user_id: UUID) -> None:
        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            if not can_manage_user(actor=actor, target=user):
                raise AuthorizationError(AuthorizationReason.CANNOT_MANAGE_USER)
            if user.is_active:
                raise ActiveUserDeletionError()
            self.uow.users.delete(entity=user)
            self.uow.commit()
