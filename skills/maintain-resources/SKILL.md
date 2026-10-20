---
name: maintain-resources
description: Maintain resource notes and compact project.md files. Use weekly by maintenance or the Chronicler, and after dataset, repository, path or tool changes.
---
# Resource and project upkeep

1. Read maintenance instructions, `resources/README.md`, index, verification dates and active projects. Stay within the charter and `memory/global/repos-data.md`; never infer new access.
2. After a known change, revise affected notes and project links. Weekly: check index/links and active-project paths; revisit notes not verified for 30 days in bounded batches. Rotate remaining notes, never rescan full volumes. Delegate searches to the locally prescribed model.
3. Check root mount/accessibility before declaring a path missing. An unavailable volume means unverified, not deleted. Do not follow links outside authorized paths.
4. Compare README, schemas, bounded structure and formats. Update only confirmed observations, sources and real verification dates. Never refresh a date without checking. No exhaustive sizes/costs or private data/secret reads.
5. Deduplicate only established identities; keep uncertain copies separate and preserve aliases/copy roles. Preserve UI catalogs and review states; report disagreements, never synchronize automatically. Use `create-resource` and `create-project-note`. Repair all links when renaming; no automatic deletion or changes to user decisions/status/access.
6. Flag drift, unassigned resources, conflicts and stale facts. Ask only for necessary decisions/access; continue the rest. Never edit historical reports.
7. Check links, budgets and `korrigans check`; `korrigans generate --check` if skills changed. Log date, checked scope, changes, errors, unavailable paths and next batch in maintenance memory/journal. No commit/push unless requested.

## Check

Read-only note validation (no dataset scan): `python3 <skill-dir>/scripts/check_notes.py <workspace>`. Fixture tests: `python3 -m unittest discover -s <skill-dir>/scripts -p 'test_*.py'`. Resolve the skill with `korrigans which skills/maintain-resources/SKILL.md`.

Two passes without source changes must produce no edits. A missing path deletes nothing. Every change is traceable and every project note stays compact.
