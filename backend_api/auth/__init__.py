"""
FedSanitize — Authentication & Authorization Module
====================================================
Self-contained identity layer: admin login, client login, JWT issuance,
role-based permission dependencies, and revocable API tokens.

This package is designed to be dropped into `backend_api/auth/` and wired
into `backend_api/main.py` with a handful of lines — see
`INTEGRATION.md` in this folder for the exact merge steps.

Nothing in here is imported automatically by the rest of the app; it only
takes effect once `main.py` includes `auth_router` and adds the
`require_admin` / `require_client_or_admin` dependencies to the existing
routes.
"""

from .router import router as auth_router  # noqa: F401
from .dependencies import (  # noqa: F401
    get_current_principal,
    require_admin,
    require_client_or_admin,
    require_role,
    Principal,
)

__all__ = [
    "auth_router",
    "get_current_principal",
    "require_admin",
    "require_client_or_admin",
    "require_role",
    "Principal",
]
