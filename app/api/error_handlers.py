from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.application.errors import (
    ActiveUserDeletionError,
    AuthorizationError,
    AuthorizationReason,
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidAccessTokenError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    PermissionDeniedError,
    RefreshTokenReplayError,
    RegistrationRoleNotFoundError,
    RoleNotFoundError,
    UserNotFoundError,
)

ERROR_RESPONSES = {
    UserNotFoundError: (status.HTTP_404_NOT_FOUND, "User not found!"),
    RegistrationRoleNotFoundError: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "Default registration role is not configured.",
    ),
    ActiveUserDeletionError: (
        status.HTTP_409_CONFLICT,
        "Active users must be deactivated before they can be deleted.",
    ),
    RoleNotFoundError: (status.HTTP_404_NOT_FOUND, "Role not found!"),
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
    PermissionDeniedError: (
        status.HTTP_403_FORBIDDEN,
        "Permission denied.",
    ),
}

AUTHORIZATION_MESSAGES = {
    AuthorizationReason.CANNOT_ASSIGN_ROLE: "You are not authorized to assign this role.",
    AuthorizationReason.CANNOT_MANAGE_USER: "You are not authorized to manage this user.",
}


def authorization_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, AuthorizationError):
        raise exc

    message = AUTHORIZATION_MESSAGES[exc.reason]

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"message": message},
    )


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
    app.add_exception_handler(
        AuthorizationError,
        authorization_error_handler,
    )
