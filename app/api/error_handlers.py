from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.application.errors import EmailAlreadyRegisteredError


def email_already_registered_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    assert isinstance(exc, EmailAlreadyRegisteredError)

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"message": "Email is already registered."},
    )
