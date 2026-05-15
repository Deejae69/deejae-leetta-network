"""
Tests for the admin blueprint (api/admin.py).

Uses a Flask test client with a pre-hashed admin password injected through
environment variables, keeping the tests hermetic.
"""

import importlib
import os
import unittest

import pyotp


def _make_app(env_overrides: dict = None):
    """Build and return a fresh Flask test app with optional env overrides."""
    defaults = {
        "JWT_SECRET_KEY": "test-admin-secret-key-at-least-32-chars",
        "JWT_ACCESS_TOKEN_EXPIRES": "3600",
        "ENVIRONMENT": "development",
        "MFA_REQUIRED": "False",
        "ADMIN_USERS": "testadmin",
    }
    if env_overrides:
        defaults.update(env_overrides)
    for k, v in defaults.items():
        os.environ[k] = v

    # Reload settings and all dependent modules to pick up env changes
    import config.settings as settings_mod
    importlib.reload(settings_mod)
    import api.auth as auth_mod
    importlib.reload(auth_mod)
    import api.audit_log as audit_mod
    importlib.reload(audit_mod)
    import api.admin as admin_mod
    importlib.reload(admin_mod)

    from flask import Flask
    from flask_cors import CORS
    app = Flask(__name__)
    app.config["TESTING"] = True
    CORS(app)
    app.register_blueprint(admin_mod.admin_bp)
    return app, auth_mod, admin_mod


class TestAdminLogin(unittest.TestCase):
    def setUp(self):
        from api.auth import hash_password
        pw_hash = hash_password("adminpass")
        self.app, self.auth, self.admin_mod = _make_app({
            "ADMIN_PASSWORD_HASH_TESTADMIN": pw_hash,
        })
        self.client = self.app.test_client()

    def test_login_success(self):
        resp = self.client.post("/admin/login", json={
            "username": "testadmin",
            "password": "adminpass",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "admin")

    def test_login_wrong_password(self):
        resp = self.client.post("/admin/login", json={
            "username": "testadmin",
            "password": "wrongpass",
        })
        self.assertEqual(resp.status_code, 401)

    def test_login_unknown_user(self):
        resp = self.client.post("/admin/login", json={
            "username": "nobody",
            "password": "anything",
        })
        self.assertEqual(resp.status_code, 401)

    def test_login_returns_error_not_hint(self):
        resp = self.client.post("/admin/login", json={
            "username": "nobody",
            "password": "x",
        })
        body = resp.get_json()
        self.assertIn("error", body)
        self.assertNotIn("username", body.get("error", "").lower())


class TestAdminLoginWithMFA(unittest.TestCase):
    def setUp(self):
        from api.auth import hash_password
        self.totp_secret = pyotp.random_base32()
        pw_hash = hash_password("mfapass")
        self.app, self.auth, self.admin_mod = _make_app({
            "ADMIN_PASSWORD_HASH_TESTADMIN": pw_hash,
            "ADMIN_TOTP_SECRET_TESTADMIN": self.totp_secret,
            "MFA_REQUIRED": "True",
        })
        self.client = self.app.test_client()

    def test_mfa_challenge_returned(self):
        resp = self.client.post("/admin/login", json={
            "username": "testadmin",
            "password": "mfapass",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("mfa_required"))
        self.assertIn("mfa_nonce", data)

    def test_mfa_complete_with_valid_code(self):
        # Step 1: get nonce
        resp1 = self.client.post("/admin/login", json={
            "username": "testadmin", "password": "mfapass",
        })
        nonce = resp1.get_json()["mfa_nonce"]
        # Step 2: submit valid TOTP code
        code = pyotp.TOTP(self.totp_secret).now()
        resp2 = self.client.post("/admin/login/mfa", json={
            "mfa_nonce": nonce, "totp_code": code,
        })
        self.assertEqual(resp2.status_code, 200)
        self.assertIn("access_token", resp2.get_json())

    def test_mfa_complete_with_invalid_code(self):
        resp1 = self.client.post("/admin/login", json={
            "username": "testadmin", "password": "mfapass",
        })
        nonce = resp1.get_json()["mfa_nonce"]
        resp2 = self.client.post("/admin/login/mfa", json={
            "mfa_nonce": nonce, "totp_code": "000000",
        })
        self.assertEqual(resp2.status_code, 401)

    def test_mfa_invalid_nonce(self):
        resp = self.client.post("/admin/login/mfa", json={
            "mfa_nonce": "bad-nonce", "totp_code": "123456",
        })
        self.assertEqual(resp.status_code, 401)


class TestAdminEndpointsRBAC(unittest.TestCase):
    def setUp(self):
        from api.auth import hash_password
        pw_hash = hash_password("adminpass")
        self.app, self.auth, self.admin_mod = _make_app({
            "ADMIN_PASSWORD_HASH_TESTADMIN": pw_hash,
        })
        self.client = self.app.test_client()

    def _admin_token(self):
        return self.auth.create_access_token("testadmin", "admin")

    def _dev_token(self):
        return self.auth.create_access_token("testdev", "developer")

    def _auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    # --- /admin/audit ---

    def test_audit_requires_auth(self):
        resp = self.client.get("/admin/audit")
        self.assertEqual(resp.status_code, 401)

    def test_audit_developer_denied(self):
        resp = self.client.get("/admin/audit",
                               headers=self._auth_headers(self._dev_token()))
        self.assertEqual(resp.status_code, 403)

    def test_audit_admin_allowed(self):
        resp = self.client.get("/admin/audit",
                               headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("events", data)

    # --- /admin/settings ---

    def test_get_settings_requires_auth(self):
        resp = self.client.get("/admin/settings")
        self.assertEqual(resp.status_code, 401)

    def test_get_settings_admin_ok(self):
        resp = self.client.get("/admin/settings",
                               headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("settings", resp.get_json())

    def test_update_setting(self):
        token = self._admin_token()
        resp = self.client.put("/admin/settings",
                               json={"log_level": "DEBUG"},
                               headers=self._auth_headers(token))
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("log_level", data["updated"])
        self.assertEqual(data["settings"]["log_level"], "DEBUG")

    def test_update_unknown_setting_rejected(self):
        resp = self.client.put("/admin/settings",
                               json={"non_existent_key": "val"},
                               headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 400)

    # --- /admin/keys ---

    def test_list_keys_empty(self):
        # Reload to reset key store
        import api.admin as am
        am._api_keys.clear()
        resp = self.client.get("/admin/keys",
                               headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["keys"], [])

    def test_create_key(self):
        import api.admin as am
        am._api_keys.clear()
        resp = self.client.post("/admin/keys",
                                json={"name": "openai", "value": "sk-test"},
                                headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["name"], "openai")

    def test_create_key_without_value_generates_one(self):
        import api.admin as am
        am._api_keys.clear()
        resp = self.client.post("/admin/keys",
                                json={"name": "auto-key"},
                                headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 201)
        # Value is stored server-side; the response does NOT include the value
        data = resp.get_json()
        self.assertNotIn("value", data)

    def test_delete_key(self):
        import api.admin as am
        am._api_keys.clear()
        self.client.post("/admin/keys",
                         json={"name": "to-delete"},
                         headers=self._auth_headers(self._admin_token()))
        resp = self.client.delete("/admin/keys/to-delete",
                                  headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 200)

    def test_delete_nonexistent_key(self):
        resp = self.client.delete("/admin/keys/does-not-exist",
                                  headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 404)

    # --- /admin/users ---

    def test_list_users(self):
        resp = self.client.get("/admin/users",
                               headers=self._auth_headers(self._admin_token()))
        self.assertEqual(resp.status_code, 200)
        users = resp.get_json()["users"]
        self.assertTrue(any(u["username"] == "testadmin" for u in users))

    def test_users_endpoint_no_passwords_exposed(self):
        resp = self.client.get("/admin/users",
                               headers=self._auth_headers(self._admin_token()))
        body = resp.get_json()
        for user in body["users"]:
            self.assertNotIn("password_hash", user)
            self.assertNotIn("totp_secret", user)


class TestAuditLogSearch(unittest.TestCase):
    def setUp(self):
        import api.audit_log as al
        al._buffer.clear()

    def test_log_and_retrieve(self):
        import api.audit_log as al
        al.log_event("alice", "login", "success", ip_address="127.0.0.1")
        al.log_event("bob", "update_settings", "success")
        events = al.get_recent_events(limit=10)
        self.assertEqual(len(events), 2)

    def test_search_by_actor(self):
        import api.audit_log as al
        al.log_event("alice", "login", "success")
        al.log_event("bob", "login", "failure")
        results = al.search_events(actor="alice")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["actor"], "alice")

    def test_search_by_outcome(self):
        import api.audit_log as al
        al.log_event("alice", "login", "success")
        al.log_event("alice", "login", "failure")
        results = al.search_events(outcome="failure")
        self.assertTrue(all(e["outcome"] == "failure" for e in results))

    def test_search_by_action(self):
        import api.audit_log as al
        al.log_event("alice", "update_settings", "success")
        al.log_event("alice", "delete_key", "success")
        results = al.search_events(action="update")
        self.assertTrue(all("update" in e["action"] for e in results))


if __name__ == "__main__":
    unittest.main()
