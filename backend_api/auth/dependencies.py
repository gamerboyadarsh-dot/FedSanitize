"""
FedSanitize Auth — FastAPI Dependencies
=========================================
Drop these into route signatures to require authentication/authorization:

    from backend_api.auth import require_admin, require_client_or_admin

    @app.post("/config")
    def update_config(update_req: ConfigUpdateRequest, _: Principal = Depends(require_admin)):
        ...

    @app.get("/clients")
    def list_clients(_: Principal = Depends(require_client_or_admin)):
        ...

Two credential types are accepted on every protected route, tried in
this order:

1. `Authorization: Bearer <JWT access token>` — issued by /auth/login or
   /auth/client-login, short-lived.
2. `X-API-Key: <opaque token>` — issued by an admin via POST
   /auth/api-tokens, long-lived and independently revocable. Intended
   for edge clients / automation that shouldn't have to re-login.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer

from .security import TokenError, decode_token
from .store import api_token_store

# `tokenUrl` only affects the Swagger "Authorize" button; the real
# validation happens in `get_current_principal` below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class Principal:
    subject: str
    role: Literal["admin", "client"]
    client_id: Optional[str] = None
    auth_method: Literal["jwt", "api_token"] = "jwt"


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_principal(
    request: Request,
    bearer_token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Depends(api_key_scheme),
) -> Principal:
    """Resolves whoever is calling, from either a JWT bearer token or an X-API-Key header."""

    if api_key:
        record = api_token_store.resolve(api_key)
        if record is None:
            raise _unauthorized("API key is invalid, expired, or has been revoked")
        return Principal(
            subject=record.name,
            role=record.role,  # type: ignore[arg-type]
            client_id=record.client_id,
            auth_method="api_token",
        )

    if bearer_token:
        try:
            payload = decode_token(bearer_token, expected_type="access")
        except TokenError as exc:
            raise _unauthorized(str(exc)) from exc
        return Principal(
            subject=payload["sub"],
            role=payload["role"],
            client_id=payload.get("client_id"),
            auth_method="jwt",
        )

    raise _unauthorized("Not authenticated — provide a Bearer token or X-API-Key header")


def require_role(*allowed_roles: str):
    """Dependency factory: `Depends(require_role("admin"))`, `Depends(require_role("admin", "client"))`."""

    def _dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of roles {list(allowed_roles)}, "
                       f"but caller has role '{principal.role}'",
            )
        return principal

    return _dependency


# Ready-made dependencies for the two roles this project uses today.
require_admin = require_role("admin")
require_client_or_admin = require_role("admin", "client")


def require_own_client_or_admin(path_client_id: str):
    """
    Dependency factory for routes scoped to one client, e.g.
    POST /clients/{client_id}/attack — an admin may act on any client,
    but a client-role principal may only act on itself.
    """

    def _dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.role == "admin":
            return principal
        if principal.role == "client" and principal.client_id == path_client_id:
            return principal
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clients may only act on their own client_id",
        )

    return _dependency
