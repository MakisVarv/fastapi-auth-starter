import hashlib
from datetime import datetime, timezone

from app.application.errors import InvalidPasswordResetTokenError
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork


class ResetPassword:
    def __init__(self, uow: UnitOfWork, password_hasher: PasswordHasher) -> None:
        self.uow = uow
        self.password_hasher = password_hasher

    def execute(self, raw_token: str, new_password: str) -> None:

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        with self.uow:
            token = self.uow.password_reset_tokens.get_by_token_hash(
                token_hash=token_hash
            )
            if token is None:
                raise InvalidPasswordResetTokenError()
            if token.used_at is not None:
                raise InvalidPasswordResetTokenError()
            if token.expires_at <= now:
                raise InvalidPasswordResetTokenError()
            user = self.uow.users.get_by_id(token.user_id)
            if user is None or not user.is_active:
                raise InvalidPasswordResetTokenError()
            password_hash = self.password_hasher.hash(new_password)
            user.password_hash = password_hash
            self.uow.users.update(user)
            self.uow.auth_sessions.revoke_all_for_user(
                user_id=token.user_id, revoked_at=now
            )
            token.used_at = now
            self.uow.password_reset_tokens.update(token)
            self.uow.commit()
