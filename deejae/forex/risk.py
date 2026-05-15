from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskPlan:
    risk_pct: float = 0.01  # 1% per trade
    equity: float = 10_000.0
    pip_value_per_unit: float = 0.0001  # simplified

    def units_for_stop(self, stop_pips: float) -> float:
        if stop_pips <= 0:
            return 0.0
        risk_amount = self.equity * self.risk_pct
        return risk_amount / (stop_pips * self.pip_value_per_unit)

