from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.errors import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshTokenReplayError,
    UserNotFoundError,
)

ERROR_RESPONSES = {
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "User not found!"),
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
    InvalidRefreshTokenError: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid refresh token.",
    ),
    InvalidAccessTokenError: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid access token.",
    ),
    RefreshTokenReplayError: (
        status.HTTP_401_UNAUTHORIZED,
        "Invalid refresh token.",
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


def request_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc

    errors = []

    for error in exc.errors():
        loc = error["loc"]
        message = error["msg"]
        location_parts = loc[1:]
        field = (
            ".".join(str(part) for part in location_parts) if location_parts else None
        )
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        errors.append(
            {
                "field": field,
                "message": message,
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )


def register_exception_handlers(app: FastAPI) -> None:
    for exception_type in ERROR_RESPONSES:
        app.add_exception_handler(
            exception_type,
            application_error_handler,
        )
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,
    )
