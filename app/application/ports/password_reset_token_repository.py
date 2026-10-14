from typing import Protocol

from app.domain.entities.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository(Protocol):
    def add(self, token: PasswordResetToken) -> None: ...

    def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None: ...

    def update(self, token: PasswordResetToken) -> None: ...
