# MCD UA IDW

The project uses an asynchronous SQLAlchemy 2.0 persistence layer backed by
PostgreSQL. Dependencies and commands are managed with
[`uv`](https://docs.astral.sh/uv/).

## Local setup

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
uv run db-check
```

The database check opens one transaction-scoped `AsyncSession`, runs
`SELECT 1`, and disposes the application engine before exiting.

## Database modules

- `mcd_ua_idw.config` validates and loads `DATABASE_URL` from the environment
  or `.env`.
- `mcd_ua_idw.db` owns the declarative `Base` and metadata conventions.
- `mcd_ua_idw.db.session` owns engine and session-factory construction.
- `mcd_ua_idw.db.models` is the import registry for mapped classes. Import new
  model modules there so Alembic can discover their metadata.

Top-level scripts own transaction boundaries:

```python
async with get_session_factory().begin() as session:
    await perform_work(session)
```

Worker functions accept an `AsyncSession`; they must not create, commit, or
close it. Never share an `AsyncSession` between concurrent asyncio tasks.


## Script runner TUI

Run database scripts through the Textual menu so the application owns session
and DQM tracking boundaries:

```bash
uv run idw-scripts
```

Runnable modules live in `src/mcd_ua_idw/scripts/` and are discovered when they
expose the script interface:

```python
NAME = "Load source CSV"  # optional; TUI display label
VERSION = 1  # required; positive integer

async def run(session: AsyncSession) -> dict[str, Any]:
    ...
    return {"rows_inserted": 10}
```

The TUI wraps the selected script in one `AsyncSession` transaction. Scripts must
use the provided session and must not create, commit, rollback, or close their
own sessions. Before execution, a separate DQM tracking transaction registers the stable
module slug in `Scripts` and the required `VERSION` in `ScriptVersions`. After
the script transaction completes, another tracking transaction writes the
timestamps, status, and structured JSON output or error details to the matching
script version.

## Migrations and tests

Create migrations only after adding or changing mapped models:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
uv run alembic upgrade head
uv run pytest
```

Runtime code does not call `Base.metadata.create_all()`. The current tests are
offline unit tests and do not require a running PostgreSQL container.
