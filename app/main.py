from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import (
    register_exception_handlers,
)
from app.api.routes.auth import router as auth_router
from app.api.routes.permissions import router as permission_router
from app.api.routes.roles import router as role_router
from app.api.routes.users import router as user_router

app = FastAPI()
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(role_router, prefix="/api")
app.include_router(permission_router, prefix="/api")
