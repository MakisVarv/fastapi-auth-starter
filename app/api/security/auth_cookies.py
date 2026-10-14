from fastapi import Response


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
    )

    response.delete_cookie(
        key="csrf_refresh_token",
        path="/",
    )
