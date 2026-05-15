from __future__ import annotations

import logging

from deejae.runner import Agent, AgentContext
from deejae.state import store_from_config

logger = logging.getLogger(__name__)


class ForexPaperTradeAgent(Agent):
    async def run_once(self, ctx: AgentContext) -> None:
        store = store_from_config(ctx.config)
        state = store.read()
        forex_state = state.get("forex") or {}
        signal = (forex_state.get("signal") or {}).get("value") or "flat"
        risk = forex_state.get("risk") or {}
        units = float(risk.get("units") or 0.0)

        portfolio = forex_state.get("paper") or {"position": "flat", "units": 0.0, "trades": 0}
        position = portfolio.get("position") or "flat"

        # Minimal "paper trade" state machine: enter on non-flat signal, exit on flat or opposite.
        desired = signal
        changed = False
        if desired == "flat" and position != "flat":
            portfolio["position"] = "flat"
            portfolio["units"] = 0.0
            portfolio["trades"] = int(portfolio.get("trades", 0)) + 1
            changed = True
        elif desired in {"long", "short"} and desired != position:
            portfolio["position"] = desired
            portfolio["units"] = units
            portfolio["trades"] = int(portfolio.get("trades", 0)) + 1
            changed = True

        forex_state["paper"] = portfolio
        state["forex"] = forex_state
        store.write(state)

        if changed:
            logger.info(
                "paper_trade_updated",
                extra={"agent_id": ctx.agent_id, "event": "forex_papertrade", "position": portfolio["position"]},
            )

