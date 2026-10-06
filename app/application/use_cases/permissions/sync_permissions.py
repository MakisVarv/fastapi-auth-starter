from dataclasses import dataclass

from app.application.common.permissions import PERMISSIONS
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities.permission import Permission


@dataclass
class PermissionSyncResult:
    created: list[str]
    updated: list[str]
    unchanged: list[str]
    stale: list[str]


class SyncPermissions:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def execute(self) -> PermissionSyncResult:
        with self.uow:
            configured_by_name = {
                permission["name"]: permission for permission in PERMISSIONS
            }

            persisted_permissions = self.uow.permissions.list_all()

            persisted_by_name = {
                permission.name: permission for permission in persisted_permissions
            }
            missing = [
                name for name in configured_by_name if name not in persisted_by_name
            ]
            stale = [
                name for name in persisted_by_name if name not in configured_by_name
            ]
            changed = [
                name
                for name in configured_by_name
                if name in persisted_by_name
                and configured_by_name[name]["description"]
                != persisted_by_name[name].description
            ]

            unchanged = [
                name
                for name in configured_by_name
                if name in persisted_by_name
                and configured_by_name[name]["description"]
                == persisted_by_name[name].description
            ]

            for name in missing:
                configured = configured_by_name[name]

                permission = Permission(
                    name=name,
                    description=configured["description"],
                )
                persisted_by_name[name] = permission

                self.uow.permissions.add(permission)
            for name in changed:
                permission = persisted_by_name[name]
                permission.description = configured_by_name[name]["description"]

                self.uow.permissions.update(permission)
            admin_role = self.uow.roles.get_by_name("Admin")
            if admin_role is None:
                raise RuntimeError("Admin role does not exist!")
            admin_permission_names = {
                permission.name for permission in admin_role.permissions
            }
            for name in configured_by_name:
                if name in admin_permission_names:
                    continue

                permission = persisted_by_name[name]

                admin_role.permissions.append(permission)
                self.uow.roles.assign_permission(
                    role=admin_role,
                    permission=permission,
                )
            self.uow.commit()
            return PermissionSyncResult(
                created=missing,
                updated=changed,
                unchanged=unchanged,
                stale=stale,
            )
