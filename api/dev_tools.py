"""
Developer debugging tools blueprint for DeeJae LeEtta Network.

⚠  These endpoints are DISABLED in ``production`` environments and will
   return 403 if ``ENVIRONMENT=production`` is set.

Exposes:
    GET  /dev/ping              — simple liveness check (no auth)
    GET  /dev/config            — view staging/dev config snapshot  [developer+]
    POST /dev/simulate          — simulate an internal API call      [developer+]
    POST /dev/log               — record a developer debug event     [developer+]
    GET  /dev/logs              — retrieve recent debug events        [developer+]

All non-ping endpoints require a valid JWT with role ``developer`` or ``admin``.
Each action is also written to the audit log.
"""

from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Blueprint, g, jsonify, request

import api.audit_log as audit_log
from api.auth import ROLE_ADMIN, ROLE_DEVELOPER, require_auth, require_role
from config.logging_config import setup_logger
from config.settings import ENVIRONMENT

logger = setup_logger(__name__)

dev_bp = Blueprint("dev", __name__, url_prefix="/dev")

_MAX_DEBUG_LOGS = 500
_debug_log_buffer: deque = deque(maxlen=_MAX_DEBUG_LOGS)


# ---------------------------------------------------------------------------
# Environment guard
# ---------------------------------------------------------------------------

def _production_guard():
    """Return a 403 response if running in production, else None."""
    if ENVIRONMENT.lower() == "production":
        return jsonify({
            "error": "Developer tools are disabled in production",
            "environment": ENVIRONMENT,
        }), 403
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@dev_bp.route("/ping", methods=["GET"])
def ping():
    """Simple liveness probe — no authentication required."""
    guard = _production_guard()
    if guard:
        return guard
    return jsonify({
        "status": "ok",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


@dev_bp.route("/config", methods=["GET"])
@require_auth
@require_role(ROLE_DEVELOPER, ROLE_ADMIN)
def get_dev_config():
    """Return a sanitised snapshot of the current non-production configuration.

    Sensitive values (keys, tokens, secrets) are redacted.
    """
    guard = _production_guard()
    if guard:
        return guard

    import os

    _REDACTED = "**REDACTED**"
    _SENSITIVE_KEYS = {
        "PRIVATE_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "JWT_SECRET_KEY", "WEBHOOK_SECRET", "GITHUB_TOKEN",
        "TWITTER_API_KEY", "DISCORD_WEBHOOK_URL", "DATABASE_URL",
    }

    config_snapshot: Dict[str, Any] = {}
    for key, value in os.environ.items():
        # Only expose app-relevant keys
        if not any(key.startswith(prefix) for prefix in [
            "LOG_", "TRADING_", "API_", "ENVIRONMENT", "TRACK_", "CAMPAIGN_",
            "WEBHOOK_PORT", "MFA_REQUIRED", "ADMIN_USERS",
        ]):
            continue
        config_snapshot[key] = _REDACTED if key in _SENSITIVE_KEYS else value

    actor = g.current_user.get("sub", "unknown")
    audit_log.log_event(actor, "view_dev_config", "success",
                        ip_address=request.remote_addr)
    return jsonify({"environment": ENVIRONMENT, "config": config_snapshot}), 200


@dev_bp.route("/simulate", methods=["POST"])
@require_auth
@require_role(ROLE_DEVELOPER, ROLE_ADMIN)
def simulate_api_call():
    """Simulate an internal API call for testing purposes.

    Body::

        {
            "endpoint": "/api/health",
            "method": "GET",
            "payload": {}
        }

    The simulation does not perform a real HTTP call; it exercises the
    registered Flask view functions directly via the test client.
    """
    guard = _production_guard()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    endpoint = data.get("endpoint", "")
    method = data.get("method", "GET").upper()
    payload = data.get("payload", {})
    actor = g.current_user.get("sub", "unknown")

    if not endpoint:
        return jsonify({"error": "endpoint is required"}), 400

    allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    if method not in allowed_methods:
        return jsonify({"error": f"method must be one of {allowed_methods}"}), 400

    # Use Flask's built-in test client to execute the endpoint handler
    # in-process without any external network calls.
    from flask import current_app
    with current_app.test_client() as client:
        func = getattr(client, method.lower(), None)
        if func is None:
            return jsonify({"error": "unsupported method"}), 400
        resp = func(endpoint, json=payload)
        try:
            resp_json = resp.get_json()
        except Exception:
            resp_json = None

    audit_log.log_event(actor, "simulate_api_call", "success",
                        resource=f"{method} {endpoint}",
                        details={"status_code": resp.status_code},
                        ip_address=request.remote_addr)

    return jsonify({
        "endpoint": endpoint,
        "method": method,
        "status_code": resp.status_code,
        "response": resp_json,
    }), 200


@dev_bp.route("/log", methods=["POST"])
@require_auth
@require_role(ROLE_DEVELOPER, ROLE_ADMIN)
def log_debug_event():
    """Record a developer debug event in the in-memory debug log.

    Body::

        {
            "level": "DEBUG",
            "message": "testing payment flow step 3",
            "data": {}
        }
    """
    guard = _production_guard()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    level = data.get("level", "DEBUG").upper()
    message = data.get("message", "")
    extra = data.get("data", {})
    actor = g.current_user.get("sub", "unknown")

    if not message:
        return jsonify({"error": "message is required"}), 400

    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
    if level not in valid_levels:
        return jsonify({"error": f"level must be one of {valid_levels}"}), 400

    event: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "level": level,
        "message": message,
    }
    if extra:
        event["data"] = extra

    _debug_log_buffer.append(event)
    logger.debug(f"DEV LOG | actor={actor} level={level} message={message}")

    audit_log.log_event(actor, "log_debug_event", "success",
                        details={"level": level, "message": message[:120]},
                        ip_address=request.remote_addr)

    return jsonify({"logged": True, "event": event}), 201


@dev_bp.route("/logs", methods=["GET"])
@require_auth
@require_role(ROLE_DEVELOPER, ROLE_ADMIN)
def get_debug_logs():
    """Return recent developer debug events.

    Query params:
        limit (int, default 50, max 200)
        level (str) — filter by level
        actor (str) — filter by actor
    """
    guard = _production_guard()
    if guard:
        return guard

    limit = min(int(request.args.get("limit", 50)), 200)
    level_filter = request.args.get("level", "").upper() or None
    actor_filter = request.args.get("actor", "") or None

    events: List[Dict[str, Any]] = list(_debug_log_buffer)
    if level_filter:
        events = [e for e in events if e.get("level") == level_filter]
    if actor_filter:
        events = [e for e in events if actor_filter.lower() in e.get("actor", "").lower()]

    events = events[-limit:]
    events.reverse()

    return jsonify({"events": events, "count": len(events)}), 200
