import uvicorn

from app.application.use_cases.permissions.sync_permissions import SyncPermissions
from app.infrastructure.database.session import SessionFactory
from app.infrastructure.uow.sqlalchemy import SqlAlchemyUnitOfWork

if __name__ == "__main__":
    uow = SqlAlchemyUnitOfWork(SessionFactory)
    result = SyncPermissions(uow).execute()

    if result.stale:
        raise RuntimeError(f"Stale permissions detected: {', '.join(result.stale)}")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
