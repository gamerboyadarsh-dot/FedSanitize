"""
FedSanitize Auth — Credential Stores
=====================================
FedSanitize's existing backend (`StateManager` in `backend_api/main.py`)
keeps all state in memory with no database, so this module follows the
same pattern for consistency and zero new infra dependencies.

Everything here is intentionally behind small, swappable classes
(`UserStore`, `ClientCredentialStore`, `ApiTokenStore`) with a plain
Python-object interface. If/when FedSanitize adds a real database, only
these three classes need reimplementing — nothing in `router.py` or
`dependencies.py` has to change.

Thread-safety: a single `threading.Lock` guards each store, which is
sufficient for FastAPI's default threadpool execution of sync endpoints
and for a single async event loop. If you move to multiple worker
processes, back these with a real DB (or Redis) instead — in-memory
state does not survive process restarts and is not shared across workers.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from .security import hash_password, verify_password, generate_api_token, hash_api_token


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Admin users
# ---------------------------------------------------------------------------

@dataclass
class AdminUser:
    username: str
    password_hash: str


class UserStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._admins: Dict[str, AdminUser] = {}

    def create_admin(self, username: str, plain_password: str) -> AdminUser:
        with self._lock:
            user = AdminUser(username=username, password_hash=hash_password(plain_password))
            self._admins[username] = user
            return user

    def get_admin(self, username: str) -> Optional[AdminUser]:
        with self._lock:
            return self._admins.get(username)

    def verify_admin_password(self, username: str, plain_password: str) -> bool:
        user = self.get_admin(username)
        if user is None:
            return False
        return verify_password(plain_password, user.password_hash)

    def set_admin_password(self, username: str, new_plain_password: str) -> bool:
        with self._lock:
            user = self._admins.get(username)
            if user is None:
                return False
            user.password_hash = hash_password(new_plain_password)
            return True


# ---------------------------------------------------------------------------
# Edge-client credentials (client_id + shared secret)
# ---------------------------------------------------------------------------

@dataclass
class ClientCredential:
    client_id: str
    secret_hash: str


class ClientCredentialStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clients: Dict[str, ClientCredential] = {}

    def register(self, client_id: str, plain_secret: str) -> ClientCredential:
        with self._lock:
            cred = ClientCredential(client_id=client_id, secret_hash=hash_password(plain_secret))
            self._clients[client_id] = cred
            return cred

    def exists(self, client_id: str) -> bool:
        with self._lock:
            return client_id in self._clients

    def verify(self, client_id: str, plain_secret: str) -> bool:
        with self._lock:
            cred = self._clients.get(client_id)
        if cred is None:
            return False
        return verify_password(plain_secret, cred.secret_hash)


# ---------------------------------------------------------------------------
# Long-lived, revocable API tokens (admin- or client-scoped)
# ---------------------------------------------------------------------------

@dataclass
class ApiToken:
    id: str
    token_hash: str
    name: str
    role: str  # "admin" | "client"
    client_id: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    revoked: bool = False


class ApiTokenStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tokens: Dict[str, ApiToken] = {}  # keyed by token id
        self._by_hash: Dict[str, str] = {}      # token_hash -> id, for O(1) lookup

    def create(
        self,
        *,
        name: str,
        role: str,
        client_id: Optional[str] = None,
        expires_in_days: Optional[int] = None,
    ) -> tuple[ApiToken, str]:
        raw_token = generate_api_token()
        token_hash = hash_api_token(raw_token)
        token_id = uuid.uuid4().hex
        expires_at = (
            _utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
        )
        record = ApiToken(
            id=token_id,
            token_hash=token_hash,
            name=name,
            role=role,
            client_id=client_id,
            created_at=_utcnow(),
            expires_at=expires_at,
        )
        with self._lock:
            self._tokens[token_id] = record
            self._by_hash[token_hash] = token_id
        return record, raw_token

    def resolve(self, raw_token: str) -> Optional[ApiToken]:
        token_hash = hash_api_token(raw_token)
        with self._lock:
            token_id = self._by_hash.get(token_hash)
            if token_id is None:
                return None
            record = self._tokens.get(token_id)
        if record is None or record.revoked:
            return None
        if record.expires_at is not None and record.expires_at < _utcnow():
            return None
        return record

    def revoke(self, token_id: str) -> bool:
        with self._lock:
            record = self._tokens.get(token_id)
            if record is None:
                return False
            record.revoked = True
            return True

    def list_all(self) -> list[ApiToken]:
        with self._lock:
            return list(self._tokens.values())


# ---------------------------------------------------------------------------
# Module-level singletons (mirrors the existing `StateManager` pattern)
# ---------------------------------------------------------------------------

user_store = UserStore()
client_credential_store = ClientCredentialStore()
api_token_store = ApiTokenStore()
