from typing import Protocol
from uuid import UUID


class TokenService(Protocol):
    def create_access_token(self, user_id: UUID) -> str: ...
