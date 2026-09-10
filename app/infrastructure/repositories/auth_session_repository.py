import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.auth_session import AuthSession
from app.infrastructure.models.auth_session import AuthSessionModel


class SqlAlchemyAuthSessionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, session_id: uuid.UUID) -> AuthSession | None:
        model = self.session.scalar(
            select(AuthSessionModel).where(AuthSessionModel.id == session_id)
        )
        if model is None:
            return None
        return AuthSession(
            user_id=model.user_id,
            current_refresh_jti=model.current_refresh_jti,
            expires_at=model.expires_at,
            id=model.id,
            revoked_at=model.revoked_at,
        )

    def add(self, auth_session: AuthSession) -> None:

        model = AuthSessionModel(
            user_id=auth_session.user_id,
            current_refresh_jti=auth_session.current_refresh_jti,
            expires_at=auth_session.expires_at,
            id=auth_session.id,
            revoked_at=auth_session.revoked_at,
        )

        self.session.add(model)
