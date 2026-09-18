from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.api.schemas.permission import PermissionResponse


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: str | None = None
    level: int
    permissions: list[PermissionResponse]
