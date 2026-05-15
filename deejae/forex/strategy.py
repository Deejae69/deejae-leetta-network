from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from deejae.forex.indicators import rsi, sma
from deejae.forex.types import Candle

Signal = Literal["long", "short", "flat"]


class Strategy:
    def signal(self, candles: list[Candle]) -> Signal:  # pragma: no cover (interface)
        raise NotImplementedError


@dataclass(frozen=True)
class MovingAverageCrossoverStrategy(Strategy):
    fast_period: int = 10
    slow_period: int = 30

    def signal(self, candles: list[Candle]) -> Signal:
        closes = [c.close for c in candles]
        fast = sma(closes, self.fast_period)
        slow = sma(closes, self.slow_period)
        if fast is None or slow is None:
            return "flat"
        if fast > slow:
            return "long"
        if fast < slow:
            return "short"
        return "flat"


@dataclass(frozen=True)
class RsiMeanReversionStrategy(Strategy):
    period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0

    def signal(self, candles: list[Candle]) -> Signal:
        closes = [c.close for c in candles]
        value = rsi(closes, self.period)
        if value is None:
            return "flat"
        if value <= self.oversold:
            return "long"
        if value >= self.overbought:
            return "short"
        return "flat"


def strategy_from_config(config: dict) -> Strategy:
    name = str(config.get("name") or "ma_crossover").lower()
    params = config.get("params") or {}
    if name in {"ma", "ma_crossover", "moving_average_crossover"}:
        return MovingAverageCrossoverStrategy(
            fast_period=int(params.get("fast_period", 10)),
            slow_period=int(params.get("slow_period", 30)),
        )
    if name in {"rsi", "rsi_mean_reversion"}:
        return RsiMeanReversionStrategy(
            period=int(params.get("period", 14)),
            oversold=float(params.get("oversold", 30.0)),
            overbought=float(params.get("overbought", 70.0)),
        )
    raise ValueError(f"Unknown strategy: {name}")

