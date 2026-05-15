"""
Token "worth" calculator (math only).

This module does not predict markets. It only answers questions like:
"Given Bitcoin price and a target ratio (e.g. 30000x), what D33J market cap or
supply would be required for the D33J *per-token price* to meet that ratio?"
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from typing import Any, Dict, Optional


def btc_price_from_market_cap(btc_market_cap: float, btc_supply: float) -> float:
    _require_positive("btc_market_cap", btc_market_cap)
    _require_positive("btc_supply", btc_supply)
    return btc_market_cap / btc_supply


def target_token_price(btc_price: float, ratio: float) -> float:
    _require_positive("btc_price", btc_price)
    _require_positive("ratio", ratio)
    return btc_price * ratio


def market_cap_from_price_and_supply(price: float, supply: float) -> float:
    _require_positive_or_zero("supply", supply)
    _require_positive_or_zero("price", price)
    return price * supply


def supply_from_market_cap_and_price(market_cap: float, price: float) -> float:
    _require_positive_or_zero("market_cap", market_cap)
    _require_positive("price", price)
    return market_cap / price


def _require_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be > 0 (got {value})")


def _require_positive_or_zero(name: str, value: float) -> None:
    if value < 0:
        raise ValueError(f"{name} must be >= 0 (got {value})")


@dataclass(frozen=True)
class WorthResult:
    btc_price: float
    ratio: float
    target_d33j_price: float
    d33j_supply: Optional[float]
    d33j_market_cap: Optional[float]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "btc_price": self.btc_price,
            "ratio": self.ratio,
            "target_d33j_price": self.target_d33j_price,
            "d33j_supply": self.d33j_supply,
            "d33j_market_cap": self.d33j_market_cap,
        }


def calculate_worth(
    *,
    btc_price: float,
    ratio: float,
    d33j_supply: Optional[float] = None,
    d33j_market_cap: Optional[float] = None,
) -> WorthResult:
    """
    Calculate the required market cap or supply to hit a per-token price ratio.

    Exactly one of d33j_supply or d33j_market_cap must be provided.
    """
    if (d33j_supply is None) == (d33j_market_cap is None):
        raise ValueError("Provide exactly one of d33j_supply or d33j_market_cap")

    price_target = target_token_price(btc_price, ratio)

    if d33j_supply is not None:
        d33j_market_cap_out = market_cap_from_price_and_supply(price_target, d33j_supply)
        return WorthResult(
            btc_price=btc_price,
            ratio=ratio,
            target_d33j_price=price_target,
            d33j_supply=d33j_supply,
            d33j_market_cap=d33j_market_cap_out,
        )

    if d33j_market_cap is None:
        raise ValueError("d33j_market_cap must be provided when d33j_supply is not")
    d33j_supply_out = supply_from_market_cap_and_price(d33j_market_cap, price_target)
    return WorthResult(
        btc_price=btc_price,
        ratio=ratio,
        target_d33j_price=price_target,
        d33j_supply=d33j_supply_out,
        d33j_market_cap=d33j_market_cap,
    )


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute what supply/market-cap would be required for D33J to be X times Bitcoin per token.",
    )

    btc_group = parser.add_mutually_exclusive_group(required=True)
    btc_group.add_argument(
        "--btc-price",
        type=float,
        help="Bitcoin price (in USD or any unit you want to use consistently)",
    )
    btc_group.add_argument("--btc-market-cap", type=float, help="Bitcoin market cap (same unit as output market cap)")
    parser.add_argument(
        "--btc-supply",
        type=float,
        default=21_000_000,
        help="Bitcoin supply used with --btc-market-cap (default: 21,000,000)",
    )

    parser.add_argument("--ratio", type=float, default=30000, help="Target per-token price ratio (default: 30000)")

    d33j_group = parser.add_mutually_exclusive_group(required=True)
    d33j_group.add_argument("--d33j-supply", type=float, help="If provided, compute required D33J market cap")
    d33j_group.add_argument("--d33j-market-cap", type=float, help="If provided, compute required D33J supply")

    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    parser.add_argument("--precision", type=int, default=8, help="Decimal places for text output")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)

    if args.btc_price is not None:
        btc_price = float(args.btc_price)
    else:
        btc_price = btc_price_from_market_cap(float(args.btc_market_cap), float(args.btc_supply))

    result = calculate_worth(
        btc_price=btc_price,
        ratio=float(args.ratio),
        d33j_supply=args.d33j_supply,
        d33j_market_cap=args.d33j_market_cap,
    )

    if args.format == "json":
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
        return 0

    precision = max(int(args.precision), 0)
    fmt = f"{{:.{precision}f}}"
    print(f"btc_price={fmt.format(result.btc_price)}")
    print(f"ratio={fmt.format(result.ratio)}")
    print(f"target_d33j_price={fmt.format(result.target_d33j_price)}")
    if result.d33j_supply is not None:
        print(f"d33j_supply={fmt.format(result.d33j_supply)}")
    if result.d33j_market_cap is not None:
        print(f"d33j_market_cap={fmt.format(result.d33j_market_cap)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
