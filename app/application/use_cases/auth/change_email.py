from datetime import datetime, timezone
from uuid import UUID

from app.application.errors import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    UserNotFoundError,
)
from app.application.ports.unit_of_work import UnitOfWork


class ChangeEmail:

    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

    def execute(self, user_id: UUID, new_email: str) -> None:
        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            if not user.is_active:
                raise InactiveUserError()
            exists = self.uow.users.get_by_email(email=new_email)
            if exists and exists.id != user.id:
                raise EmailAlreadyRegisteredError()
            if new_email == user.email:
                return
            self.uow.auth_sessions.revoke_all_for_user(
                user_id=user_id, revoked_at=datetime.now(timezone.utc)
            )
            user.email = new_email
            self.uow.users.update(user)
            self.uow.commit()
