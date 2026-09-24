from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_permission
from app.api.dependencies.permissions import (
    get_list_permissions,
    get_permission_use_case,
)
from app.api.schemas.permission import PermissionResponse
from app.application.use_cases.permissions.get_permission import GetPermission
from app.application.use_cases.permissions.list_permissions import ListPermissions

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get(
    "",
    response_model=list[PermissionResponse],
    dependencies=[Depends(require_permission("permission.read"))],
)
def list_permissions(
    use_case: ListPermissions = Depends(get_list_permissions),
) -> list[PermissionResponse]:
    permissions = use_case.execute()

    return [PermissionResponse.model_validate(permission) for permission in permissions]


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    dependencies=[Depends(require_permission("permission.read"))],
)
def get_permission(
    permission_id: UUID, use_case: GetPermission = Depends(get_permission_use_case)
) -> PermissionResponse:
    permission = use_case.execute(permission_id)
    return PermissionResponse.model_validate(permission)
