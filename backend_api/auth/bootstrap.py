"""
FedSanitize Auth — Startup Bootstrap
=======================================
Call `bootstrap_auth()` once, early in `backend_api/main.py` (see
INTEGRATION.md). It seeds:

1. A default admin account — username from FEDSANITIZE_ADMIN_USERNAME
   (default "admin"). If FEDSANITIZE_ADMIN_PASSWORD is not set, a random
   password is generated and printed ONCE. Copy it immediately; it is
   never stored or logged anywhere else. Rotate it via
   POST /auth/change-password right after first login.

2. Optional demo edge-client credentials, one per id listed in
   FEDSANITIZE_SEED_CLIENT_IDS (comma-separated, e.g. "C0,C1,...,C9" to
   match FedSanitize's default 10-client simulation roster). Each gets a
   random secret, printed ONCE. In production, provision real clients
   via POST /auth/register-client (admin-only) instead of env seeding.

This function is idempotent-safe to call once; calling it twice will
just overwrite the seeded accounts with new random credentials, which is
almost certainly not what you want — so call it exactly once, at import
time or app startup, not per-request.
"""

from __future__ import annotations

import secrets as _secrets

from .config import settings
from .store import user_store, client_credential_store


def _generate_strong_password() -> str:
    return _secrets.token_urlsafe(18)


def bootstrap_auth() -> None:
    # --- Admin ---
    admin_password = settings.admin_password_env or _generate_strong_password()
    user_store.create_admin(settings.admin_username, admin_password)

    if not settings.admin_password_env:
        print("=" * 72)
        print("FedSanitize Auth: generated a random admin password (shown once).")
        print(f"  username: {settings.admin_username}")
        print(f"  password: {admin_password}")
        print("Set FEDSANITIZE_ADMIN_PASSWORD to pin this across restarts, and")
        print("rotate it via POST /auth/change-password after first login.")
        print("=" * 72)

    # --- Demo / seeded clients ---
    seed_ids = [c.strip() for c in settings.seed_client_ids.split(",") if c.strip()]
    if seed_ids:
        print("=" * 72)
        print("FedSanitize Auth: seeded client credentials (shown once).")
        for client_id in seed_ids:
            secret = _secrets.token_urlsafe(16)
            client_credential_store.register(client_id, secret)
            print(f"  {client_id}: {secret}")
        print("Distribute each secret to its corresponding client and do not")
        print("log this output anywhere persistent.")
        print("=" * 72)
