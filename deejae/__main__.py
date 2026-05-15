from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from deejae.config import load_config
from deejae.logging_setup import setup_logging
from deejae.runner import run_agents_once, run_agents_forever


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="deejae", description="DeeJae LeEtta agent runner")
    parser.add_argument(
        "--config",
        default=os.environ.get("DEEJAE_CONFIG", "examples/config.example.json"),
        help="Path to JSON config (or set DEEJAE_CONFIG).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run each enabled agent once and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    config_path = Path(args.config)
    config = load_config(config_path)
    setup_logging(config.log)
    if args.once:
        asyncio.run(run_agents_once(config))
    else:
        asyncio.run(run_agents_forever(config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

