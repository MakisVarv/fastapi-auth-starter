from datetime import datetime, timezone
from uuid import UUID

from app.application.errors import InactiveUserError, UserNotFoundError
from app.application.ports.unit_of_work import UnitOfWork


class LogoutAll:

    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self, user_id: UUID):

        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            if not user.is_active:
                raise InactiveUserError()
            self.uow.auth_sessions.revoke_all_for_user(
                user_id=user_id, revoked_at=datetime.now(timezone.utc)
            )
            self.uow.commit()
