"""
Audit log module for DeeJae LeEtta Network.

Provides:
- Thread-safe in-memory circular buffer of audit events
- File persistence (one JSON-lines file per day under logs/audit/)
- Structured event records with timestamp, actor, action, IP, outcome
- Search / filter helpers consumed by the admin dashboard
"""

import json
import os
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.logging_config import setup_logger

logger = setup_logger(__name__)

_AUDIT_LOG_DIR = Path(__file__).parent.parent / "logs" / "audit"
_AUDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

_MAX_IN_MEMORY = 1000  # keep the last N events in RAM

_lock = threading.Lock()
_buffer: deque = deque(maxlen=_MAX_IN_MEMORY)

# Keys in the ``details`` dict that must be redacted before storage or logging
_SENSITIVE_DETAIL_KEYS = {
    "password", "passwd", "secret", "token", "key",
    "api_key", "private_key", "totp_code", "mfa_code",
}


def _sanitize_details(details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return a copy of *details* with any sensitive keys replaced by ``**REDACTED**``."""
    if not details:
        return details
    return {
        k: "**REDACTED**" if k.lower() in _SENSITIVE_DETAIL_KEYS else v
        for k, v in details.items()
    }


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _today_log_file() -> Path:
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return _AUDIT_LOG_DIR / f"audit_{date_str}.jsonl"


def log_event(
    actor: str,
    action: str,
    outcome: str,
    resource: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a single audit event.

    Args:
        actor: Username or ``"system"`` performing the action.
        action: Human-readable action label (e.g. ``"login"``, ``"update_setting"``).
        outcome: ``"success"`` | ``"failure"`` | ``"denied"``.
        resource: Optional resource being acted upon (e.g. ``"api_key:123"``).
        details: Optional free-form metadata dict.
        ip_address: Caller's IP address.

    Returns:
        The event dict that was stored.
    """
    event: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "outcome": outcome,
    }
    if resource:
        event["resource"] = resource
    if details:
        event["details"] = _sanitize_details(details)
    if ip_address:
        event["ip_address"] = ip_address

    with _lock:
        _buffer.append(event)
        try:
            with _today_log_file().open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event) + "\n")
        except OSError as exc:
            logger.error(f"Failed to write audit log: {exc}")

    logger.info(f"AUDIT | actor={actor} action={action} outcome={outcome}")
    return event


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_recent_events(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent *limit* events from the in-memory buffer."""
    with _lock:
        events = list(_buffer)
    return events[-limit:]


def search_events(
    actor: Optional[str] = None,
    action: Optional[str] = None,
    outcome: Optional[str] = None,
    since: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Filter audit events from the in-memory buffer.

    Args:
        actor: Filter by actor (case-insensitive substring match).
        action: Filter by action (case-insensitive substring match).
        outcome: Exact match on outcome field.
        since: ISO-8601 datetime string; only events on or after this time.
        limit: Maximum number of results.

    Returns:
        Filtered list, newest-first.
    """
    with _lock:
        events = list(_buffer)

    results = []
    for evt in reversed(events):
        if actor and actor.lower() not in evt.get("actor", "").lower():
            continue
        if action and action.lower() not in evt.get("action", "").lower():
            continue
        if outcome and evt.get("outcome") != outcome:
            continue
        if since:
            if evt.get("timestamp", "") < since:
                continue
        results.append(evt)
        if len(results) >= limit:
            break

    return results


def get_log_files() -> List[str]:
    """Return sorted list of audit log file paths (newest first)."""
    files = sorted(_AUDIT_LOG_DIR.glob("audit_*.jsonl"), reverse=True)
    return [str(f) for f in files]
