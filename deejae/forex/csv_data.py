from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from deejae.forex.types import Candle


_TS_COLUMNS = ("ts", "timestamp", "time", "date", "datetime")
_OPEN_COLUMNS = ("open", "o")
_HIGH_COLUMNS = ("high", "h")
_LOW_COLUMNS = ("low", "l")
_CLOSE_COLUMNS = ("close", "c")


def _pick(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for key in keys:
        if key in row and row[key] != "":
            return row[key]
    raise KeyError(f"Missing required column: one of {keys}")


def _parse_ts(raw: str) -> datetime:
    raw = raw.strip()
    try:
        # ISO 8601
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        # fallback: unix seconds
        ts = datetime.fromtimestamp(float(raw), tz=timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def load_candles_csv(path: Path, *, limit: int | None = None) -> list[Candle]:
    candles: list[Candle] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV must include a header row")
        for row in reader:
            normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items()}
            candle = Candle(
                ts=_parse_ts(_pick(normalized, _TS_COLUMNS)),
                open=float(_pick(normalized, _OPEN_COLUMNS)),
                high=float(_pick(normalized, _HIGH_COLUMNS)),
                low=float(_pick(normalized, _LOW_COLUMNS)),
                close=float(_pick(normalized, _CLOSE_COLUMNS)),
            )
            candles.append(candle)
            if limit is not None and len(candles) >= limit:
                break
    candles.sort(key=lambda c: c.ts)
    return candles
