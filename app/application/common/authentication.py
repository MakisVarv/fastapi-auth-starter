from datetime import datetime, timedelta

FRESH_AUTH_MAX_AGE = timedelta(minutes=10)


def is_authentication_fresh(
    authenticated_at: datetime,
    now: datetime,
    max_age: timedelta = FRESH_AUTH_MAX_AGE,
) -> bool:
    age = now - authenticated_at
    return timedelta(0) <= age < max_age
