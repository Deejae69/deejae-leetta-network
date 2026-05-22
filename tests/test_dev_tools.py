"""
Tests for the developer tools blueprint (api/dev_tools.py).
"""

import importlib
import os
import unittest


def _make_dev_app(environment: str = "development"):
    """Return a Flask test app with dev_bp registered."""
    env = {
        "JWT_SECRET_KEY": "test-dev-secret-key-at-least-32-chars-long",
        "JWT_ACCESS_TOKEN_EXPIRES": "3600",
        "ENVIRONMENT": environment,
    }
    for k, v in env.items():
        os.environ[k] = v

    import config.settings as settings_mod
    importlib.reload(settings_mod)
    import api.auth as auth_mod
    importlib.reload(auth_mod)
    import api.audit_log as audit_mod
    importlib.reload(audit_mod)
    import api.dev_tools as dev_mod
    importlib.reload(dev_mod)
    dev_mod._debug_log_buffer.clear()

    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True

    # Register a minimal health endpoint so /api/health is simulatable
    @app.route("/api/health")
    def health():
        from flask import jsonify
        return jsonify({"status": "healthy"}), 200

    app.register_blueprint(dev_mod.dev_bp)
    return app, auth_mod, dev_mod


class TestDevPing(unittest.TestCase):
    def test_ping_development(self):
        app, _, _ = _make_dev_app("development")
        client = app.test_client()
        resp = client.get("/dev/ping")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["environment"], "development")

    def test_ping_staging(self):
        app, _, _ = _make_dev_app("staging")
        client = app.test_client()
        resp = client.get("/dev/ping")
        self.assertEqual(resp.status_code, 200)

    def test_ping_production_blocked(self):
        app, _, _ = _make_dev_app("production")
        client = app.test_client()
        resp = client.get("/dev/ping")
        self.assertEqual(resp.status_code, 403)


class TestDevConfig(unittest.TestCase):
    def setUp(self):
        self.app, self.auth, _ = _make_dev_app("development")
        self.client = self.app.test_client()

    def _dev_token(self):
        return self.auth.create_access_token("devuser", "developer")

    def _admin_token(self):
        return self.auth.create_access_token("adminuser", "admin")

    def _viewer_token(self):
        return self.auth.create_access_token("viewuser", "viewer")

    def test_no_auth_returns_401(self):
        resp = self.client.get("/dev/config")
        self.assertEqual(resp.status_code, 401)

    def test_viewer_denied(self):
        resp = self.client.get(
            "/dev/config",
            headers={"Authorization": f"Bearer {self._viewer_token()}"},
        )
        self.assertEqual(resp.status_code, 403)

    def test_developer_allowed(self):
        resp = self.client.get(
            "/dev/config",
            headers={"Authorization": f"Bearer {self._dev_token()}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["environment"], "development")
        self.assertIn("config", data)

    def test_admin_allowed(self):
        resp = self.client.get(
            "/dev/config",
            headers={"Authorization": f"Bearer {self._admin_token()}"},
        )
        self.assertEqual(resp.status_code, 200)

    def test_sensitive_values_redacted(self):
        os.environ["JWT_SECRET_KEY"] = "test-dev-secret-key-at-least-32-chars-long"
        os.environ["OPENAI_API_KEY"] = "sk-real-key"
        os.environ["LOG_LEVEL"] = "INFO"
        resp = self.client.get(
            "/dev/config",
            headers={"Authorization": f"Bearer {self._dev_token()}"},
        )
        config = resp.get_json().get("config", {})
        # JWT_SECRET_KEY is not in the exposed prefix list so it won't appear
        self.assertNotIn("super-secret", str(config))
        # OPENAI_API_KEY should be redacted or absent
        if "OPENAI_API_KEY" in config:
            self.assertEqual(config["OPENAI_API_KEY"], "**REDACTED**")

    def test_production_blocked(self):
        prod_app, auth, _ = _make_dev_app("production")
        client = prod_app.test_client()
        token = auth.create_access_token("devuser", "developer")
        resp = client.get("/dev/config",
                          headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 403)


class TestDevSimulate(unittest.TestCase):
    def setUp(self):
        self.app, self.auth, _ = _make_dev_app("development")
        self.client = self.app.test_client()

    def _dev_token(self):
        return self.auth.create_access_token("devuser", "developer")

    def test_simulate_health_endpoint(self):
        token = self._dev_token()
        resp = self.client.post(
            "/dev/simulate",
            json={"endpoint": "/api/health", "method": "GET"},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["method"], "GET")
        self.assertEqual(data["endpoint"], "/api/health")
        self.assertEqual(data["status_code"], 200)

    def test_simulate_missing_endpoint(self):
        resp = self.client.post(
            "/dev/simulate",
            json={"method": "GET"},
            headers={"Authorization": f"Bearer {self._dev_token()}"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_simulate_invalid_method(self):
        resp = self.client.post(
            "/dev/simulate",
            json={"endpoint": "/api/health", "method": "CONNECT"},
            headers={"Authorization": f"Bearer {self._dev_token()}"},
        )
        self.assertEqual(resp.status_code, 400)

    def test_simulate_no_auth(self):
        resp = self.client.post("/dev/simulate",
                                json={"endpoint": "/api/health"})
        self.assertEqual(resp.status_code, 401)


class TestDevLog(unittest.TestCase):
    def setUp(self):
        self.app, self.auth, self.dev_mod = _make_dev_app("development")
        self.client = self.app.test_client()

    def _dev_token(self):
        return self.auth.create_access_token("devuser", "developer")

    def _headers(self):
        return {"Authorization": f"Bearer {self._dev_token()}"}

    def test_log_event(self):
        resp = self.client.post(
            "/dev/log",
            json={"level": "DEBUG", "message": "testing step 1"},
            headers=self._headers(),
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertTrue(data["logged"])
        self.assertEqual(data["event"]["level"], "DEBUG")

    def test_log_event_missing_message(self):
        resp = self.client.post("/dev/log", json={"level": "INFO"},
                                headers=self._headers())
        self.assertEqual(resp.status_code, 400)

    def test_log_event_invalid_level(self):
        resp = self.client.post(
            "/dev/log",
            json={"level": "TRACE", "message": "x"},
            headers=self._headers(),
        )
        self.assertEqual(resp.status_code, 400)

    def test_get_logs(self):
        self.client.post("/dev/log",
                         json={"level": "INFO", "message": "event A"},
                         headers=self._headers())
        self.client.post("/dev/log",
                         json={"level": "ERROR", "message": "event B"},
                         headers=self._headers())
        resp = self.client.get("/dev/logs", headers=self._headers())
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertGreaterEqual(data["count"], 2)

    def test_get_logs_filtered_by_level(self):
        self.client.post("/dev/log",
                         json={"level": "DEBUG", "message": "debug msg"},
                         headers=self._headers())
        self.client.post("/dev/log",
                         json={"level": "ERROR", "message": "error msg"},
                         headers=self._headers())
        resp = self.client.get("/dev/logs?level=ERROR", headers=self._headers())
        events = resp.get_json()["events"]
        self.assertTrue(all(e["level"] == "ERROR" for e in events))

    def test_get_logs_no_auth(self):
        resp = self.client.get("/dev/logs")
        self.assertEqual(resp.status_code, 401)


class TestDevToolsProductionBlocked(unittest.TestCase):
    def setUp(self):
        self.prod_app, self.auth, _ = _make_dev_app("production")
        self.client = self.prod_app.test_client()
        self.token = self.auth.create_access_token("devuser", "developer")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def test_config_blocked(self):
        resp = self.client.get("/dev/config", headers=self._headers())
        self.assertEqual(resp.status_code, 403)

    def test_simulate_blocked(self):
        resp = self.client.post("/dev/simulate",
                                json={"endpoint": "/api/health"},
                                headers=self._headers())
        self.assertEqual(resp.status_code, 403)

    def test_log_blocked(self):
        resp = self.client.post("/dev/log",
                                json={"level": "DEBUG", "message": "x"},
                                headers=self._headers())
        self.assertEqual(resp.status_code, 403)

    def test_logs_blocked(self):
        resp = self.client.get("/dev/logs", headers=self._headers())
        self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
