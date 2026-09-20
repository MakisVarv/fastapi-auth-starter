from enum import Enum


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


class InvalidAccessTokenError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class AuthSessionNotFoundError(Exception):
    pass


class RefreshTokenReplayError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class RegistrationRoleNotFoundError(Exception):
    pass


class RoleNotFoundError(Exception):
    pass


class PermissionDeniedError(Exception):
    pass


class AuthorizationReason(str, Enum):
    CANNOT_ASSIGN_ROLE = "cannot_assign_role"
    CANNOT_MANAGE_USER = "cannot_manage_user"


class AuthorizationError(Exception):
    def __init__(self, reason: AuthorizationReason) -> None:
        self.reason = reason
        super().__init__(reason.value)
