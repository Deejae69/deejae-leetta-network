"""
CLI definition for the DeeJae LeEtta Network.

Usage examples
--------------
  python -m deejae --help
  python -m deejae run --agent all
  python -m deejae run --agent mmo_customer
  python -m deejae forex --summary
  python -m deejae status
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

import deejae.config as config_mod
from deejae import __version__
from deejae.agents import REGISTRY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_run(args: argparse.Namespace, cfg: dict) -> int:
    """Run one or all agents for a single cycle."""
    enabled: list[str] = cfg["agents"]["enabled"]
    targets: list[str]

    if args.agent == "all":
        targets = enabled
    elif args.agent in REGISTRY:
        targets = [args.agent]
    else:
        print(
            f"Unknown agent: {args.agent!r}. "
            f"Available: {', '.join(REGISTRY)} or 'all'",
            file=sys.stderr,
        )
        return 1

    results = {}
    for name in targets:
        if name not in REGISTRY:
            logging.getLogger("deejae.cli").warning("Agent %r not found, skipping", name)
            continue
        agent = REGISTRY[name](cfg)
        results[name] = agent.run()

    _print_json(results)
    return 0


def cmd_forex(args: argparse.Namespace, cfg: dict) -> int:
    """Run the forex paper-trade engine once."""
    from deejae.agents.trading_strategy import TradingStrategyAgent

    agent = TradingStrategyAgent(cfg)
    result = agent.run()

    if args.summary:
        _print_json(agent._trader.summary())
    else:
        _print_json(result)
    return 0


def cmd_status(_args: argparse.Namespace, cfg: dict) -> int:
    """Print current configuration and available agents."""
    info = {
        "version": __version__,
        "network": cfg["network"],
        "log_level": cfg["log_level"],
        "agents_enabled": cfg["agents"]["enabled"],
        "forex_paper_trade": cfg["forex"]["paper_trade"],
        "forex_symbols": cfg["forex"]["symbols"],
    }
    _print_json(info)
    return 0


def cmd_tickblaze(args: argparse.Namespace, cfg: dict) -> int:
    """Test Tickblaze API connectivity/auth."""
    from deejae.tickblaze import test_connection

    tb_cfg = cfg.get("tickblaze", {})
    base_url = args.base_url or tb_cfg.get("base_url") or ""
    path = args.path or tb_cfg.get("ping_path") or "/"
    api_key = args.api_key or tb_cfg.get("api_key") or ""
    auth_header = args.auth_header or tb_cfg.get("auth_header") or "Authorization"
    auth_prefix = args.auth_prefix or tb_cfg.get("auth_prefix") or "Bearer"
    timeout_seconds = args.timeout_seconds
    if timeout_seconds is None:
        timeout_seconds = tb_cfg.get("timeout_seconds", 10.0)

    if not base_url:
        print(
            "Missing Tickblaze base URL. Set --base-url or DEEJAE_TICKBLAZE_BASE_URL.",
            file=sys.stderr,
        )
        return 1

    result = test_connection(
        base_url=base_url,
        path=path,
        api_key=api_key,
        auth_header=auth_header,
        auth_prefix=auth_prefix,
        timeout_seconds=float(timeout_seconds),
        show_body=bool(args.show_body),
    )
    _print_json(result)

    if not result.get("reachable", False):
        return 1
    if api_key and result.get("auth_ok") is False:
        return 2
    status = result.get("status_code")
    if isinstance(status, int) and status >= 500:
        return 3
    return 0


# ---------------------------------------------------------------------------
# Parser factory
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m deejae",
        description="DeeJae LeEtta Network — autonomous agent runner",
    )
    parser.add_argument(
        "--version", action="version", version=f"deejae {__version__}"
    )
    parser.add_argument(
        "--config",
        default=None,
        metavar="PATH",
        help="Path to JSON config file (default: config.json or $DEEJAE_CONFIG)",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level",
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # --- run ---
    run_p = sub.add_parser("run", help="Run one or all agents for a single cycle")
    run_p.add_argument(
        "--agent",
        default="all",
        metavar="NAME",
        help=f"Agent name or 'all'. Choices: {', '.join(REGISTRY)}, all",
    )

    # --- forex ---
    forex_p = sub.add_parser("forex", help="Execute the forex paper-trade engine")
    forex_p.add_argument(
        "--summary",
        action="store_true",
        help="Print account summary after the cycle",
    )

    # --- status ---
    sub.add_parser("status", help="Show current configuration and agent list")

    # --- tickblaze ---
    tick_p = sub.add_parser("tickblaze", help="Test Tickblaze API connectivity")
    tick_p.add_argument(
        "--base-url",
        default=None,
        metavar="URL",
        help="Tickblaze API base URL (or $DEEJAE_TICKBLAZE_BASE_URL)",
    )
    tick_p.add_argument(
        "--path",
        default=None,
        metavar="PATH",
        help="GET path to request (default: config tickblaze.ping_path or '/')",
    )
    tick_p.add_argument(
        "--api-key",
        default=None,
        metavar="TOKEN",
        help="API key/token (or $DEEJAE_TICKBLAZE_API_KEY)",
    )
    tick_p.add_argument(
        "--auth-header",
        default=None,
        metavar="NAME",
        help="Auth header name (default: Authorization or config tickblaze.auth_header)",
    )
    tick_p.add_argument(
        "--auth-prefix",
        default=None,
        metavar="PREFIX",
        help="Auth prefix before token (default: Bearer or config tickblaze.auth_prefix; set \"\" for none)",
    )
    tick_p.add_argument(
        "--timeout-seconds",
        type=float,
        default=None,
        metavar="N",
        help="Request timeout in seconds (default: config tickblaze.timeout_seconds or 10)",
    )
    tick_p.add_argument(
        "--show-body",
        action="store_true",
        help="Include up to 16KB of response body in output",
    )

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cfg = config_mod.load(args.config)

    # CLI --log-level overrides config file value
    log_level = (args.log_level or cfg["log_level"]).upper()
    _setup_logging(log_level)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "run": cmd_run,
        "forex": cmd_forex,
        "status": cmd_status,
        "tickblaze": cmd_tickblaze,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args, cfg)
