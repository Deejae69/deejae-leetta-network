from __future__ import annotations

import asyncio
import importlib
import logging
from dataclasses import dataclass
from typing import Any

from deejae.config import AppConfig, AgentSpec
from deejae.webhooks import WebhookClient

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    agent_id: str
    config: dict[str, Any]
    webhooks: WebhookClient


class Agent:
    async def run_once(self, ctx: AgentContext) -> None:  # pragma: no cover (protocol-like)
        raise NotImplementedError


def _load_agent_class(class_path: str) -> type[Agent]:
    module_name, _, attr = class_path.rpartition(".")
    if not module_name:
        raise ValueError(f"Invalid agent class path: {class_path}")
    module = importlib.import_module(module_name)
    cls = getattr(module, attr, None)
    if cls is None:
        raise ValueError(f"Agent class not found: {class_path}")
    if not isinstance(cls, type):
        raise ValueError(f"Agent class path is not a class: {class_path}")
    return cls


def _instantiate_agent(spec: AgentSpec) -> Agent:
    cls = _load_agent_class(spec.class_path)
    return cls()


async def _run_agent_loop(*, spec: AgentSpec, app: AppConfig, webhooks: WebhookClient) -> None:
    agent = _instantiate_agent(spec)
    ctx = AgentContext(agent_id=spec.id, config=spec.config, webhooks=webhooks)
    while True:
        try:
            await agent.run_once(ctx)
        except Exception:
            logger.exception("agent_run_failed", extra={"agent_id": spec.id, "event": "agent_error"})
            await webhooks.send_event(
                event="agent_error",
                title=f"Agent failed: {spec.id}",
                body="See logs for traceback.",
                agent_id=spec.id,
            )
        await asyncio.sleep(max(0.1, float(spec.interval_seconds)))


async def run_agents_forever(app: AppConfig) -> None:
    webhooks = WebhookClient(app.webhooks)
    enabled = [spec for spec in app.agents if spec.enabled]
    if not enabled:
        logger.warning("no_agents_enabled", extra={"event": "config"})
        return

    await webhooks.send_event(event="runner_start", title="Agent runner started", body="", agent_id=None)
    tasks = [asyncio.create_task(_run_agent_loop(spec=spec, app=app, webhooks=webhooks)) for spec in enabled]
    await asyncio.gather(*tasks)


async def run_agents_once(app: AppConfig) -> None:
    webhooks = WebhookClient(app.webhooks)
    for spec in app.agents:
        if not spec.enabled:
            continue
        agent = _instantiate_agent(spec)
        ctx = AgentContext(agent_id=spec.id, config=spec.config, webhooks=webhooks)
        await agent.run_once(ctx)

