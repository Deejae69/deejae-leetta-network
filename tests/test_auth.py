"""
Tests for api.auth — JWT, RBAC, password hashing, MFA helpers.
"""

import os
import time
import unittest

import jwt
import pyotp


class TestPasswordHashing(unittest.TestCase):
    def test_hash_and_verify(self):
        from api.auth import hash_password, verify_password

        pw = "super-secret-password"
        stored = hash_password(pw)
        self.assertTrue(verify_password(pw, stored))

    def test_wrong_password_rejected(self):
        from api.auth import hash_password, verify_password

        stored = hash_password("correct")
        self.assertFalse(verify_password("wrong", stored))

    def test_hashes_are_unique(self):
        from api.auth import hash_password

        h1 = hash_password("same")
        h2 = hash_password("same")
        self.assertNotEqual(h1, h2, "Each hash should use a different salt")

    def test_malformed_hash_returns_false(self):
        from api.auth import verify_password

        self.assertFalse(verify_password("any", "no-dollar-sign"))


class TestJWT(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-at-least-32-chars-long"

    def test_create_and_decode(self):
        import importlib
        import api.auth as auth_module
        importlib.reload(auth_module)
        from api.auth import create_access_token, decode_access_token

        token = create_access_token("alice", "admin")
        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], "alice")
        self.assertEqual(payload["role"], "admin")

    def test_expired_token_raises(self):
        import importlib
        os.environ["JWT_ACCESS_TOKEN_EXPIRES"] = "0"
        import config.settings as s
        importlib.reload(s)
        import api.auth as auth_module
        importlib.reload(auth_module)
        from api.auth import create_access_token, decode_access_token

        token = create_access_token("alice", "admin")
        time.sleep(1)
        with self.assertRaises(jwt.ExpiredSignatureError):
            decode_access_token(token)
        # Restore
        os.environ["JWT_ACCESS_TOKEN_EXPIRES"] = "3600"
        importlib.reload(s)
        importlib.reload(auth_module)

    def test_tampered_token_raises(self):
        import importlib
        import api.auth as auth_module
        importlib.reload(auth_module)
        from api.auth import create_access_token, decode_access_token

        token = create_access_token("bob", "developer") + "x"
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(token)


class TestRoleHierarchy(unittest.TestCase):
    def test_role_hierarchy(self):
        from api.auth import User, ROLE_ADMIN, ROLE_DEVELOPER, ROLE_VIEWER

        admin = User("u", ROLE_ADMIN, "hash")
        dev = User("u", ROLE_DEVELOPER, "hash")
        viewer = User("u", ROLE_VIEWER, "hash")

        # Admin has all roles
        self.assertTrue(admin.has_role(ROLE_ADMIN))
        self.assertTrue(admin.has_role(ROLE_DEVELOPER))
        self.assertTrue(admin.has_role(ROLE_VIEWER))

        # Developer does not have admin
        self.assertFalse(dev.has_role(ROLE_ADMIN))
        self.assertTrue(dev.has_role(ROLE_DEVELOPER))
        self.assertTrue(dev.has_role(ROLE_VIEWER))

        # Viewer has only viewer
        self.assertFalse(viewer.has_role(ROLE_ADMIN))
        self.assertFalse(viewer.has_role(ROLE_DEVELOPER))
        self.assertTrue(viewer.has_role(ROLE_VIEWER))


class TestTOTP(unittest.TestCase):
    def test_valid_code_accepted(self):
        from api.auth import verify_totp, generate_totp_secret

        secret = generate_totp_secret()
        code = pyotp.TOTP(secret).now()
        self.assertTrue(verify_totp(secret, code))

    def test_invalid_code_rejected(self):
        from api.auth import verify_totp, generate_totp_secret

        secret = generate_totp_secret()
        self.assertFalse(verify_totp(secret, "000000"))

    def test_provisioning_uri(self):
        from api.auth import get_totp_provisioning_uri, generate_totp_secret

        secret = generate_totp_secret()
        uri = get_totp_provisioning_uri("alice", secret)
        self.assertIn("otpauth://totp/", uri)
        self.assertIn("alice", uri)


class TestRequireAuthDecorator(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-at-least-32-chars-long"
        from flask import Flask
        import importlib
        import api.auth as auth_module
        importlib.reload(auth_module)
        self.auth = auth_module

        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.route("/protected")
        @auth_module.require_auth
        def protected():
            from flask import g
            return {"user": g.current_user["sub"]}

        self.client = app.test_client()

    def test_no_token_returns_401(self):
        resp = self.client.get("/protected")
        self.assertEqual(resp.status_code, 401)

    def test_invalid_token_returns_401(self):
        resp = self.client.get("/protected", headers={"Authorization": "Bearer bad"})
        self.assertEqual(resp.status_code, 401)

    def test_valid_token_passes(self):
        token = self.auth.create_access_token("alice", "admin")
        resp = self.client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200)


class TestRequireRoleDecorator(unittest.TestCase):
    def setUp(self):
        os.environ["JWT_SECRET_KEY"] = "test-secret-key-at-least-32-chars-long"
        import importlib
        import api.auth as auth_module
        importlib.reload(auth_module)
        self.auth = auth_module

        from flask import Flask
        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.route("/admin-only")
        @auth_module.require_auth
        @auth_module.require_role("admin")
        def admin_only():
            return {"ok": True}

        self.client = app.test_client()

    def _make_token(self, role):
        return self.auth.create_access_token("user", role)

    def test_viewer_is_denied(self):
        resp = self.client.get("/admin-only",
                               headers={"Authorization": f"Bearer {self._make_token('viewer')}"})
        self.assertEqual(resp.status_code, 403)

    def test_developer_is_denied(self):
        resp = self.client.get("/admin-only",
                               headers={"Authorization": f"Bearer {self._make_token('developer')}"})
        self.assertEqual(resp.status_code, 403)

    def test_admin_is_allowed(self):
        resp = self.client.get("/admin-only",
                               headers={"Authorization": f"Bearer {self._make_token('admin')}"})
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
