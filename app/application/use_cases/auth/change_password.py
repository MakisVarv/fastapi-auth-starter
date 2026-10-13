from datetime import datetime, timezone
from uuid import UUID

from app.application.errors import InactiveUserError, UserNotFoundError
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork


class ChangePassword:

    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
    ) -> None:
        self.uow = uow
        self.password_hasher = password_hasher

    def execute(self, user_id: UUID, new_password: str) -> None:
        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            if not user.is_active:
                raise InactiveUserError()
            password_hash = self.password_hasher.hash(new_password)
            user.password_hash = password_hash
            self.uow.users.update(user)
            self.uow.auth_sessions.revoke_all_for_user(
                user_id=user_id, revoked_at=datetime.now(timezone.utc)
            )
            self.uow.commit()
