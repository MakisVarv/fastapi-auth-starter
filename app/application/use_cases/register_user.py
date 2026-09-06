from app.application.errors import EmailAlreadyRegisteredError
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.user import User


class RegisterUser:
    def __init__(
        self,
        uow: UnitOfWork,
        password_hasher: PasswordHasher,
    ) -> None:
        self.uow = uow
        self.password_hasher = password_hasher

    def execute(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
    ) -> User:
        with self.uow:
            existing_user = self.uow.users.get_by_email(email)

            if existing_user is not None:
                raise EmailAlreadyRegisteredError

            password_hash = self.password_hasher.hash(password)

            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
            )

            self.uow.users.add(user)

            self.uow.commit()

            return user
