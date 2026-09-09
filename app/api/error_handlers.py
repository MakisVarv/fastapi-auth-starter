from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.errors import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
)

ERROR_RESPONSES = {
    EmailAlreadyRegisteredError: (
        status.HTTP_409_CONFLICT,
        "Email is already registered.",
    ),
    InvalidCredentialsError: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid credentials.",
    ),
    InactiveUserError: (
        status.HTTP_403_FORBIDDEN,
        "Account is inactive.",
    ),
}


def application_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    status_code, message = ERROR_RESPONSES[type(exc)]

    return JSONResponse(
        status_code=status_code,
        content={"message": message},
    )


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type in ERROR_RESPONSES:
        app.add_exception_handler(
            exception_type,
            application_error_handler,
        )
