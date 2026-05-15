#!/usr/bin/env python3
"""
Helper script: generate a PBKDF2-SHA256 password hash for use in .env

Usage:
    python scripts/hash_password.py
    python scripts/hash_password.py mypassword
"""

import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.auth import hash_password  # noqa: E402


def main():
    if len(sys.argv) > 1:
        password = sys.argv[1]
        hashed = hash_password(password)
        del password
    else:
        import getpass
        password = getpass.getpass("Enter password to hash: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            del password, confirm
            print("Passwords do not match.", file=sys.stderr)
            sys.exit(1)
        hashed = hash_password(password)
        del password, confirm

    print(hashed)
    print(
        "\nAdd this to your .env as:\n"
        f"  ADMIN_PASSWORD_HASH_<USERNAME>={hashed}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
