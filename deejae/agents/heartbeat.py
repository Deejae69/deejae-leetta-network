from __future__ import annotations

import logging
from datetime import datetime, timezone

from deejae.runner import Agent, AgentContext

logger = logging.getLogger(__name__)


class HeartbeatAgent(Agent):
    async def run_once(self, ctx: AgentContext) -> None:
        now = datetime.now(tz=timezone.utc).isoformat()
        logger.info("heartbeat", extra={"agent_id": ctx.agent_id, "event": "heartbeat"})
        await ctx.webhooks.send_event(
            event="heartbeat",
            title=f"Heartbeat: {ctx.agent_id}",
            body=f"ts={now}",
            agent_id=ctx.agent_id,
        )

