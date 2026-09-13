from uuid import UUID

from app.application.errors import UserNotFoundError
from app.application.ports.unit_of_work import UnitOfWork


class UpdateCurrentUser:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow


def execute(self, user_id: UUID, updates: dict[str, str | None]) -> User:
    allowed_fields = {"first_name", "last_name", "phone"}
    with self.uow:
        user = self.uow.users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(user, field, value)
        self.uow.users.update(user)
        self.uow.commit()
