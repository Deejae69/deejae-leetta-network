"""Tests for scripts/hash_password.py."""

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

import scripts.hash_password as hash_script


class TestHashPasswordScript(unittest.TestCase):
    def test_main_with_cli_argument(self):
        out = io.StringIO()
        err = io.StringIO()
        with patch("scripts.hash_password.sys.argv", ["hash_password.py", "abc123"]), \
                patch("scripts.hash_password.hash_password", return_value="hashed-value") as mocked_hash, \
                redirect_stdout(out), redirect_stderr(err):
            hash_script.main()

        mocked_hash.assert_called_once_with("abc123")
        self.assertIn("hashed-value", out.getvalue())
        self.assertIn("ADMIN_PASSWORD_HASH_<USERNAME>=hashed-value", err.getvalue())

    def test_main_password_mismatch_exits(self):
        err = io.StringIO()
        with patch("scripts.hash_password.sys.argv", ["hash_password.py"]), \
                patch("getpass.getpass", side_effect=["one", "two"]), \
                redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                hash_script.main()

        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Passwords do not match", err.getvalue())

    def test_main_interactive_success(self):
        out = io.StringIO()
        with patch("scripts.hash_password.sys.argv", ["hash_password.py"]), \
                patch("getpass.getpass", side_effect=["same-pass", "same-pass"]), \
                patch("scripts.hash_password.hash_password", return_value="interactive-hash") as mocked_hash, \
                redirect_stdout(out):
            hash_script.main()

        mocked_hash.assert_called_once_with("same-pass")
        self.assertIn("interactive-hash", out.getvalue())


if __name__ == "__main__":
    unittest.main()
