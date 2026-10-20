# Module todoist

Mirrors the household's tasks in a Todoist project, so you see who does what in the app you already use.
The charter (`tasks/<id>/charter.md`) stays the truth.

Enable it with `modules = ["todoist"]` in `korrigans.toml`, then:

```toml
[todoist]
project = "Korrigans"        # the project the household writes to
read_only = ["Work"]         # your own projects: read, never changed, moved or deleted
```

Put your API token in the workspace's `.env`, as the value of `TODOIST_API_TOKEN` (from Todoist's settings,
Integrations, Developer). Agents never read it; `korrigans daily` loads it.

- `korrigans todoist today`: tasks due today or overdue, for the Morning Chronicle (`state/todoist-YYYY-MM-DD.json`).
- `korrigans todoist read "Work"`: a whole project, read only (`state/todoist-work.json`).
- `korrigans todoist apply tasks/<id>/assignment.md`: preview the copy of the tasks the household takes on;
  add `--execute` once you agree. Nothing is ever deleted.

The skill `todoist-sync` walks the Seneschal through it. The module also adds the official Todoist MCP
server (`mcp/servers.toml`) to the files `korrigans generate` writes for each harness.
