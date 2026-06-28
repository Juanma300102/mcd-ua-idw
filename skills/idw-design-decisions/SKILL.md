---
name: idw-design-decisions
description: "Trigger: decisiones de diseño, DQM, TXT, TMP, ING, DWA, Northwind schema. Apply mcd-ua-idw data warehouse design rules."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## Activation Contract

Use this skill before changing database schemas, ETL scripts, DQM logic, layer prefixes, CSV mappings, validation rules, or reportable design decisions for this project.

## Hard Rules

- Treat the assignment prompt as source of truth; prior-year examples are format references only.
- Discuss and document new design decisions before implementation in `DOCS/decisiones_de_diseno.md`.
- Keep DW transformation logic in SQL; Python scripts orchestrate sessions, CSV reads, and runner integration.
- Use documented layer prefixes: `TXT_`, `TMP_`, `ING_`, `DWA_`, `DQM_`, `DWM_`, `MET_`, `DPxx_`.
- Use snake_case database columns; map CSV camelCase names explicitly in Python loaders.
- Preserve current DQM grain: `dqm_eventos`, `dqm_validaciones`, `dqm_perfilado`; do not collapse them into EAV.

## Decision Gates

| Change | Required action |
|---|---|
| New table/layer | Confirm prefix and grain in design doc first |
| CSV quirk or type mismatch | Record the accepted handling in design decisions |
| New quality check | Insert results into the correct DQM table and catalog `tipo_chequeo` |
| FK/staging change | Prefer DQM validation over physical FK constraints in TMP unless explicitly agreed |

## Execution Steps

1. Read `DOCS/decisiones_de_diseno.md` for existing decisions before proposing changes.
2. Check `CLAUDE.md` for current project status, TODOs, and operational rules.
3. Implement according to existing Etapa script patterns and table naming conventions.
4. Update the design decision log when a new choice, exception, or data-quality finding is introduced.

## Output Contract

Report the decision source used, files changed, any new/updated decision entry, and whether implementation follows existing layer/DQM conventions.

## References

- `DOCS/decisiones_de_diseno.md` — canonical project design decisions.
- `CLAUDE.md` — project conventions, status, and operating rules.
