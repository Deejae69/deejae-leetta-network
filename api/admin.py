"""
Admin dashboard blueprint for DeeJae LeEtta Network.

Exposes:
    POST /admin/login           — issue JWT (+ MFA challenge if MFA_REQUIRED)
    POST /admin/login/mfa       — complete MFA and receive final JWT
    GET  /admin/audit           — search audit log          [admin only]
    GET  /admin/settings        — view current settings      [admin only]
    PUT  /admin/settings        — update mutable settings    [admin only]
    GET  /admin/keys            — list managed API-key names [admin only]
    POST /admin/keys            — register / rotate key      [admin only]
    DELETE /admin/keys/<name>   — revoke a key               [admin only]
    GET  /admin/users           — list configured users      [admin only]

All mutating endpoints write an audit event.  Authentication uses JWTs
issued by ``api.auth``.  MFA (TOTP) can be required via ``MFA_REQUIRED``.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Blueprint, request, jsonify, g

from config.logging_config import setup_logger
from config.settings import MFA_REQUIRED, ADMIN_USERS
import api.audit_log as audit_log
from api.auth import (
    ROLE_ADMIN,
    ROLE_DEVELOPER,
    create_access_token,
    get_user,
    hash_password,
    require_auth,
    require_role,
    verify_password,
    verify_totp,
)

logger = setup_logger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ---------------------------------------------------------------------------
# In-memory key store (production should replace with a secrets manager)
# ---------------------------------------------------------------------------
# {name: {"value": "...", "created_at": "...", "created_by": "..."}}
_api_keys: Dict[str, Dict[str, Any]] = {}

# Mutable settings store (a small subset of the full config)
_mutable_settings: Dict[str, Any] = {
    "log_level": os.getenv("LOG_LEVEL", "INFO"),
    "track_campaigns": os.getenv("TRACK_CAMPAIGNS", "True"),
    "campaign_check_interval": int(os.getenv("CAMPAIGN_CHECK_INTERVAL", "3600")),
}

# Pending MFA tokens keyed by a short-lived nonce
_mfa_pending: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@admin_bp.route("/login", methods=["POST"])
def login():
    """Authenticate an admin user and issue a JWT (or MFA nonce)."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    client_ip = request.remote_addr

    user = get_user(username)
    if not user:
        audit_log.log_event("unknown", "login", "failure",
                            details={"username": username}, ip_address=client_ip)
        return jsonify({"error": "Invalid credentials"}), 401

    if not verify_password(password, user.password_hash):
        audit_log.log_event(username, "login", "failure",
                            details={"reason": "bad_password"}, ip_address=client_ip)
        return jsonify({"error": "Invalid credentials"}), 401

    # MFA required and user has a secret configured
    if MFA_REQUIRED and user.totp_secret:
        import secrets as _secrets
        nonce = _secrets.token_urlsafe(24)
        _mfa_pending[nonce] = {
            "username": username,
            "role": user.role,
            "totp_secret": user.totp_secret,
            "expires_at": datetime.now(timezone.utc).timestamp() + 120,  # 2 min
        }
        audit_log.log_event(username, "login_mfa_challenge", "success",
                            ip_address=client_ip)
        return jsonify({"mfa_required": True, "mfa_nonce": nonce}), 200

    token = create_access_token(username, user.role)
    audit_log.log_event(username, "login", "success", ip_address=client_ip)
    return jsonify({"access_token": token, "role": user.role}), 200


@admin_bp.route("/login/mfa", methods=["POST"])
def login_mfa():
    """Complete the MFA challenge and issue a final JWT."""
    data = request.get_json(silent=True) or {}
    nonce = data.get("mfa_nonce", "")
    code = data.get("totp_code", "")
    client_ip = request.remote_addr

    pending = _mfa_pending.get(nonce)
    if not pending:
        return jsonify({"error": "Invalid or expired MFA session"}), 401

    if datetime.now(timezone.utc).timestamp() > pending["expires_at"]:
        _mfa_pending.pop(nonce, None)
        return jsonify({"error": "MFA session expired"}), 401

    if not verify_totp(pending["totp_secret"], code):
        audit_log.log_event(pending["username"], "login_mfa", "failure",
                            details={"reason": "bad_totp"}, ip_address=client_ip)
        return jsonify({"error": "Invalid MFA code"}), 401

    _mfa_pending.pop(nonce, None)
    username = pending["username"]
    role = pending["role"]
    token = create_access_token(username, role)
    audit_log.log_event(username, "login_mfa", "success", ip_address=client_ip)
    return jsonify({"access_token": token, "role": role}), 200


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

@admin_bp.route("/audit", methods=["GET"])
@require_auth
@require_role(ROLE_ADMIN)
def get_audit_log():
    """Return recent audit events, with optional filtering."""
    actor = request.args.get("actor")
    action = request.args.get("action")
    outcome = request.args.get("outcome")
    since = request.args.get("since")
    limit = min(int(request.args.get("limit", 100)), 500)

    events = audit_log.search_events(actor=actor, action=action,
                                     outcome=outcome, since=since, limit=limit)
    return jsonify({"events": events, "count": len(events)}), 200


# ---------------------------------------------------------------------------
# Settings management
# ---------------------------------------------------------------------------

@admin_bp.route("/settings", methods=["GET"])
@require_auth
@require_role(ROLE_ADMIN)
def get_settings():
    """Return the current mutable settings."""
    return jsonify({"settings": _mutable_settings}), 200


@admin_bp.route("/settings", methods=["PUT"])
@require_auth
@require_role(ROLE_ADMIN)
def update_settings():
    """Update one or more mutable settings.

    Only keys already present in ``_mutable_settings`` can be changed.
    """
    data = request.get_json(silent=True) or {}
    actor = g.current_user.get("sub", "unknown")
    client_ip = request.remote_addr

    updated = {}
    for key, value in data.items():
        if key not in _mutable_settings:
            return jsonify({"error": f"Unknown setting: {key}"}), 400
        old_value = _mutable_settings[key]
        _mutable_settings[key] = value
        updated[key] = {"old": old_value, "new": value}

    audit_log.log_event(actor, "update_settings", "success",
                        details={"changes": updated}, ip_address=client_ip)
    return jsonify({"settings": _mutable_settings, "updated": list(updated.keys())}), 200


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------

@admin_bp.route("/keys", methods=["GET"])
@require_auth
@require_role(ROLE_ADMIN)
def list_keys():
    """List registered API-key names (values are never returned)."""
    keys_summary = [
        {"name": name, "created_at": info["created_at"], "created_by": info["created_by"]}
        for name, info in _api_keys.items()
    ]
    return jsonify({"keys": keys_summary}), 200


@admin_bp.route("/keys", methods=["POST"])
@require_auth
@require_role(ROLE_ADMIN)
def add_or_rotate_key():
    """Register or rotate an API key.

    Body: ``{ "name": "my-service", "value": "secret-value" }``
    """
    import secrets as _secrets

    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    value = data.get("value") or _secrets.token_urlsafe(32)
    actor = g.current_user.get("sub", "unknown")
    client_ip = request.remote_addr

    if not name:
        return jsonify({"error": "name is required"}), 400

    action = "rotate_key" if name in _api_keys else "create_key"
    _api_keys[name] = {
        "value": value,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": actor,
    }
    audit_log.log_event(actor, action, "success",
                        resource=f"api_key:{name}", ip_address=client_ip)
    return jsonify({"name": name, "created_at": _api_keys[name]["created_at"]}), 201


@admin_bp.route("/keys/<name>", methods=["DELETE"])
@require_auth
@require_role(ROLE_ADMIN)
def delete_key(name: str):
    """Revoke an API key by name."""
    actor = g.current_user.get("sub", "unknown")
    client_ip = request.remote_addr

    if name not in _api_keys:
        return jsonify({"error": "Key not found"}), 404

    del _api_keys[name]
    audit_log.log_event(actor, "revoke_key", "success",
                        resource=f"api_key:{name}", ip_address=client_ip)
    return jsonify({"deleted": name}), 200


# ---------------------------------------------------------------------------
# User listing (read-only)
# ---------------------------------------------------------------------------

@admin_bp.route("/users", methods=["GET"])
@require_auth
@require_role(ROLE_ADMIN)
def list_users():
    """Return configured admin usernames and their roles (no password info)."""
    users = []
    for username in ADMIN_USERS:
        username = username.strip()
        if not username:
            continue
        user = get_user(username)
        if user:
            users.append({
                "username": user.username,
                "role": user.role,
                "mfa_configured": bool(user.totp_secret),
            })
    return jsonify({"users": users}), 200
