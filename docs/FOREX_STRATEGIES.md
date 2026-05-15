# Forex Strategies (MVP)

This repository includes a minimal forex signal loop intended for paper trading and strategy iteration.

## Included Strategies

Configured under `agents[].config.strategy` for `ForexStrategyAgent`:

- `ma_crossover`
  - Params: `fast_period`, `slow_period`
  - Signal: `long` when fast SMA > slow SMA, `short` when fast SMA < slow SMA

- `rsi_mean_reversion`
  - Params: `period`, `oversold`, `overbought`
  - Signal: `long` when RSI <= oversold, `short` when RSI >= overbought

## Risk Sizing

`ForexRiskAgent` uses:
- `equity` and `risk_pct` to set a fixed risk-per-trade budget
- `stop_pips` to compute a suggested unit size

This is a simplified model and must be adapted to your broker, contract size, and currency pair quote conventions.

