"""Configuration loader — reads JSON config file and environment variables."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


_DEFAULTS: dict[str, Any] = {
    "log_level": "INFO",
    "network": "mainnet",
    "d33j_contract": "",
    "forex": {
        "paper_trade": True,
        "initial_balance": 10_000.0,
        "max_risk_pct": 2.0,
        "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
    },
    "agents": {
        "run_interval_seconds": 3600,
        "enabled": [
            "mmo_customer",
            "ecommerce",
            "arts_marketing",
            "investor_relations",
            "trading_strategy",
            "campaign_optimizer",
        ],
    },
    "webhook": {
        "url": "",
        "secret": "",
    },
}


def load(path: str | Path | None = None) -> dict[str, Any]:
    """Return merged config: defaults ← file ← environment overrides."""
    cfg: dict[str, Any] = json.loads(json.dumps(_DEFAULTS))  # deep copy

    if path is None:
        path = os.environ.get("DEEJAE_CONFIG", "config.json")

    file_path = Path(path)
    if file_path.exists():
        with file_path.open() as fh:
            file_cfg = json.load(fh)
        _deep_merge(cfg, file_cfg)

    # Environment overrides
    if lvl := os.environ.get("DEEJAE_LOG_LEVEL"):
        cfg["log_level"] = lvl
    if net := os.environ.get("DEEJAE_NETWORK"):
        cfg["network"] = net
    if contract := os.environ.get("D33J_CONTRACT"):
        cfg["d33j_contract"] = contract
    if wh_url := os.environ.get("DEEJAE_WEBHOOK_URL"):
        cfg["webhook"]["url"] = wh_url
    if wh_secret := os.environ.get("DEEJAE_WEBHOOK_SECRET"):
        cfg["webhook"]["secret"] = wh_secret

    return cfg


def _deep_merge(base: dict, override: dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
