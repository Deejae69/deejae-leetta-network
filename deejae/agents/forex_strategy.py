from __future__ import annotations

import logging
from datetime import datetime

from deejae.forex.strategy import strategy_from_config
from deejae.forex.types import Candle
from deejae.runner import Agent, AgentContext
from deejae.state import store_from_config

logger = logging.getLogger(__name__)


class ForexStrategyAgent(Agent):
    async def run_once(self, ctx: AgentContext) -> None:
        store = store_from_config(ctx.config)
        state = store.read()
        candles_raw = (((state.get("forex") or {}).get("candles")) or [])
        candles = [
            Candle(
                ts=datetime.fromisoformat(str(item["ts"]).replace("Z", "+00:00")),
                open=float(item["open"]),
                high=float(item["high"]),
                low=float(item["low"]),
                close=float(item["close"]),
            )
            for item in candles_raw
        ]
        if not candles:
            logger.warning("no_candles_available", extra={"agent_id": ctx.agent_id, "event": "forex_strategy"})
            return

        strategy = strategy_from_config(ctx.config.get("strategy") or {})
        signal = strategy.signal(candles)

        state["forex"] = state.get("forex", {})
        state["forex"]["signal"] = {"value": signal, "ts": candles[-1].ts.isoformat()}
        store.write(state)

        symbol = str(ctx.config.get("symbol") or "EURUSD")
        logger.info(
            "signal_generated",
            extra={"agent_id": ctx.agent_id, "event": "forex_strategy", "symbol": symbol, "signal": signal},
        )
        await ctx.webhooks.send_event(
            event="forex_signal",
            title=f"FX signal {symbol}: {signal}",
            body=f"ts={candles[-1].ts.isoformat()}",
            agent_id=ctx.agent_id,
            extra={"symbol": symbol, "signal": signal},
        )
