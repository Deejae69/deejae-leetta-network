from __future__ import annotations

import logging
from pathlib import Path

from deejae.forex.csv_data import load_candles_csv
from deejae.runner import Agent, AgentContext
from deejae.state import store_from_config

logger = logging.getLogger(__name__)


class ForexDataAgent(Agent):
    async def run_once(self, ctx: AgentContext) -> None:
        csv_path = Path(ctx.config.get("csv_path") or "examples/eurusd_sample.csv")
        limit = int(ctx.config.get("limit", 500))
        store = store_from_config(ctx.config)
        candles = load_candles_csv(csv_path, limit=limit)

        state = store.read()
        state["forex"] = state.get("forex", {})
        state["forex"]["candles"] = [
            {"ts": c.ts.isoformat(), "open": c.open, "high": c.high, "low": c.low, "close": c.close}
            for c in candles
        ]
        store.write(state)

        logger.info(
            "forex_data_loaded",
            extra={"agent_id": ctx.agent_id, "event": "forex_data", "rows": len(candles)},
        )

