from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.infrastructure.models.user import UserModel


class SqlAlchemyUserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email))
        if model is None:
            return None

        return User(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            password_hash=model.password_hash,
            is_active=model.is_active,
        )

    def add(self, user: User) -> None:

        model = UserModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )

        self.session.add(model)
