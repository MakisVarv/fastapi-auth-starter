from sqlalchemy import func, select

from app.application.common.pagination import Page
from app.application.errors import UserNotFoundError
from app.domain.entities.user import User
from app.infrastructure.models.user import UserModel
from app.infrastructure.repositories.base import SqlAlchemyRepository


class SqlAlchemyUserRepository(SqlAlchemyRepository[User, UserModel]):
    model_type = UserModel

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=model.email,
            phone=model.phone,
            role_id=model.role_id,
            password_hash=model.password_hash,
            is_active=model.is_active,
        )

    def list_paginated(
        self,
        *,
        page: int,
        page_size: int,
    ) -> Page[User]:
        statement = self._base_query()
        count_statement = select(func.count()).select_from(UserModel)
        return self._paginate(
            statement=statement,
            count_statement=count_statement,
            page_size=page_size,
            page=page,
        )

    def get_by_email(self, email: str) -> User | None:
        model = self.session.scalar(select(UserModel).where(UserModel.email == email))
        if model is None:
            return None

        return self._to_domain(model)

    def add(self, user: User) -> None:

        model = UserModel(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role_id=user.role_id,
            phone=user.phone,
            password_hash=user.password_hash,
            is_active=user.is_active,
        )

        self.session.add(model)

    def update(self, user: User) -> None:
        model = self.session.scalar(select(UserModel).where(UserModel.id == user.id))
        if model is None:
            raise UserNotFoundError()
        model.first_name = user.first_name
        model.last_name = user.last_name
        model.email = user.email
        model.role_id = user.role_id
        model.phone = user.phone
        model.password_hash = user.password_hash
        model.is_active = user.is_active
