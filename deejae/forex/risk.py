"""
Forex risk management — position sizing and exposure limits.
"""

from __future__ import annotations


class RiskManager:
    """
    Calculates position size based on a fixed-risk-per-trade model.

    Parameters
    ----------
    max_risk_pct:
        Maximum percentage of account balance to risk per trade (e.g. 2.0 = 2 %).
    """

    def __init__(self, max_risk_pct: float = 2.0) -> None:
        if not (0 < max_risk_pct <= 100):
            raise ValueError("max_risk_pct must be between 0 and 100")
        self.max_risk_pct = max_risk_pct

    def position_size(
        self,
        balance: float,
        stop_pips: float,
        pip_value: float = 10.0,
    ) -> float:
        """
        Return position size in lots.

        Parameters
        ----------
        balance:    Current account balance in account currency.
        stop_pips:  Distance to stop-loss in pips.
        pip_value:  Value per pip per lot in account currency (default 10 USD).
        """
        if stop_pips <= 0 or pip_value <= 0:
            return 0.0
        risk_amount = balance * (self.max_risk_pct / 100)
        lots = risk_amount / (stop_pips * pip_value)
        return round(lots, 2)
