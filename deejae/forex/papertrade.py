"""
Paper-trade simulator — tracks open positions and running P&L without
touching a real brokerage account.
"""

from __future__ import annotations

from typing import Any


class PaperTrader:
    """
    Simulates order execution and tracks a virtual account balance.

    All prices are treated as mid-prices. Spread/commission modelling
    can be added once a live feed is integrated.
    """

    def __init__(self, initial_balance: float = 10_000.0) -> None:
        if initial_balance <= 0:
            raise ValueError("initial_balance must be positive")
        self.balance: float = initial_balance
        self.open_positions: list[dict[str, Any]] = []
        self.closed_trades: list[dict[str, Any]] = []

    # ------------------------------------------------------------------

    def execute(
        self,
        symbol: str,
        action: str,  # "buy" | "sell"
        size: float,
        price: float,
        stop_pips: float = 20,
        pip_value: float = 10.0,
    ) -> dict[str, Any]:
        """Open a new paper position and return a trade record."""
        if action not in ("buy", "sell"):
            raise ValueError(f"Unknown action: {action!r}")

        trade: dict[str, Any] = {
            "symbol": symbol,
            "action": action,
            "size": size,
            "entry_price": price,
            "stop_pips": stop_pips,
            "pip_value": pip_value,
            "pnl": 0.0,
            "status": "open",
        }
        self.open_positions.append(trade)
        return trade

    def close_position(self, index: int, exit_price: float) -> dict[str, Any]:
        """Close the position at *index* and update balance."""
        if index < 0 or index >= len(self.open_positions):
            raise IndexError(f"No open position at index {index}")

        pos = self.open_positions.pop(index)
        direction = 1 if pos["action"] == "buy" else -1
        price_diff = (exit_price - pos["entry_price"]) * direction
        pips = price_diff / 0.0001  # standard pip for 4-decimal pairs
        pnl = round(pips * pos["pip_value"] * pos["size"], 2)

        pos["exit_price"] = exit_price
        pos["pnl"] = pnl
        pos["status"] = "closed"

        self.balance = round(self.balance + pnl, 2)
        self.closed_trades.append(pos)
        return pos

    def summary(self) -> dict[str, Any]:
        """Return a snapshot of the current account state."""
        total_pnl = sum(t["pnl"] for t in self.closed_trades)
        return {
            "balance": self.balance,
            "open_positions": len(self.open_positions),
            "closed_trades": len(self.closed_trades),
            "total_realised_pnl": round(total_pnl, 2),
        }
