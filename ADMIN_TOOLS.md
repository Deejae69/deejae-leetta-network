# Admin & Developer Tools — Setup and Maintenance Guide

## Overview

This document describes the secure admin dashboard and developer debugging tools
added to the DeeJae LeEtta Network.  The implementation adds:

| Component | Description |
|-----------|-------------|
| `api/auth.py` | JWT authentication, RBAC decorators, MFA (TOTP) helpers, password hashing |
| `api/audit_log.py` | Thread-safe audit event store with file persistence and search |
| `api/admin.py` | Admin dashboard Flask blueprint |
| `api/dev_tools.py` | Developer debugging tools Flask blueprint (dev/staging only) |

---

## 1. Roles

Three roles are defined with a strict hierarchy:

| Role | Level | Capabilities |
|------|-------|-------------|
| `viewer` | 0 | Read-only access (reserved for future use) |
| `developer` | 1 | Access to developer tools endpoints |
| `admin` | 2 | Full admin dashboard + all developer tool endpoints |

A user with a higher-level role automatically satisfies lower-level requirements.

---

## 2. Environment Variables

Add these to your `.env` file (see `.env.example` for the full template):

```dotenv
# Runtime environment — set to "production" to disable developer tools
ENVIRONMENT=development        # development | staging | production

# JWT signing secret — generate with: openssl rand -hex 32
JWT_SECRET_KEY=change-me-in-production

# Token lifetime in seconds (default 3600 = 1 hour)
JWT_ACCESS_TOKEN_EXPIRES=3600

# Comma-separated list of admin usernames
ADMIN_USERS=alice,bob

# Per-user password hash (generate with the helper below)
ADMIN_PASSWORD_HASH_ALICE=<pbkdf2-hash>
ADMIN_PASSWORD_HASH_BOB=<pbkdf2-hash>

# Optional: override role for a user (default is "admin")
ADMIN_ROLE_BOB=developer

# MFA — set True to require TOTP for all admin logins
MFA_REQUIRED=False

# Per-user TOTP secret (generate with: python -c "import pyotp; print(pyotp.random_base32())")
ADMIN_TOTP_SECRET_ALICE=<base32-secret>
```

### Generating a password hash

```bash
python - <<'EOF'
from api.auth import hash_password
print(hash_password("your-password-here"))
EOF
```

Copy the output into `ADMIN_PASSWORD_HASH_<USERNAME>`.

### Generating a TOTP secret

```bash
python -c "import pyotp; print(pyotp.random_base32())"
```

Copy the output into `ADMIN_TOTP_SECRET_<USERNAME>` and scan the provisioning
URI with your authenticator app:

```bash
python - <<'EOF'
from api.auth import get_totp_provisioning_uri
print(get_totp_provisioning_uri("alice", "YOUR_BASE32_SECRET"))
EOF
```

---

## 3. Admin Dashboard Endpoints

Base URL: `http://localhost:5000/admin`

All endpoints except `/admin/login` and `/admin/login/mfa` require a valid JWT
sent in the `Authorization: Bearer <token>` header.

### Authentication

#### `POST /admin/login`

Authenticate and receive a JWT (or an MFA nonce when MFA is required).

**Request body:**
```json
{
  "username": "alice",
  "password": "your-password"
}
```

**Response (no MFA):**
```json
{
  "access_token": "<jwt>",
  "role": "admin"
}
```

**Response (MFA required):**
```json
{
  "mfa_required": true,
  "mfa_nonce": "<nonce>"
}
```

#### `POST /admin/login/mfa`

Complete the MFA challenge.

**Request body:**
```json
{
  "mfa_nonce": "<nonce-from-login>",
  "totp_code": "123456"
}
```

**Response:**
```json
{
  "access_token": "<jwt>",
  "role": "admin"
}
```

---

### Audit Log — `[admin only]`

#### `GET /admin/audit`

Search audit events.

**Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `actor` | Substring match on actor username |
| `action` | Substring match on action label |
| `outcome` | Exact match: `success`, `failure`, or `denied` |
| `since` | ISO-8601 timestamp — only events on/after this time |
| `limit` | Max results (default 100, max 500) |

**Response:**
```json
{
  "events": [
    {
      "timestamp": "2025-01-15T12:00:00+00:00",
      "actor": "alice",
      "action": "update_settings",
      "outcome": "success",
      "ip_address": "10.0.0.1"
    }
  ],
  "count": 1
}
```

---

### Settings Management — `[admin only]`

#### `GET /admin/settings`

View mutable runtime settings.

#### `PUT /admin/settings`

Update one or more mutable settings.  Only existing keys can be changed.

**Request body:**
```json
{
  "log_level": "DEBUG",
  "track_campaigns": "False"
}
```

Available mutable settings:

| Key | Default | Description |
|-----|---------|-------------|
| `log_level` | `INFO` | Logging level |
| `track_campaigns` | `True` | Enable campaign tracking |
| `campaign_check_interval` | `3600` | Campaign check interval (seconds) |

---

### API Key Management — `[admin only]`

#### `GET /admin/keys`

List registered key names (values are **never** returned).

#### `POST /admin/keys`

Register or rotate an API key.

```json
{
  "name": "openai",
  "value": "sk-..."
}
```

If `value` is omitted, a cryptographically random 32-byte token is generated.

#### `DELETE /admin/keys/<name>`

Revoke a key by name.

---

### User Management — `[admin only]`

#### `GET /admin/users`

List configured admin users and their roles.  Password hashes and TOTP secrets
are never exposed.

---

## 4. Developer Tools Endpoints

Base URL: `http://localhost:5000/dev`

> ⚠️  **All endpoints except `/dev/ping` are disabled when `ENVIRONMENT=production`.**

### `GET /dev/ping`

Liveness check — no authentication required.

### `GET /dev/config` — `[developer+]`

Returns a sanitised snapshot of the current runtime configuration.
All sensitive values (API keys, tokens, secrets) are redacted.

### `POST /dev/simulate` — `[developer+]`

Simulate an internal API call without making a real HTTP request.

```json
{
  "endpoint": "/api/health",
  "method": "GET",
  "payload": {}
}
```

### `POST /dev/log` — `[developer+]`

Record a developer debug event in the in-memory debug log.

```json
{
  "level": "DEBUG",
  "message": "testing payment flow step 3",
  "data": {"step": 3}
}
```

Supported levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`.

### `GET /dev/logs` — `[developer+]`

Retrieve recent debug events.

**Query parameters:** `limit` (default 50, max 200), `level`, `actor`.

---

## 5. Security Features

### JWT Tokens

- Signed with HS256 using a secret from `JWT_SECRET_KEY`
- Default expiry: 1 hour (configurable via `JWT_ACCESS_TOKEN_EXPIRES`)
- Minimum recommended secret length: 32 bytes
- Tokens carry `sub` (username), `role`, `iat`, and `exp` claims

### Password Storage

Passwords are stored as PBKDF2-HMAC-SHA256 hashes with a random per-user
salt (260,000 iterations).  Plain-text passwords are never logged or stored.

### Multi-Factor Authentication

TOTP (RFC 6238, compatible with Google Authenticator, Authy, etc.) is supported
for all admin users.  Enable with `MFA_REQUIRED=True`.  The MFA flow:

1. `POST /admin/login` → returns `mfa_nonce` (valid 2 minutes)
2. User enters 6-digit TOTP code from their authenticator app
3. `POST /admin/login/mfa` → returns final JWT

### Audit Logging

Every administrative action is written to:

- An in-memory circular buffer (last 1 000 events)
- A daily JSON-lines file under `logs/audit/audit_YYYYMMDD.jsonl`

Each event records: `timestamp`, `actor`, `action`, `outcome`, optional
`resource`, `details`, and `ip_address`.

### Production Guard

All developer tool endpoints (except `/dev/ping`) return **HTTP 403** when
`ENVIRONMENT=production`.  Set this environment variable in your production
deployment to prevent accidental exposure.

---

## 6. Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run only the auth/admin/dev-tools tests
python -m pytest tests/test_auth.py tests/test_admin.py tests/test_dev_tools.py -v

# Run full test suite
python -m pytest
```

---

## 7. Maintenance Checklist

- [ ] Rotate `JWT_SECRET_KEY` regularly (quarterly recommended)
- [ ] Use `POST /admin/keys` to rotate API keys; revoke old ones with `DELETE /admin/keys/<name>`
- [ ] Review `logs/audit/` files regularly; archive and purge old files
- [ ] Keep `MFA_REQUIRED=True` in production
- [ ] Ensure `ENVIRONMENT=production` in all production deployments
- [ ] Keep `PyJWT` and `pyotp` up to date (check `pip audit`)
