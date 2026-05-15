"""
Forex strategy module — generates buy/hold/sell signals.

This is an MVP stub that returns randomised signals so the rest of the
pipeline can be developed and tested end-to-end before live data feeds
are integrated.
"""

from __future__ import annotations

import random
from typing import Any


class MomentumStrategy:
    """
    Simple momentum strategy stub.

    In a production integration this class would:
    - Fetch OHLCV data from a broker / exchange API
    - Compute a short-term vs. long-term EMA crossover
    - Return a structured signal dict

    For now it returns a randomised signal so the full trade pipeline
    can be exercised in tests and paper-trade mode.
    """

    def __init__(self, short_period: int = 9, long_period: int = 21) -> None:
        self.short_period = short_period
        self.long_period = long_period

    def signal(self, symbol: str) -> dict[str, Any]:
        """Return a signal dict for *symbol*."""
        # Stub: randomly pick an action with a realistic distribution
        action = random.choices(
            ["buy", "sell", "hold"],
            weights=[0.25, 0.25, 0.50],
        )[0]

        # Stub mid-price — replace with live feed
        price = round(random.uniform(1.05, 1.40), 5)

        return {
            "symbol": symbol,
            "action": action,
            "price": price,
            "stop_pips": 20,
            "pip_value": 10.0,
        }
