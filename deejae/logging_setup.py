from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from deejae.config import LogConfig


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key in ("agent_id", "event", "symbol"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(config: LogConfig) -> None:
    level = getattr(logging, config.level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    if config.format == "text":
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    else:
        handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=level, handlers=[handler])

    logging.getLogger("asyncio").setLevel(max(level, logging.WARNING))
