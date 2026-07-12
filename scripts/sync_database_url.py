#!/usr/bin/env python3
"""Write DATABASE_URL for Docker host networking into .env.docker-runtime."""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).resolve().parents[1]


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


def main():
    runtime_env = ROOT / ".env.docker-runtime"
    database_url = build_database_url()

    lines = []
    if runtime_env.exists():
        for line in runtime_env.read_text(encoding="utf-8").splitlines():
            if line.startswith("DATABASE_URL="):
                continue
            lines.append(line)

    lines.append(f"DATABASE_URL={database_url}")
    runtime_env.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote DATABASE_URL to {runtime_env}")


if __name__ == "__main__":
    main()
