from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import email_already_registered_handler
from app.api.routes.auth import router as auth_router
from app.application.errors import EmailAlreadyRegisteredError

app = FastAPI()

app.add_exception_handler(
    EmailAlreadyRegisteredError,
    email_already_registered_handler,
)
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
