---
name: todoist-sync
description: Build and keep the household's Todoist project, next to the user's own projects, with an owner (the user or an agent) for each delegated task. Used by the Seneschal once at the start, then when the user delegates new tasks.
---

The user's own projects (korrigans.toml `[todoist] read_only`) stay theirs: read them, never move, change or delete anything in them. The household's project (`[todoist] project`) only receives what the household takes on.

1. `korrigans todoist read "<the user's project>"` writes `state/todoist-<project>.json` (sections, tasks, sub-tasks, labels). Read only.
2. Propose the assignment in `tasks/<id>/assignment.md`: a table `| id | section | task | owner | reason |`, with the proposed owner (`user` or `agent-...`, see the labels in `AGENTS.md`) and the reason in a few words. Propose only tasks where an agent can do all or part of the work; the others stay only in the user's project. Split a shared task: the agent's part gets the agent's label, the user's part (decision, review) gets `user`. When in doubt, do not copy it, and ask (skill `ask-question`).
3. Show the proposal to the user. Nothing is created before they agree.
4. Once they agree: `korrigans todoist apply tasks/<id>/assignment.md --from "<the user's project>" --execute`. The script creates the household's project if it is missing, with the same sections, the owner and status labels, then copies the kept tasks with a link to the original in their description. It never moves or deletes anything.
5. Write in `memory/global/registry.md` how the project is organized, and close the task with the script's output as evidence.

Later, keep the two in step: when a charter's status changes, update its Todoist task (label `in-progress`, `to-review` or `waiting-on-you`). When they disagree, the charter wins and Todoist is corrected.
