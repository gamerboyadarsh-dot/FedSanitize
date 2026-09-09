# Merging the auth module into FedSanitize

This folder is fully self-contained and does not modify anything by
itself. Follow these steps to wire it in.

## 1. Copy files in

```
backend_api/auth/            -> merge into your existing backend_api/auth/
requirements-auth.txt        -> merge into your existing requirements.txt
.env.example                 -> project root (copy to .env and fill in)
```

## 2. Install dependencies

```bash
pip install -r requirements-auth.txt
```

## 3. Edit `backend_api/main.py`

### 3a. Imports — add near the top, after the existing imports:

```python
from backend_api.auth import auth_router, require_admin, require_client_or_admin
from backend_api.auth.bootstrap import bootstrap_auth
```

### 3b. Bootstrap + mount the router — right after `app = FastAPI(...)`
and the CORS middleware block, add:

```python
bootstrap_auth()
app.include_router(auth_router)
```

### 3c. Protect the existing routes

Add a `Depends(...)` parameter to each existing endpoint. Suggested
split for this project:

| Endpoint                              | Method | Dependency                    |
|----------------------------------------|--------|--------------------------------|
| `/health`                              | GET    | none (leave public for uptime checks/load balancers) |
| `/config`                              | GET    | `require_client_or_admin`     |
| `/config`                              | POST   | `require_admin`               |
| `/clients`                             | GET    | `require_client_or_admin`     |
| `/clients/{client_id}/attack`          | POST   | `require_admin`               |
| `/simulation/round`                    | POST   | `require_admin`               |
| `/simulation/reset`                    | POST   | `require_admin`               |
| `/simulation/load-demo`                | POST   | `require_admin`               |
| `/experiments/history`                 | GET    | `require_client_or_admin`     |

Example diff for one mutating and one read-only route (repeat the
pattern for the rest of the table above):

```diff
+from backend_api.auth.dependencies import Principal

 @app.post("/config")
-def update_config(update_req: ConfigUpdateRequest):
+def update_config(update_req: ConfigUpdateRequest, _: Principal = Depends(require_admin)):
     """Updates configuration dataclasses safely."""
     ...

 @app.get("/clients", response_model=List[ClientSummary])
-def list_clients():
+def list_clients(_: Principal = Depends(require_client_or_admin)):
     """Lists all configured clients with their latest security evaluation status."""
     ...
```

`Depends` is already imported by FastAPI in most setups; add it to the
top-level `from fastapi import ...` line if it isn't already there.

### 3d. Client-scoped attack assignment (optional, tighter policy)

If you want a client to only ever be able to modify *its own* entry
(instead of any client an authenticated client-role token could touch),
swap `require_admin` on `/clients/{client_id}/attack` for the
per-route factory:

```python
from backend_api.auth.dependencies import require_own_client_or_admin

@app.post("/clients/{client_id}/attack")
def set_client_attack(
    client_id: str,
    req: AttackAssignmentRequest,
    _: Principal = Depends(require_own_client_or_admin(client_id)),
):
    ...
```

(Note `require_own_client_or_admin` still lets admins act on any
client; only client-role callers are restricted to their own id. Given
this endpoint reassigns *attack type* — a simulation/admin concept — the
simple `require_admin` in the table above is the recommended default;
this variant is here if your deployment wants clients self-managing
their own attack designation.)

## 4. Frontend

`frontend/src/api/auth.ts` (included alongside this guide) is a small,
dependency-free helper: `login()`, `logout()`, `getAccessToken()`, and
an `authFetch()` wrapper that attaches the `Authorization` header and
transparently retries once after refreshing an expired access token.

Update `frontend/src/api/client.ts` to route its `fetch()` calls through
`authFetch()` instead of the bare `fetch()`, and add a login screen that
calls `login()` before the app renders (see the comment block at the
top of `auth.ts` for the exact call shape). Both admin and client
credentials use the same `login()` / `authFetch()` API — pass a
`role: "admin"` or `role: "client"` login payload and the module talks
to the right endpoint.

## 5. First run checklist

1. Set `FEDSANITIZE_SECRET_KEY` in `.env` (a blank value auto-generates
   one per process, which breaks multi-worker deployments and
   invalidates tokens on every restart).
2. Start the server; if `FEDSANITIZE_ADMIN_PASSWORD` was left blank,
   copy the printed admin password immediately — it is not stored or
   shown again.
3. `POST /auth/login` (form-encoded `username`/`password`) to confirm
   you get back a token pair.
4. `POST /auth/change-password` to rotate off the generated password.
5. For each real edge client, either:
   - seed it via `FEDSANITIZE_SEED_CLIENT_IDS` for a quick demo, or
   - `POST /auth/register-client` (admin-only) for a real deployment,
     then have that client call `POST /auth/client-login`, or
   - issue it a non-expiring `POST /auth/api-tokens` credential instead
     of a login flow, if it's a headless script rather than an
     interactive session.
6. Confirm a request to a protected route (e.g. `GET /clients`) without
   any credential returns `401`, and with a client-role token against
   an admin-only route (e.g. `POST /config`) returns `403`.
