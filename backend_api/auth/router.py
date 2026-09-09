"""
FedSanitize Auth — Router
============================
Mount with `app.include_router(auth_router)` in `backend_api/main.py`.
See INTEGRATION.md for the exact merge steps.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from .dependencies import Principal, get_current_principal, require_admin
from .models import (
    ApiTokenCreated,
    ApiTokenCreateRequest,
    ApiTokenSummary,
    ChangePasswordRequest,
    ClientLoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterClientRequest,
    Token,
)
from .rate_limit import login_rate_limiter
from .security import TokenError, create_access_token, create_token_pair, decode_token
from .store import api_token_store, client_credential_store, user_store

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    # Respect a reverse proxy's forwarded header if present; fall back to
    # the direct connection. Trust this only if your proxy sanitizes it.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Admin login  (OAuth2 "password" flow — also powers the Swagger "Authorize" button)
# ---------------------------------------------------------------------------

@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    ip = _client_ip(request)
    login_rate_limiter.check(ip, form_data.username)

    if not user_store.verify_admin_password(form_data.username, form_data.password):
        login_rate_limiter.record_failure(ip, form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_rate_limiter.record_success(ip, form_data.username)
    pair = create_token_pair(subject=form_data.username, role="admin")
    return Token(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
        role="admin",
    )


# ---------------------------------------------------------------------------
# Client login  (client_id + shared secret -> JWT with role="client")
# ---------------------------------------------------------------------------

@router.post("/client-login", response_model=Token)
def client_login(request: Request, body: ClientLoginRequest):
    ip = _client_ip(request)
    login_rate_limiter.check(ip, body.client_id)

    if not client_credential_store.verify(body.client_id, body.client_secret):
        login_rate_limiter.record_failure(ip, body.client_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect client_id or client_secret",
        )

    login_rate_limiter.record_success(ip, body.client_id)
    pair = create_token_pair(subject=body.client_id, role="client", client_id=body.client_id)
    return Token(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=pair.expires_in,
        role="client",
        client_id=body.client_id,
    )


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest):
    try:
        payload = decode_token(body.refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    new_access = create_access_token(
        subject=payload["sub"], role=payload["role"], client_id=payload.get("client_id")
    )
    from .config import settings  # local import avoids a module-level cycle risk

    return Token(
        access_token=new_access,
        refresh_token=body.refresh_token,  # unchanged; rotate here if you want single-use refresh tokens
        expires_in=settings.access_token_expire_minutes * 60,
        role=payload["role"],
        client_id=payload.get("client_id"),
    )


# ---------------------------------------------------------------------------
# Whoami
# ---------------------------------------------------------------------------

@router.get("/me", response_model=MeResponse)
def me(principal: Principal = Depends(get_current_principal)):
    return MeResponse(
        subject=principal.subject,
        role=principal.role,
        client_id=principal.client_id,
        auth_method=principal.auth_method,
    )


# ---------------------------------------------------------------------------
# Admin: change own password
# ---------------------------------------------------------------------------

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(body: ChangePasswordRequest, principal: Principal = Depends(require_admin)):
    if not user_store.verify_admin_password(principal.subject, body.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect"
        )
    user_store.set_admin_password(principal.subject, body.new_password)


# ---------------------------------------------------------------------------
# Admin: provision a new edge-client credential
# ---------------------------------------------------------------------------

@router.post("/register-client", status_code=status.HTTP_201_CREATED)
def register_client(body: RegisterClientRequest, _: Principal = Depends(require_admin)):
    if client_credential_store.exists(body.client_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Client '{body.client_id}' is already registered",
        )
    client_credential_store.register(body.client_id, body.client_secret)
    return {"status": "success", "client_id": body.client_id}


# ---------------------------------------------------------------------------
# Admin: API token lifecycle
# ---------------------------------------------------------------------------

@router.post("/api-tokens", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED)
def create_api_token(body: ApiTokenCreateRequest, _: Principal = Depends(require_admin)):
    if body.role == "client" and not body.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="client_id is required when role='client'",
        )
    record, raw_token = api_token_store.create(
        name=body.name,
        role=body.role,
        client_id=body.client_id,
        expires_in_days=body.expires_in_days,
    )
    return ApiTokenCreated(
        id=record.id,
        token=raw_token,
        name=record.name,
        role=record.role,  # type: ignore[arg-type]
        client_id=record.client_id,
        created_at=record.created_at,
        expires_at=record.expires_at,
    )


@router.get("/api-tokens", response_model=list[ApiTokenSummary])
def list_api_tokens(_: Principal = Depends(require_admin)):
    return [
        ApiTokenSummary(
            id=t.id,
            name=t.name,
            role=t.role,  # type: ignore[arg-type]
            client_id=t.client_id,
            created_at=t.created_at,
            expires_at=t.expires_at,
            revoked=t.revoked,
        )
        for t in api_token_store.list_all()
    ]


@router.delete("/api-tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_token(token_id: str, _: Principal = Depends(require_admin)):
    if not api_token_store.revoke(token_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
