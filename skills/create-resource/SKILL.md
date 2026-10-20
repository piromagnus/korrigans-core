---
name: create-resource
description: Create or revise a compact dataset, repository or tool note with observed paths, metadata and folder layout. Use before linking a resource from a project.
---
# Resource note

1. Read access rules, `resources/README.md` and existing notes. Reuse established identities, not one note per project. Keep uncertain copies separate; never merge by name alone.
2. Inspect authorized paths read-only: README, schemas, non-secret config, folder names and extensions. Follow local search-model rules. Bound depth and samples; no full scans, private records or execution of third-party code.
3. Write `resources/<datasets|repos|tools>/<slug>.md` using `templates/resource.md` (resolve with `korrigans which`). Aim for 8-15 body lines, about 1,500 characters; short bullets, no narrative. Exceed only for essential facts.
4. Include purpose; exact paths and each copy's role; types/formats; useful metadata; 1-3 folder levels; first file to open. Dataset: unit, modalities, labels/splits only if observed. Repository: components, entry points, declared dependencies. Tool: purpose, installation/non-secret config and documented command; do not claim it was tested.
5. Separate observations from interpretation. Mark unknown or unverified size, license, units, counts, quality, availability and access. Cite exact sources and real verification date. Missing storage is not proven deletion. Presence of a schema is not proof all data conform to it.
6. Never copy secrets, patient identifiers, raw records, `.env` contents or full file listings. Notes describe, never grant permissions: `memory/global/repos-data.md` remains authoritative. Preserve any existing UI catalog and review states; no automatic synchronization.
7. Link established project uses through `create-project-note`. Leave unassigned resources in the index; do not invent a project association.

## Check

- Observations, paths and formats sourced; uncertainty and inspection limits explicit.
- No secrets; local links resolve; `korrigans check` has no new errors.
- The note alone lets an agent decide where to look without loading the resource.
