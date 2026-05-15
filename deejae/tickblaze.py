"""Tickblaze API connectivity helpers (stdlib-only)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return ""
    if "://" not in base_url:
        base_url = "https://" + base_url
    return base_url.rstrip("/")


def _build_url(base_url: str, path: str) -> str:
    base = _normalize_base_url(base_url)
    if not base:
        return ""
    path = (path or "/").strip()
    if not path.startswith("/"):
        path = "/" + path
    return base + path


def _headers_to_dict(headers: Any) -> dict[str, str]:
    if headers is None:
        return {}
    if isinstance(headers, dict):
        return {str(k): str(v) for k, v in headers.items()}
    try:
        return {str(k): str(v) for k, v in headers.items()}
    except Exception:
        return {}


def _auth_header_value(api_key: str, auth_prefix: str) -> str:
    prefix = (auth_prefix or "").strip()
    if not prefix:
        return api_key
    return f"{prefix} {api_key}"


def test_connection(
    *,
    base_url: str,
    path: str = "/",
    api_key: str = "",
    auth_header: str = "Authorization",
    auth_prefix: str = "Bearer",
    timeout_seconds: float = 10.0,
    show_body: bool = False,
    max_body_bytes: int = 16 * 1024,
) -> dict[str, Any]:
    """
    Attempt a GET request and return a structured result.

    - Does not include the API key in returned output.
    - `reachable` is true when an HTTP response is received (even 401/404).
    """
    url = _build_url(base_url, path)
    started = time.monotonic()

    if not url:
        return {
            "ok": False,
            "reachable": False,
            "url": url,
            "elapsed_ms": 0,
            "error": {"type": "ValueError", "message": "Missing Tickblaze base_url"},
        }

    request = urllib.request.Request(url, method="GET")
    request.add_header("Accept", "application/json")

    api_key = (api_key or "").strip()
    if api_key:
        hdr_name = (auth_header or "Authorization").strip() or "Authorization"
        request.add_header(hdr_name, _auth_header_value(api_key, auth_prefix))

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as resp:
            status_code = getattr(resp, "status", None) or resp.getcode()
            headers = _headers_to_dict(getattr(resp, "headers", None))
            elapsed_ms = int((time.monotonic() - started) * 1000)

            result: dict[str, Any] = {
                "ok": True,
                "reachable": True,
                "url": url,
                "status_code": status_code,
                "elapsed_ms": elapsed_ms,
                "auth_ok": None if not api_key else status_code not in (401, 403),
                "headers": headers,
            }

            if show_body:
                body = resp.read(max_body_bytes)
                content_type = (headers.get("Content-Type") or "").lower()
                if "application/json" in content_type:
                    try:
                        result["body"] = json.loads(body.decode("utf-8", errors="replace"))
                    except json.JSONDecodeError:
                        result["body"] = body.decode("utf-8", errors="replace")
                else:
                    result["body"] = body.decode("utf-8", errors="replace")

            return result

    except urllib.error.HTTPError as e:
        status_code = getattr(e, "code", None)
        headers = _headers_to_dict(getattr(e, "headers", None))
        elapsed_ms = int((time.monotonic() - started) * 1000)

        result: dict[str, Any] = {
            "ok": True,
            "reachable": True,
            "url": url,
            "status_code": status_code,
            "elapsed_ms": elapsed_ms,
            "auth_ok": None if not api_key else status_code not in (401, 403),
            "headers": headers,
            "error": {"type": "HTTPError", "message": str(e)},
        }
        if show_body:
            try:
                body = e.read(max_body_bytes)
            except Exception:
                body = b""
            result["body"] = body.decode("utf-8", errors="replace")
        return result

    except Exception as e:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return {
            "ok": False,
            "reachable": False,
            "url": url,
            "elapsed_ms": elapsed_ms,
            "error": {"type": type(e).__name__, "message": str(e)},
        }

