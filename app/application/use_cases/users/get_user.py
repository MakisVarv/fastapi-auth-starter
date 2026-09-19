from uuid import UUID

from app.application.errors import UserNotFoundError
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User


class GetUser:
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        self.uow = uow

    def execute(self, user_id: UUID) -> User:

        with self.uow:
            user = self.uow.users.get_by_id(user_id)
            if user is None:
                raise UserNotFoundError()
            return user
