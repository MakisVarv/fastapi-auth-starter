from app.application.use_cases.permissions.sync_permissions import SyncPermissions
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork

if __name__ == "__main__":
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    result = SyncPermissions(uow).execute()

    print(f"Created: {result.created}")
    print(f"Updated: {result.updated}")
    print(f"Unchanged: {result.unchanged}")

    if result.stale:
        raise RuntimeError(f"Stale permissions detected: {', '.join(result.stale)}")
