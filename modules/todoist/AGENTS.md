## Task manager: Todoist (module todoist)

- The household's tasks are mirrored in one Todoist project (korrigans.toml `[todoist] project`), next to the user's own projects. `korrigans todoist today` lists what is due; the skill `todoist-sync` builds and updates the project.
- One label per owner: `user`, `agent-seneschal`, `agent-commander`, `agent-code`, `agent-research`, `agent-mail`. Status labels: `in-progress`, `to-review`, `waiting-on-you` (with the reason in the task's comment).
- When Todoist and a charter disagree, `tasks/<id>/charter.md` wins and Todoist is corrected.
- The user's read-only projects (`[todoist] read_only`) are read, never changed, moved or deleted. In the household's project, tasks are created and updated, never deleted.
- The token (`TODOIST_API_TOKEN`) is in the workspace's `.env`: check it exists, never read or print it.
