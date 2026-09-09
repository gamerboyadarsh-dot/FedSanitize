"""
FedSanitize Auth — Request / Response Schemas
==============================================
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: Literal["admin", "client"]
    client_id: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class ClientLoginRequest(BaseModel):
    client_id: str = Field(..., description="Edge client identifier, e.g. 'C0'")
    client_secret: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class MeResponse(BaseModel):
    subject: str
    role: Literal["admin", "client"]
    client_id: Optional[str] = None
    auth_method: Literal["jwt", "api_token"]


class ApiTokenCreateRequest(BaseModel):
    name: str = Field(..., description="Human-readable label, e.g. 'C3 edge device'")
    role: Literal["admin", "client"] = "client"
    client_id: Optional[str] = Field(
        None, description="Required when role='client'; ties the token to one edge client"
    )
    expires_in_days: Optional[int] = Field(
        None, description="Omit for a non-expiring token (rotate/revoke manually instead)"
    )


class ApiTokenCreated(BaseModel):
    id: str
    token: str = Field(..., description="Shown only once — store it now, it cannot be retrieved again")
    name: str
    role: Literal["admin", "client"]
    client_id: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class ApiTokenSummary(BaseModel):
    id: str
    name: str
    role: Literal["admin", "client"]
    client_id: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked: bool


class RegisterClientRequest(BaseModel):
    """Admin-only: provision a brand new client credential (in addition to any seeded at startup)."""
    client_id: str
    client_secret: str = Field(..., min_length=12)
