from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LogConfig:
    level: str = "INFO"
    format: str = "json"  # "json" | "text"


@dataclass(frozen=True)
class WebhookConfig:
    default_url: str | None = None
    timeout_seconds: float = 10.0
    max_retries: int = 2


@dataclass(frozen=True)
class AgentSpec:
    id: str
    class_path: str
    enabled: bool = True
    interval_seconds: float = 60.0
    config: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    log: LogConfig = LogConfig()
    webhooks: WebhookConfig = WebhookConfig()
    agents: list[AgentSpec] = field(default_factory=list)


def _require_dict(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def _require_list(value: Any, *, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _coerce_float(value: Any, *, name: str, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number") from exc


def _coerce_int(value: Any, *, name: str, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc


def load_config(path: Path) -> AppConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw = _require_dict(raw, name="config")

    log_raw = _require_dict(raw.get("log", {}), name="log")
    log = LogConfig(
        level=str(log_raw.get("level", "INFO")).upper(),
        format=str(log_raw.get("format", "json")).lower(),
    )

    web_raw = _require_dict(raw.get("webhooks", {}), name="webhooks")
    webhooks = WebhookConfig(
        default_url=web_raw.get("default_url"),
        timeout_seconds=_coerce_float(
            web_raw.get("timeout_seconds"), name="webhooks.timeout_seconds", default=10.0
        ),
        max_retries=_coerce_int(web_raw.get("max_retries"), name="webhooks.max_retries", default=2),
    )

    agents_raw = _require_list(raw.get("agents", []), name="agents")
    agents: list[AgentSpec] = []
    for idx, item in enumerate(agents_raw):
        item = _require_dict(item, name=f"agents[{idx}]")
        agent_id = str(item.get("id") or "")
        if not agent_id:
            raise ValueError(f"agents[{idx}].id is required")
        class_path = str(item.get("class") or item.get("class_path") or "")
        if not class_path:
            raise ValueError(f"agents[{idx}].class is required")
        agents.append(
            AgentSpec(
                id=agent_id,
                class_path=class_path,
                enabled=bool(item.get("enabled", True)),
                interval_seconds=_coerce_float(
                    item.get("interval_seconds"), name=f"agents[{idx}].interval_seconds", default=60.0
                ),
                config=_require_dict(item.get("config", {}), name=f"agents[{idx}].config"),
            )
        )

    return AppConfig(log=log, webhooks=webhooks, agents=agents)

