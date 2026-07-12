#!/usr/bin/env python3
"""Print DATABASE_URL from POSTGRES_* environment variables."""

import os
import sys
from urllib.parse import quote_plus


def build_database_url():
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    database = os.environ.get("POSTGRES_DB")
    host = os.environ.get("POSTGRES_HOST", "127.0.0.1")
    port = os.environ.get("POSTGRES_PORT", "5432")

    missing = [name for name, value in (
        ("POSTGRES_USER", user),
        ("POSTGRES_PASSWORD", password),
        ("POSTGRES_DB", database),
    ) if not value]
    if missing:
        raise SystemExit(f"Missing required env vars: {', '.join(missing)}")

    return (
        f"postgresql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{database}"
    )


if __name__ == "__main__":
    sys.stdout.write(build_database_url())
