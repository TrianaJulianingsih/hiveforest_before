# HiveForest

Internal enterprise Django application (Sales, CRM, Supply Chain, Finance, Human Capital, BI, and more).

## Prerequisites

- Python 3.x
- PostgreSQL (local instance is fine for development)
- Git

## 1. Clone and install dependencies

```
git clone <repo-url>
cd hiveforest
pip install -r requirements.txt
```

## 2. Configure environment variables

Copy `.env.example` to `.env` and fill in real values:

```
cp .env.example .env
```

At minimum, for local development, set:

- `SECRET_KEY` — any long random string
- `DEBUG=True`
- `ALLOWED_HOSTS=localhost,127.0.0.1`
- `DB_HIVEFOREST_ENGINE=django.db.backends.postgresql`
- `DB_HIVEFOREST_DATABASE`, `DB_HIVEFOREST_USER`, `DB_HIVEFOREST_PASSWORD`, `DB_HIVEFOREST_HOST`, `DB_HIVEFOREST_PORT` — match whatever local PostgreSQL instance/credentials you set up in step 3
- `SESSION_COOKIE_SECURE=False` and `CSRF_COOKIE_SECURE=False` (these must be `False` for local `http://` development — leaving them `True` will cause `CSRF verification failed` errors in the browser)

Never commit `.env` — it's already gitignored.

## 3. Set up PostgreSQL

If you don't already have a local PostgreSQL server, install one (e.g. via `winget install PostgreSQL.PostgreSQL.17` on Windows, or your OS's package manager) and note the superuser password you set during install. Make sure the values match what you put in `.env` in step 2. The database named in `DB_HIVEFOREST_DATABASE` (commonly the default `postgres` database) must exist — no separate `CREATE DATABASE` step is required if you're using the default database.

## 4. Run migrations

```
python manage.py migrate --skip-checks
```

`--skip-checks` is required **the first time** you migrate a brand-new/empty database. Django's system checks load `ROOT_URLCONF`, which imports a view (`apps/humancapital/views/assignment_view.py`) that queries the database at import time — this fails on a database with no tables yet. Once tables exist, checks pass normally and `--skip-checks` is no longer necessary for later `migrate` runs.

## 5. Seed the CMS menu and translations

The sidebar menu (applications, modules, menu items) is database-driven, not hardcoded. Seed it with:

```
python manage.py seed_menu
python manage.py seed_translations
```

Both commands are idempotent — safe to re-run any time (e.g. after pulling changes to `apps/cms/management/commands/seed_data/*.csv`).

## 6. Log in

This project uses one shared superuser account for all interns:

- **Username:** `admin`
- **Password:** `admin123`

Superuser accounts automatically get full access to every active application/module/menu (see `apps/base/context_processors.py::has_access`) — no separate permission grant needed. The same account can be logged into from multiple devices/browsers at once; Django's session-based auth doesn't restrict an account to a single concurrent session.

If this account doesn't exist yet on your database, create it with:

```
python manage.py createsuperuser --username admin
```

(Change the shared password from the placeholder above before this ever goes near a non-local environment.)

For anyone who *does* need their own individually-scoped account instead of the shared one, use `python manage.py seed_roles --username <username>` after `createsuperuser` — this grants a specific non-superuser account full menu access via the custom `Role`/`CMSPermission` system, without making them a superuser.

## 7. Run the server

```
python manage.py runserver
```

This defaults to **port 8080** (patched in `manage.py`) instead of Django's usual 8000, to avoid clashing with other local instances of this project. Pass an explicit port to override, e.g. `python manage.py runserver 8000`.

Then open **http://127.0.0.1:8080/** and log in with the account from step 6.

## Known issues / gotchas

- **First migrate on an empty DB needs `--skip-checks`** — see step 4.
- **Non-superuser accounts need an explicit Role grant** — regular (non-superuser) accounts see an empty sidebar until granted access via `seed_roles` or the admin UI at `/admin/base/role/`. Superusers are exempt from this (see step 6).
- **CSRF errors on login/forms** — usually means `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE` are `True` while running on plain `http://`. Set both to `False` for local dev (see step 2), and hard-refresh the page after any server restart.
- Some historical migrations (`apps/{analytics,crm,finance,sales}/migrations/0002_initial.py`) are intentionally left as no-ops — they were accidentally regenerated duplicates of schema the real migration chain already creates, kept only so later merge migrations that depend on them stay valid. Don't repopulate their `operations` list.
