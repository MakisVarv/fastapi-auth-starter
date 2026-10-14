from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.errors import PasswordResetTokenNotFoundError
from app.domain.entities.password_reset_token import PasswordResetToken
from app.infrastructure.models import PasswordResetTokenModel


class SqlAlchemyPasswordResetTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, token: PasswordResetToken) -> None:
        model = PasswordResetTokenModel(
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )
        self.session.add(model)

    def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:

        model = self.session.scalar(
            select(PasswordResetTokenModel).where(
                PasswordResetTokenModel.token_hash == token_hash
            )
        )

        if model is None:
            return None

        return PasswordResetToken(
            user_id=model.user_id,
            token_hash=model.token_hash,
            expires_at=model.expires_at,
            used_at=model.used_at,
        )

    def update(self, token: PasswordResetToken) -> None:
        model = self.session.get(PasswordResetTokenModel, token.id)

        if model is None:
            raise PasswordResetTokenNotFoundError()

        model.used_at = token.used_at
