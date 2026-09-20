from uuid import UUID

from app.application.errors import (
    AuthorizationError,
    AuthorizationReason,
    EmailAlreadyRegisteredError,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.authorization import can_manage_user
from app.domain.entities.user import User


class UpdateUser:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(
        self, actor: User, user_id: UUID, updates: dict[str, str | None]
    ) -> User:
        allowed_fields = {"first_name", "last_name", "email", "phone"}
        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            if not can_manage_user(actor=actor, target=user):
                raise AuthorizationError(AuthorizationReason.CANNOT_MANAGE_USER)
            if "email" in updates and updates["email"] is not None:
                normalized_email = updates["email"].strip().lower()
                existing = self.uow.users.get_by_email(normalized_email)
                if existing is not None and existing.id != user.id:
                    raise EmailAlreadyRegisteredError()
                updates["email"] = normalized_email
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(user, field, value)
            self.uow.users.update(user)
            self.uow.commit()
            return user
