from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from deejae.forex.risk import RiskPlan
from deejae.forex.strategy import MovingAverageCrossoverStrategy, RsiMeanReversionStrategy
from deejae.forex.types import Candle
from deejae.state import StateStore


class TestForexStrategy(unittest.TestCase):
    def test_ma_crossover_generates_long(self) -> None:
        candles = []
        for i, close in enumerate([1, 2, 3, 4, 5, 6], start=1):
            ts = datetime(2026, 5, 14, 0, i, tzinfo=timezone.utc)
            candles.append(Candle(ts=ts, open=close, high=close, low=close, close=float(close)))
        strat = MovingAverageCrossoverStrategy(fast_period=2, slow_period=4)
        self.assertEqual(strat.signal(candles), "long")

    def test_rsi_mean_reversion_overbought_is_short(self) -> None:
        # Rising closes -> high RSI -> short.
        candles = []
        for i in range(20):
            close = 1.0 + (i * 0.01)
            ts = datetime(2026, 5, 14, 0, i, tzinfo=timezone.utc)
            candles.append(Candle(ts=ts, open=close, high=close, low=close, close=close))
        strat = RsiMeanReversionStrategy(period=14, oversold=30, overbought=60)
        self.assertEqual(strat.signal(candles), "short")


class TestRisk(unittest.TestCase):
    def test_units_for_stop(self) -> None:
        plan = RiskPlan(risk_pct=0.01, equity=10_000, pip_value_per_unit=0.0001)
        units = plan.units_for_stop(25)
        self.assertAlmostEqual(units, 40_000.0)


class TestStateStore(unittest.TestCase):
    def test_read_write_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            store = StateStore(path=path)
            store.write({"a": 1})
            self.assertEqual(store.read()["a"], 1)


if __name__ == "__main__":
    unittest.main()

