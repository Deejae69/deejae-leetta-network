from __future__ import annotations

import logging

from deejae.forex.risk import RiskPlan
from deejae.runner import Agent, AgentContext
from deejae.state import store_from_config

logger = logging.getLogger(__name__)


class ForexRiskAgent(Agent):
    async def run_once(self, ctx: AgentContext) -> None:
        store = store_from_config(ctx.config)
        state = store.read()
        forex_state = state.get("forex") or {}
        signal = (forex_state.get("signal") or {}).get("value") or "flat"

        stop_pips = float(ctx.config.get("stop_pips", 25))
        plan = RiskPlan(
            risk_pct=float(ctx.config.get("risk_pct", 0.01)),
            equity=float(ctx.config.get("equity", 10_000.0)),
            pip_value_per_unit=float(ctx.config.get("pip_value_per_unit", 0.0001)),
        )
        units = plan.units_for_stop(stop_pips) if signal != "flat" else 0.0

        forex_state["risk"] = {"stop_pips": stop_pips, "units": units}
        state["forex"] = forex_state
        store.write(state)

        logger.info(
            "risk_plan_updated",
            extra={"agent_id": ctx.agent_id, "event": "forex_risk", "signal": signal, "units": units},
        )

