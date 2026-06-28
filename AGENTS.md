# AGENTS.md — mcd-ua-idw agent entrypoint

Agents working in this repository should load the relevant local skills before acting:

- `skills/idw-design-decisions/SKILL.md` — use for data warehouse design decisions, DQM/TXT/TMP/ING/DWA conventions, schema choices, CSV quirks, and validation semantics.
- `skills/idw-operating-protocol/SKILL.md` — use for script authoring, runner behavior, database operation guidance, DDL safety, and test/run commands.

Project convention sources:

- `CLAUDE.md` — operational rules, script contract, manual execution checklist, and current project status.
- `DOCS/decisiones_de_diseno.md` — canonical design-decision log. Update it when new design choices are made.

Critical safety rule: agents may write or review scripts, but database-changing DDL (`CREATE TABLE`, `DROP TABLE`) is executed manually by a human through `uv run idw-scripts`.
