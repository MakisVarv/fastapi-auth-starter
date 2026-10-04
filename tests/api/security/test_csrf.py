import pytest

from app.api.security.csrf import generate_csrf_token, verify_csrf_token


def test_generated_csrf_token_verifies_against_same_refresh_token() -> None:
    refresh_token = "refresh-token-a"

    csrf_token = generate_csrf_token(refresh_token)

    assert verify_csrf_token(
        refresh_token=refresh_token,
        csrf_token=csrf_token,
    )


def test_csrf_token_is_bound_to_refresh_token() -> None:
    csrf_token = generate_csrf_token("refresh-token-a")

    assert not verify_csrf_token(
        refresh_token="refresh-token-b",
        csrf_token=csrf_token,
    )


def test_tampered_csrf_signature_is_rejected() -> None:
    refresh_token = "refresh-token-a"
    csrf_token = generate_csrf_token(refresh_token)

    nonce, signature = csrf_token.rsplit(".", 1)

    tampered_signature = ("0" if signature[0] != "0" else "1") + signature[1:]

    tampered_token = f"{nonce}.{tampered_signature}"

    assert not verify_csrf_token(
        refresh_token=refresh_token,
        csrf_token=tampered_token,
    )


def test_tampered_csrf_nonce_is_rejected() -> None:
    refresh_token = "refresh-token-a"
    csrf_token = generate_csrf_token(refresh_token)

    nonce, signature = csrf_token.rsplit(".", 1)

    tampered_token = f"{nonce}tampered.{signature}"

    assert not verify_csrf_token(
        refresh_token=refresh_token,
        csrf_token=tampered_token,
    )


@pytest.mark.parametrize(
    "csrf_token",
    [
        "",
        "garbage",
        ".",
        "nonce.",
        ".signature",
    ],
)
def test_malformed_csrf_token_is_rejected(
    csrf_token: str,
) -> None:
    assert not verify_csrf_token(
        refresh_token="refresh-token-a",
        csrf_token=csrf_token,
    )
