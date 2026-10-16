import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.application.ports.password_reset_mailer import PasswordResetMailer
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.password_reset_token import PasswordResetToken


class RequestPasswordReset:

    def __init__(
        self, uow: UnitOfWork, password_reset_mailer: PasswordResetMailer
    ) -> None:
        self.uow = uow
        self.password_reset_mailer = password_reset_mailer

    def execute(self, email: str):
        with self.uow:
            user = self.uow.users.get_by_email(email=email)
            if user is None or not user.is_active:
                return
            self.uow.password_reset_tokens.delete_unused_for_user(user_id=user.id)
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=30)
            token = PasswordResetToken(
                expires_at=expires_at, token_hash=token_hash, user_id=user.id
            )
            self.uow.password_reset_tokens.add(token=token)
            self.uow.commit()
        self.password_reset_mailer.send_password_reset(email=email, raw_token=raw_token)
