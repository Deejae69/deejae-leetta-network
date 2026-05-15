from __future__ import annotations

import asyncio
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

from deejae.config import WebhookConfig

logger = logging.getLogger(__name__)


class WebhookClient:
    def __init__(self, config: WebhookConfig) -> None:
        self._config = config

    async def send_event(
        self,
        *,
        event: str,
        title: str,
        body: str,
        agent_id: str | None,
        url: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        url = url or self._config.default_url
        if not url:
            return

        payload: dict[str, Any] = {
            "event": event,
            "title": title,
            "body": body,
            "agent_id": agent_id,
            "extra": extra or {},
        }
        try:
            await asyncio.to_thread(self._post_json_sync, url, payload)
        except Exception as exc:
            logger.warning("webhook_send_event_failed", extra={"event": "webhook", "error": str(exc)})

    def _post_json_sync(self, url: str, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "deejae/0.1"},
            method="POST",
        )

        last_exc: Exception | None = None
        for attempt in range(self._config.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self._config.timeout_seconds) as response:
                    response.read()
                logger.info("webhook_sent", extra={"event": "webhook", "attempt": attempt})
                return
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = exc
                logger.warning(
                    "webhook_send_failed",
                    extra={"event": "webhook", "attempt": attempt, "error": str(exc)},
                )
                if attempt < self._config.max_retries:
                    time.sleep(min(2.0, 0.25 * (2**attempt)))

        if last_exc:
            raise last_exc
