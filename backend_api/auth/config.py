"""
FedSanitize Auth — Settings
===========================
All secrets and tunables come from environment variables so nothing
sensitive ever lives in source control. Copy `.env.example` to `.env`
and fill it in (or export the vars however your deployment prefers).

If SECRET_KEY is not set, a random one is generated at process start.
That is fine for local development but means every restart invalidates
existing tokens, and it will NOT work correctly with multiple worker
processes (each would mint a different key). Always set SECRET_KEY
explicitly outside of local dev.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    return int(val) if val else default


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AuthSettings:
    # --- JWT ---
    secret_key: str = os.environ.get("FEDSANITIZE_SECRET_KEY") or secrets.token_urlsafe(48)
    jwt_algorithm: str = os.environ.get("FEDSANITIZE_JWT_ALG", "HS256")
    access_token_expire_minutes: int = _env_int("FEDSANITIZE_ACCESS_TOKEN_EXPIRE_MINUTES", 30)
    refresh_token_expire_days: int = _env_int("FEDSANITIZE_REFRESH_TOKEN_EXPIRE_DAYS", 7)
    issuer: str = os.environ.get("FEDSANITIZE_JWT_ISSUER", "fedsanitize-api")

    # --- Default admin bootstrap ---
    # If FEDSANITIZE_ADMIN_PASSWORD is not set, a random password is
    # generated and printed ONCE to stdout at startup. Rotate it via
    # POST /auth/change-password immediately after first login.
    admin_username: str = os.environ.get("FEDSANITIZE_ADMIN_USERNAME", "admin")
    admin_password_env: str | None = os.environ.get("FEDSANITIZE_ADMIN_PASSWORD", "admin123")

    # --- Login rate limiting ---
    login_rate_limit_attempts: int = _env_int("FEDSANITIZE_LOGIN_RATE_LIMIT_ATTEMPTS", 10)
    login_rate_limit_window_seconds: int = _env_int("FEDSANITIZE_LOGIN_RATE_LIMIT_WINDOW_SECONDS", 60)

    # --- Client credential bootstrap ---
    # Comma-separated client ids to seed with credentials at startup,
    # e.g. "C0,C1,C2,...,C9" to match the demo's default 10-client roster.
    seed_client_ids: str = os.environ.get("FEDSANITIZE_SEED_CLIENT_IDS", "C0,C1,C2,C3,C4,C5,C6,C7,C8,C9")

    require_https_in_prod: bool = _env_bool("FEDSANITIZE_REQUIRE_HTTPS", True)
    environment: str = os.environ.get("FEDSANITIZE_ENV", "development")


settings = AuthSettings()
