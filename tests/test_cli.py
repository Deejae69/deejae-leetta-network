"""Tests for the DeeJae LeEtta Network CLI and core modules."""

from __future__ import annotations

import sys
import types
import unittest
from unittest import mock


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestConfig(unittest.TestCase):
    def test_defaults_loaded(self):
        import deejae.config as cfg_mod
        cfg = cfg_mod.load("/nonexistent/path/config.json")
        self.assertEqual(cfg["network"], "mainnet")
        self.assertIn("forex", cfg)
        self.assertIn("agents", cfg)

    def test_env_override(self):
        import os, deejae.config as cfg_mod
        os.environ["DEEJAE_LOG_LEVEL"] = "DEBUG"
        os.environ["DEEJAE_NETWORK"] = "testnet"
        try:
            cfg = cfg_mod.load("/nonexistent/path/config.json")
            self.assertEqual(cfg["log_level"], "DEBUG")
            self.assertEqual(cfg["network"], "testnet")
        finally:
            os.environ.pop("DEEJAE_LOG_LEVEL", None)
            os.environ.pop("DEEJAE_NETWORK", None)


# ---------------------------------------------------------------------------
# Risk Manager
# ---------------------------------------------------------------------------

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        from deejae.forex.risk import RiskManager
        self.rm = RiskManager(max_risk_pct=2.0)

    def test_position_size_basic(self):
        size = self.rm.position_size(balance=10_000, stop_pips=20, pip_value=10.0)
        # risk = 200, stop_cost = 200 → 1.0 lot
        self.assertAlmostEqual(size, 1.0, places=2)

    def test_position_size_zero_stop(self):
        self.assertEqual(self.rm.position_size(10_000, stop_pips=0), 0.0)

    def test_invalid_risk_pct(self):
        from deejae.forex.risk import RiskManager
        with self.assertRaises(ValueError):
            RiskManager(max_risk_pct=0)
        with self.assertRaises(ValueError):
            RiskManager(max_risk_pct=101)


# ---------------------------------------------------------------------------
# Paper Trader
# ---------------------------------------------------------------------------

class TestPaperTrader(unittest.TestCase):
    def setUp(self):
        from deejae.forex.papertrade import PaperTrader
        self.trader = PaperTrader(initial_balance=10_000.0)

    def test_initial_balance(self):
        self.assertEqual(self.trader.balance, 10_000.0)

    def test_execute_opens_position(self):
        trade = self.trader.execute("EURUSD", "buy", 1.0, 1.10000)
        self.assertEqual(len(self.trader.open_positions), 1)
        self.assertEqual(trade["status"], "open")

    def test_close_position_updates_balance(self):
        self.trader.execute("EURUSD", "buy", 1.0, 1.10000)
        closed = self.trader.close_position(0, exit_price=1.10200)  # +20 pips
        self.assertEqual(closed["status"], "closed")
        self.assertAlmostEqual(closed["pnl"], 200.0, places=1)
        self.assertAlmostEqual(self.trader.balance, 10_200.0, places=1)

    def test_invalid_action(self):
        with self.assertRaises(ValueError):
            self.trader.execute("EURUSD", "hold", 1.0, 1.1)

    def test_invalid_balance(self):
        from deejae.forex.papertrade import PaperTrader
        with self.assertRaises(ValueError):
            PaperTrader(initial_balance=0)

    def test_summary(self):
        summary = self.trader.summary()
        self.assertIn("balance", summary)
        self.assertIn("open_positions", summary)


# ---------------------------------------------------------------------------
# Momentum Strategy stub
# ---------------------------------------------------------------------------

class TestMomentumStrategy(unittest.TestCase):
    def test_signal_structure(self):
        from deejae.forex.strategy import MomentumStrategy
        strat = MomentumStrategy()
        sig = strat.signal("EURUSD")
        self.assertIn(sig["action"], ("buy", "sell", "hold"))
        self.assertEqual(sig["symbol"], "EURUSD")
        self.assertIn("price", sig)


# ---------------------------------------------------------------------------
# Campaign Optimizer (UCB1 bandit)
# ---------------------------------------------------------------------------

class TestCampaignOptimizer(unittest.TestCase):
    def _make_agent(self):
        from deejae.agents.campaign_optimizer import CampaignOptimizerAgent
        import deejae.config as cfg_mod
        cfg = cfg_mod.load("/nonexistent/path/config.json")
        return CampaignOptimizerAgent(cfg)

    def test_run_returns_top_channel(self):
        agent = self._make_agent()
        result = agent.run()
        self.assertIn("top_channel", result)
        self.assertIn(result["top_channel"], agent._CHANNELS)

    def test_record_outcome_updates_state(self):
        agent = self._make_agent()
        # Give every channel many low-reward trials to bound their exploration term
        for ch in agent._CHANNELS:
            for _ in range(100):
                agent.record_outcome(ch, 0.0)
        # Give twitter many wins so its exploitation term dominates
        for _ in range(200):
            agent.record_outcome("twitter", 1.0)
        result = agent.run()
        self.assertEqual(result["top_channel"], "twitter")


# ---------------------------------------------------------------------------
# CLI integration smoke test
# ---------------------------------------------------------------------------

class TestCLI(unittest.TestCase):
    def _run(self, *args):
        from deejae.cli import main
        return main(list(args))

    def test_status(self):
        rc = self._run("status")
        self.assertEqual(rc, 0)

    def test_run_all(self):
        rc = self._run("run", "--agent", "all")
        self.assertEqual(rc, 0)

    def test_run_single_agent(self):
        rc = self._run("run", "--agent", "mmo_customer")
        self.assertEqual(rc, 0)

    def test_run_unknown_agent(self):
        rc = self._run("run", "--agent", "nonexistent_agent")
        self.assertEqual(rc, 1)

    def test_forex(self):
        rc = self._run("forex")
        self.assertEqual(rc, 0)

    def test_forex_summary(self):
        rc = self._run("forex", "--summary")
        self.assertEqual(rc, 0)

    def test_no_subcommand_prints_help(self):
        rc = self._run()
        self.assertEqual(rc, 0)

    def test_tickblaze_requires_base_url(self):
        rc = self._run("tickblaze")
        self.assertEqual(rc, 1)

    def test_tickblaze_success(self):
        class _Headers:
            def __init__(self, d):
                self._d = d

            def items(self):
                return list(self._d.items())

            def get(self, key, default=None):
                return self._d.get(key, default)

        class _Resp:
            def __init__(self, status, body=b"{}", headers=None):
                self.status = status
                self._body = body
                self.headers = _Headers(headers or {"Content-Type": "application/json"})

            def getcode(self):
                return self.status

            def read(self, _n=-1):
                return self._body

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        with mock.patch(
            "deejae.tickblaze.urllib.request.urlopen",
            return_value=_Resp(200, b"{\"ok\":true}"),
        ):
            rc = self._run(
                "tickblaze", "--base-url", "https://example.com", "--path", "/ping"
            )
            self.assertEqual(rc, 0)

    def test_tickblaze_auth_failure_exit_code(self):
        import io
        import urllib.error

        err = urllib.error.HTTPError(
            url="https://example.com/ping",
            code=401,
            msg="Unauthorized",
            hdrs={"Content-Type": "text/plain"},
            fp=io.BytesIO(b"unauthorized"),
        )
        with mock.patch("deejae.tickblaze.urllib.request.urlopen", side_effect=err):
            rc = self._run(
                "tickblaze",
                "--base-url",
                "https://example.com",
                "--path",
                "/ping",
                "--api-key",
                "secret",
            )
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
