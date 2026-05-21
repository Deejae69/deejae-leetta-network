"""
Tests for the webhook handler (api/webhook_handler.py).

Covers: health check, verify_signature helper, and the three webhook
endpoints (github, trading, campaign) with a variety of payloads.
"""

import hashlib
import hmac
import json
import os
import unittest


def _make_client(webhook_secret: str = ""):
    """Return a Flask test client backed by the webhook handler app."""
    os.environ["WEBHOOK_SECRET"] = webhook_secret
    os.environ["WEBHOOK_PORT"] = "8080"

    # Reload settings so the module picks up the new env vars
    import importlib
    import config.settings as settings_mod
    importlib.reload(settings_mod)

    import api.webhook_handler as wh_mod
    importlib.reload(wh_mod)

    wh_mod.app.config["TESTING"] = True
    return wh_mod.app.test_client()


def _make_wh():
    """Return the reloaded webhook_handler module (for helper function access)."""
    os.environ["WEBHOOK_SECRET"] = "test-wh-secret"
    import importlib
    import config.settings as settings_mod
    importlib.reload(settings_mod)
    import api.webhook_handler as wh_mod
    importlib.reload(wh_mod)
    return wh_mod


def _sign(secret: str, body: bytes) -> str:
    """Generate an HMAC-SHA256 signature header value."""
    mac = hmac.new(secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256)
    return "sha256=" + mac.hexdigest()


class TestHealthCheck(unittest.TestCase):
    def setUp(self):
        self.client = _make_client()

    def test_health_returns_200(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)

    def test_health_body(self):
        data = self.client.get("/health").get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("DeeJae", data["service"])


class TestVerifySignature(unittest.TestCase):
    def setUp(self):
        self.wh = _make_wh()
        os.environ["WEBHOOK_SECRET"] = "test-secret"
        import importlib, config.settings as s
        importlib.reload(s)
        importlib.reload(self.wh)

    def test_valid_signature_accepted(self):
        payload = b'{"foo": "bar"}'
        sig = _sign("test-secret", payload)
        self.assertTrue(self.wh.verify_signature(payload, sig))

    def test_invalid_signature_rejected(self):
        payload = b'{"foo": "bar"}'
        self.assertFalse(self.wh.verify_signature(payload, "sha256=badhex"))

    def test_no_secret_always_returns_true(self):
        import importlib, config.settings as s
        os.environ["WEBHOOK_SECRET"] = ""
        importlib.reload(s)
        importlib.reload(self.wh)
        self.assertTrue(self.wh.verify_signature(b"anything", ""))


class TestGitHubWebhook(unittest.TestCase):
    def setUp(self):
        self.secret = "gh-secret"
        self.client = _make_client(webhook_secret=self.secret)

    def _post(self, payload: dict, event: str = "push"):
        body = json.dumps(payload).encode()
        sig = _sign(self.secret, body)
        return self.client.post(
            "/webhook/github",
            data=body,
            content_type="application/json",
            headers={
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": event,
            },
        )

    def test_push_event_returns_200(self):
        resp = self._post(
            {"repository": {"full_name": "org/repo"}, "ref": "refs/heads/main", "commits": []},
            event="push",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["event"], "push")

    def test_pull_request_event_returns_200(self):
        resp = self._post(
            {"action": "opened", "pull_request": {"number": 42}},
            event="pull_request",
        )
        self.assertEqual(resp.status_code, 200)

    def test_issues_event_returns_200(self):
        resp = self._post(
            {"action": "opened", "issue": {"number": 1}},
            event="issues",
        )
        self.assertEqual(resp.status_code, 200)

    def test_workflow_run_event_returns_200(self):
        resp = self._post(
            {"workflow": {"name": "CI"}, "workflow_run": {"conclusion": "success"}},
            event="workflow_run",
        )
        self.assertEqual(resp.status_code, 200)

    def test_unknown_event_returns_200(self):
        resp = self._post({}, event="star")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "processed")

    def test_invalid_signature_returns_403(self):
        body = json.dumps({"ref": "main"}).encode()
        resp = self.client.post(
            "/webhook/github",
            data=body,
            content_type="application/json",
            headers={
                "X-Hub-Signature-256": "sha256=badsignature",
                "X-GitHub-Event": "push",
            },
        )
        self.assertEqual(resp.status_code, 403)


class TestGitHubWebhookNoSecret(unittest.TestCase):
    """When WEBHOOK_SECRET is unset signature verification is skipped."""

    def setUp(self):
        self.client = _make_client(webhook_secret="")

    def test_no_signature_header_still_processed(self):
        body = json.dumps({"ref": "refs/heads/main", "commits": []}).encode()
        resp = self.client.post(
            "/webhook/github",
            data=body,
            content_type="application/json",
            headers={"X-GitHub-Event": "push"},
        )
        self.assertEqual(resp.status_code, 200)


class TestTradingWebhook(unittest.TestCase):
    def setUp(self):
        self.client = _make_client()

    def _post(self, payload):
        return self.client.post(
            "/webhook/trading",
            json=payload,
        )

    def test_buy_signal_returns_200(self):
        resp = self._post({"signal_type": "buy", "symbol": "BTC", "price": 50000})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "processed")

    def test_sell_signal_returns_200(self):
        resp = self._post({"signal_type": "sell", "symbol": "ETH", "price": 3000})
        self.assertEqual(resp.status_code, 200)

    def test_market_update_returns_200(self):
        resp = self._post({"signal_type": "market_update", "data": {}})
        self.assertEqual(resp.status_code, 200)

    def test_unknown_signal_returns_200(self):
        resp = self._post({"signal_type": "unknown_type"})
        self.assertEqual(resp.status_code, 200)

    def test_no_payload_returns_400(self):
        # Sending an empty JSON body evaluates to None/empty, triggering 400
        resp = self.client.post(
            "/webhook/trading",
            data="null",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class TestCampaignWebhook(unittest.TestCase):
    def setUp(self):
        self.client = _make_client()

    def _post(self, payload):
        return self.client.post("/webhook/campaign", json=payload)

    def test_signup_event_returns_200(self):
        resp = self._post({"event_type": "signup", "source": "twitter"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "tracked")

    def test_purchase_event_returns_200(self):
        resp = self._post({"event_type": "purchase", "amount": 99.99, "source": "instagram"})
        self.assertEqual(resp.status_code, 200)

    def test_conversion_event_returns_200(self):
        resp = self._post({"event_type": "conversion", "type": "lead", "source": "organic"})
        self.assertEqual(resp.status_code, 200)

    def test_unknown_event_returns_200(self):
        resp = self._post({"event_type": "unknown"})
        self.assertEqual(resp.status_code, 200)

    def test_no_payload_returns_400(self):
        # Sending a null JSON body evaluates to None, triggering 400
        resp = self.client.post(
            "/webhook/campaign",
            data="null",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
