from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.application.errors import PasswordResetTokenNotFoundError
from app.domain.entities.password_reset_token import PasswordResetToken
from app.infrastructure.models import PasswordResetTokenModel


class SqlAlchemyPasswordResetTokenRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, token: PasswordResetToken) -> None:
        model = PasswordResetTokenModel(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            expires_at=token.expires_at,
            used_at=token.used_at,
        )
        self.session.add(model)

    def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:

        model = self.session.scalar(
            select(PasswordResetTokenModel)
            .where(PasswordResetTokenModel.token_hash == token_hash)
            .with_for_update()
        )

        if model is None:
            return None

        return PasswordResetToken(
            id=model.id,
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

    def delete_unused_for_user(self, user_id: UUID) -> None:
        stmt = delete(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user_id,
            PasswordResetTokenModel.used_at.is_(None),
        )
        self.session.execute(stmt)
