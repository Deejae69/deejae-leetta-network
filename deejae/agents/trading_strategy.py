"""Trading Strategy Agent — wraps the forex strategy engine as an agent."""

from __future__ import annotations

from typing import Any

from deejae.agents.base import BaseAgent
from deejae.forex.strategy import MomentumStrategy
from deejae.forex.risk import RiskManager
from deejae.forex.papertrade import PaperTrader


class TradingStrategyAgent(BaseAgent):
    name = "trading_strategy"
    description = "Run forex momentum strategy with paper-trade simulation."

    def __init__(self, cfg: dict[str, Any]) -> None:
        super().__init__(cfg)
        forex_cfg = cfg.get("forex", {})
        self._strategy = MomentumStrategy()
        self._risk = RiskManager(
            max_risk_pct=forex_cfg.get("max_risk_pct", 2.0),
        )
        self._trader = PaperTrader(
            initial_balance=forex_cfg.get("initial_balance", 10_000.0),
        )

    def _run(self) -> dict[str, Any]:
        symbols: list[str] = self.cfg.get("forex", {}).get(
            "symbols", ["EURUSD", "GBPUSD", "USDJPY"]
        )
        results = []
        for symbol in symbols:
            signal = self._strategy.signal(symbol)
            if signal["action"] != "hold":
                size = self._risk.position_size(
                    balance=self._trader.balance,
                    stop_pips=signal.get("stop_pips", 20),
                    pip_value=signal.get("pip_value", 10.0),
                )
                trade = self._trader.execute(
                    symbol=symbol,
                    action=signal["action"],
                    size=size,
                    price=signal["price"],
                    stop_pips=signal.get("stop_pips", 20),
                )
                results.append(trade)
                self.log.info("Trade executed: %s", trade)

        return {
            "agent": self.name,
            "balance": self._trader.balance,
            "trades": results,
            "open_positions": len(self._trader.open_positions),
        }
