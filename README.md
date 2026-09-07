# Weekly Retro Tool

See `AGENTS.md` and `_docs/` for the product spec, architecture, and task backlog.

## Setup

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env   # then fill in SECRET_KEY etc. if needed
```

Local dev works out of the box with no Postgres/Redis running: `DATABASE_URL`
unset falls back to a SQLite file, and `REDIS_URL` unset falls back to
Channels' in-memory layer. Set both in `.env` to match production once you
need real Postgres/Redis behavior.

## Running

```powershell
.venv\Scripts\python.exe manage.py check
.venv\Scripts\python.exe manage.py runserver
```

## Tests

```powershell
.venv\Scripts\python.exe -m pytest
```

## Formatting & linting

```powershell
.venv\Scripts\python.exe -m black .
.venv\Scripts\python.exe -m isort .
.venv\Scripts\python.exe -m ruff check .
```
