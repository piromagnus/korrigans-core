---
name: create-project-note
description: Create or condense a compact project.md with goal, state, next action and resource links. Use for new projects or oversized project context.
---
# Compact project note

1. Read the existing project note, rules, decisions and active tasks. Use `templates/project.md` via `korrigans which`; preserve frontmatter needed by the CLI.
2. Keep identity, one-line summary, status, owner, priority, relations and useful current facts. Never turn a perspective into a commitment or a reported result into evidence.
3. Aim for 5-10 body lines, at most 20: goal, verified state/blocker, next action, resource links. Short fragments; no long paragraphs or redundant tables.
4. Move paths, formats, architecture, commands and technical context into resource notes (`create-resource`). Do not repeat their metadata. Link existing rules and decisions. Preserve unique information in linked context or historical files before condensing; do not merely move long prose elsewhere in project.md.
5. Associate only resources whose use is supported by project sources. Keep candidates proposed, not established dependencies. Use relative Markdown links, or typed relations declared in `rules/relations.yaml`.
6. Never change status, priority, access, commitments or user decisions to fit the budget. Keep any essential exception and explain it.

## Check

- Sources and decisions preserved; no silent loss of facts.
- No broken links; `korrigans check` has no new errors.
- Goal, current state and next action understandable without opening resources.
