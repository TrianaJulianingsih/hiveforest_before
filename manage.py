#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import codecs
from pathlib import Path

from dotenv import load_dotenv

sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

PROTECTED_COMMANDS = {"migrate", "flush", "sqlflush", "loaddata"}


def patch_runserver_default_port(argv):
    """Default `runserver` to port 8080 instead of Django's usual 8000,
    to avoid clashing with other local instances of this project."""
    if len(argv) < 2 or argv[1] != "runserver":
        return argv
    has_addrport = any(not arg.startswith("-") for arg in argv[2:])
    if has_addrport:
        return argv
    return argv[:2] + ["8080"] + argv[2:]


def guard_production_commands(argv):
    if len(argv) < 2:
        return

    command = argv[1]
    app_env = os.environ.get("APP_ENV", "").strip().lower()
    allow_prod_migrate = os.environ.get("ALLOW_PROD_MIGRATE", "0").strip().lower()
    is_override_enabled = allow_prod_migrate in {"1", "true", "yes", "on"}

    if app_env == "prod" and command in PROTECTED_COMMANDS and not is_override_enabled:
        raise SystemExit(
            "Refusing to run database-impacting command on production. "
            "Set ALLOW_PROD_MIGRATE=1 if you intentionally want to proceed."
        )


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cfg.settings")
    sys.argv = patch_runserver_default_port(sys.argv)
    guard_production_commands(sys.argv)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
