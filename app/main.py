from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import (
    register_exception_handlers,
)
from app.api.routes.auth import router as auth_router

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
