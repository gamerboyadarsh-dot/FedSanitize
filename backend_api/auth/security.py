"""
FedSanitize Auth — Cryptographic Helpers
=========================================
- Password hashing: PBKDF2-HMAC-SHA256 (stdlib `hashlib`, no extra native
  dependency). Swap for passlib[bcrypt]/argon2 if you prefer — the
  `hash_password` / `verify_password` interface is the only thing callers
  depend on, so the implementation can change without touching the rest
  of the module.
- JWT: PyJWT, HS256, short-lived access tokens + longer-lived refresh
  tokens, both carrying `sub` (subject id), `role`, and (for clients)
  `client_id`.
- API tokens: high-entropy opaque secrets (`secrets.token_urlsafe`).
  Only a SHA-256 hash of the token is ever stored, so a leaked database
  dump does not expose usable credentials.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Literal

import jwt  # PyJWT

from .config import settings

# ---------------------------------------------------------------------------
# Password hashing (PBKDF2-HMAC-SHA256)
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 260_000
_SALT_BYTES = 16


def hash_password(plain_password: str) -> str:
    """Returns a self-describing hash string: pbkdf2_sha256$iterations$salt$hash (all base64/int)."""
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        _PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations_s, salt_b64, hash_b64 = stored_hash.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_s)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate, expected)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

Role = Literal["admin", "client"]


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0


def _base_claims(subject: str, role: Role, client_id: str | None) -> dict[str, Any]:
    claims: dict[str, Any] = {"sub": subject, "role": role, "iss": settings.issuer}
    if client_id is not None:
        claims["client_id"] = client_id
    return claims


def create_access_token(subject: str, role: Role, client_id: str | None = None) -> str:
    now = int(time.time())
    claims = _base_claims(subject, role, client_id)
    claims.update(
        {
            "type": "access",
            "iat": now,
            "exp": now + settings.access_token_expire_minutes * 60,
        }
    )
    return jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str, role: Role, client_id: str | None = None) -> str:
    now = int(time.time())
    claims = _base_claims(subject, role, client_id)
    claims.update(
        {
            "type": "refresh",
            "iat": now,
            "exp": now + settings.refresh_token_expire_days * 24 * 60 * 60,
        }
    )
    return jwt.encode(claims, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_token_pair(subject: str, role: Role, client_id: str | None = None) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(subject, role, client_id),
        refresh_token=create_refresh_token(subject, role, client_id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


class TokenError(Exception):
    """Raised for any invalid/expired/malformed JWT. Callers map this to HTTP 401."""


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "iat", "sub", "role"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Token is invalid") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")

    return payload


# ---------------------------------------------------------------------------
# Opaque API tokens (for machine-to-machine / long-lived client credentials)
# ---------------------------------------------------------------------------

API_TOKEN_PREFIX = "fdsz_"  # helps identify leaked tokens in logs/scans


def generate_api_token() -> str:
    return API_TOKEN_PREFIX + secrets.token_urlsafe(32)


def hash_api_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
