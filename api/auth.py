"""
Authentication and authorisation module for DeeJae LeEtta Network.

Provides:
- Role-based access control (RBAC): roles admin, developer, viewer
- JWT-based token issuance / validation
- TOTP-based Multi-Factor Authentication helpers
- Password hashing / verification using stdlib PBKDF2-SHA256
- ``require_auth`` / ``require_role`` Flask request decorators
- User look-up from environment-variable-backed user store
"""

import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, List, Optional

import jwt
import pyotp
from flask import request, jsonify, g

from config.logging_config import setup_logger
from config.settings import (
    JWT_SECRET_KEY,
    JWT_ACCESS_TOKEN_EXPIRES,
    ADMIN_USERS,
    MFA_REQUIRED,
)

logger = setup_logger(__name__)

# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

ROLE_ADMIN = "admin"
ROLE_DEVELOPER = "developer"
ROLE_VIEWER = "viewer"

ROLE_HIERARCHY: Dict[str, int] = {
    ROLE_VIEWER: 0,
    ROLE_DEVELOPER: 1,
    ROLE_ADMIN: 2,
}


# ---------------------------------------------------------------------------
# Password helpers (PBKDF2-SHA256, stdlib only)
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS = 260_000
_PBKDF2_HASH = "sha256"


def hash_password(password: str) -> str:
    """Return a *salt$hash* string suitable for storage.

    Uses PBKDF2-HMAC-SHA256 with a random 16-byte salt.
    """
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        _PBKDF2_HASH,
        password.encode(),
        salt.encode(),
        _PBKDF2_ITERATIONS,
    )
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Constant-time password verification."""
    try:
        salt, hash_hex = stored_hash.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac(
        _PBKDF2_HASH,
        password.encode(),
        salt.encode(),
        _PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(dk.hex(), hash_hex)


# ---------------------------------------------------------------------------
# User store (backed by environment variables)
# ---------------------------------------------------------------------------

class User:
    """Lightweight user representation."""

    def __init__(self, username: str, role: str, password_hash: str, totp_secret: Optional[str] = None):
        self.username = username
        self.role = role
        self.password_hash = password_hash
        self.totp_secret = totp_secret

    def has_role(self, required_role: str) -> bool:
        """Return True if this user's role is >= required_role in hierarchy."""
        return ROLE_HIERARCHY.get(self.role, -1) >= ROLE_HIERARCHY.get(required_role, 0)


def _load_users() -> Dict[str, User]:
    """Load users from environment variables.

    Reads ADMIN_USERS (comma-separated list of usernames) and for each
    username looks up:
        ADMIN_PASSWORD_HASH_<UPPERCASE_USERNAME>  — PBKDF2 hash (or empty)
        ADMIN_TOTP_SECRET_<UPPERCASE_USERNAME>    — base32 TOTP secret (optional)
        ADMIN_ROLE_<UPPERCASE_USERNAME>           — role override (default: admin)
    """
    users: Dict[str, User] = {}
    for username in ADMIN_USERS:
        username = username.strip()
        if not username:
            continue
        key = username.upper()
        pw_hash = os.getenv(f"ADMIN_PASSWORD_HASH_{key}", "")
        totp_secret = os.getenv(f"ADMIN_TOTP_SECRET_{key}", "") or None
        role = os.getenv(f"ADMIN_ROLE_{key}", ROLE_ADMIN)
        users[username] = User(username=username, role=role, password_hash=pw_hash, totp_secret=totp_secret)
    return users


def get_user(username: str) -> Optional[User]:
    """Look up a user by username (reloads from env each call to pick up changes in tests)."""
    return _load_users().get(username)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

_JWT_ALGORITHM = "HS256"


def create_access_token(username: str, role: str) -> str:
    """Issue a signed JWT access token."""
    now = int(time.time())
    payload = {
        "sub": username,
        "role": role,
        "iat": now,
        "exp": now + JWT_ACCESS_TOKEN_EXPIRES,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=_JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict:
    """Decode and validate a JWT access token.

    Raises ``jwt.PyJWTError`` on any validation failure.
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[_JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# MFA (TOTP) helpers
# ---------------------------------------------------------------------------

def verify_totp(totp_secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code against the user's secret."""
    totp = pyotp.TOTP(totp_secret)
    return totp.verify(code, valid_window=1)


def generate_totp_secret() -> str:
    """Generate a fresh base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_provisioning_uri(username: str, totp_secret: str) -> str:
    """Return an otpauth:// URI for use with authenticator apps."""
    totp = pyotp.TOTP(totp_secret)
    return totp.provisioning_uri(name=username, issuer_name="DeeJae LeEtta Network")


# ---------------------------------------------------------------------------
# Flask decorators
# ---------------------------------------------------------------------------

def _extract_bearer_token() -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def require_auth(f):
    """Decorator: ensures the request carries a valid JWT.

    On success the decoded token payload is available as ``g.current_user``.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"error": "Authentication required"}), 401
        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.PyJWTError as exc:
            logger.warning(f"Invalid token: {exc}")
            return jsonify({"error": "Invalid token"}), 401
        g.current_user = payload
        return f(*args, **kwargs)
    return decorated


def require_role(*roles: str):
    """Decorator factory: ensures the authenticated user has one of the given roles.

    Must be used *after* ``@require_auth``.

    Example::

        @app.route('/admin/...')
        @require_auth
        @require_role('admin')
        def admin_endpoint(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_payload = getattr(g, "current_user", None)
            if not user_payload:
                return jsonify({"error": "Authentication required"}), 401
            user_role = user_payload.get("role", "")
            # Accept if user's role level is >= the minimum required
            min_level = min(ROLE_HIERARCHY.get(r, 0) for r in roles)
            if ROLE_HIERARCHY.get(user_role, -1) < min_level:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
