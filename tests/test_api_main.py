"""Tests for top-level API routes in api.main."""

import unittest
from unittest.mock import patch

import api.main as main_api


class BrokenContext:
    """Context manager that raises on enter to trigger endpoint error handlers."""

    def __init__(self, *_args, **_kwargs):
        pass

    def __enter__(self):
        raise RuntimeError("boom")

    def __exit__(self, exc_type, exc, tb):
        return False


class TestApiMainEndpoints(unittest.TestCase):
    def setUp(self):
        main_api.app.config["TESTING"] = True
        self.client = main_api.app.test_client()

    def test_health(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_agents(self):
        resp = self.client.get("/api/agents")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data["agents"]), 6)

    def test_campaigns(self):
        resp = self.client.get("/api/campaigns")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("total_revenue", data)

    def test_trading_status(self):
        resp = self.client.get("/api/trading/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("portfolio_value", data)

    def test_trading_signals(self):
        resp = self.client.get("/api/trading/signals")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["signals"], [])

    def test_metrics(self):
        resp = self.client.get("/api/metrics")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["active_agents"], 6)

    def test_agents_internal_error(self):
        with patch("api.main.ErrorContext", BrokenContext):
            resp = self.client.get("/api/agents")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["error"], "Internal error")

    def test_campaigns_internal_error(self):
        with patch("api.main.ErrorContext", BrokenContext):
            resp = self.client.get("/api/campaigns")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["error"], "Internal error")

    def test_trading_status_internal_error(self):
        with patch("api.main.ErrorContext", BrokenContext):
            resp = self.client.get("/api/trading/status")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["error"], "Internal error")

    def test_trading_signals_internal_error(self):
        with patch("api.main.ErrorContext", BrokenContext):
            resp = self.client.get("/api/trading/signals")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["error"], "Internal error")

    def test_metrics_internal_error(self):
        with patch("api.main.ErrorContext", BrokenContext):
            resp = self.client.get("/api/metrics")
        self.assertEqual(resp.status_code, 500)
        self.assertEqual(resp.get_json()["error"], "Internal error")


if __name__ == "__main__":
    unittest.main()
