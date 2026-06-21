from __future__ import annotations

from app.application.security import TokenService


def test_password_hashing_roundtrip():
    token_service = TokenService()
    hashed = token_service.hash_password("verystrongpassword")
    assert token_service.verify_password("verystrongpassword", hashed)
    assert not token_service.verify_password("wrong-password", hashed)
