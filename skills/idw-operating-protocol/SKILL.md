---
name: idw-operating-protocol
description: "Trigger: operate, run scripts, idw-scripts, DDL, script runner, new pipeline script. Follow mcd-ua-idw execution rules."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## Activation Contract

Use this skill before creating, editing, or running project scripts, touching the database, changing runner behavior, or advising another agent/human how to operate the pipeline.

## Hard Rules

- Use `uv` for Python commands and dependency work.
- Runnable modules live in `src/mcd_ua_idw/scripts/` and expose `VERSION: int` plus `async def run(session) -> dict`.
- `run()` must not commit or rollback; the runner owns the transaction boundary.
- Return only JSON-serializable dictionaries from scripts.
- Keep helpers outside `mcd_ua_idw/scripts/`; discovery imports every module and ignores only non-runnable modules without `run`.
- Never execute `CREATE TABLE`/`DROP TABLE` DDL automatically as an agent. Write or review scripts, but a human triggers DB-changing DDL through `uv run idw-scripts`.

## Decision Gates

| Situation | Action |
|---|---|
| SQL-backed script | Co-locate `.py` wrapper and same-base `.sql`; wrapper calls `run_sql_file` |
| New pipeline step | Name `e<etapa>_p<paso>_<descripcion>` and update the manual execution checklist |
| Utility/test script | Name `util_<descripcion>` |
| DB state uncertainty | Verify code and docs before assuming prior runs happened |

## Execution Steps

1. Read `CLAUDE.md` before operating the pipeline.
2. Use `uv run idw-scripts` for manual TUI execution guidance; it runs selected scripts only.
3. Respect the documented checklist order, not visual TUI order, when running dependent scripts.
4. Run tests after code changes, normally `uv run pytest`.

## Output Contract

Report commands run, tests, any manual steps still required, and whether any DDL/data-changing step was intentionally left for a human.

## References

- `CLAUDE.md` — operating protocol and script execution checklist.
- `src/mcd_ua_idw/script_runner/discovery.py` — script discovery contract.
- `src/mcd_ua_idw/script_runner/runner.py` — transaction and tracking boundaries.
- `src/mcd_ua_idw/script_runner/sql_utils.py` — SQL-backed script helper.
