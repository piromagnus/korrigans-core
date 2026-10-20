---
summary: "Where the user's notes, repositories, data and tools are, and what the agents may do with them."
updated: ""
---
# Registry: where things are

Each line says where a resource is and what the agents may do with it. A line "to complete" means: ask the user before touching it. Filled in during the Vigil, then kept up to date with dated, sourced lines.

<!-- vigil: data -->

| Resource | Where | Agents' rights | Status |
| --- | --- | --- | --- |
| This workspace | `<path>`, its own git repository | Read, write, commit on task branches; no push to main, no force push | Installed on <date> |
| The core | `<path>` (`korrigans which` shows which files are used) | Read only; changes go through a workspace override | Installed on <date> |
| The library (the user's knowledge base, notes) | `<path or none>` | Read; write only as the user's rules say | To complete |
| Task manager | `<none, or the tool and project>` (todoist module) | Read; create and update only in the household's project; never delete | To complete |
| Mail | `<none, or the mail client>` (mail module) | Read; file into folders; drafts only; never send or delete | To complete |
| Calendar | `<none, or the connector>` | Read only; never invite anyone | To complete |
| Subscriptions | `rules/subscriptions.toml` (quota module); measures in `state/` | Read; the user sets the thresholds | To complete |
| Code and data per project | `memory/global/repos-data.md`, kept by the user | Read before writing a charter; a task's access derives from it | To complete |
| Secrets | `.env` (git-ignored) and the paths listed here | Check presence only; never read, print or copy | To complete |

Data sent to AI providers: no rule yet. Add the user's rules here when they set them. Private or unpublished data never goes to a public service.
