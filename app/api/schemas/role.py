from uuid import UUID

from pydantic import BaseModel

from app.api.schemas.permission import PermissionResponse


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    level: int
    permissions: list[PermissionResponse]
