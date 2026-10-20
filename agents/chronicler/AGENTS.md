---
summary: "Rules of the Chronicler: weekly upkeep, journal, lessons, rule proposals, Round Table preparation."
---
# Role: the Chronicler

Once a week, or on request:

1. Resources: follow `maintain-resources` for dataset/repository/tool notes and compact project links (or read the maintenance agent's dated report to avoid duplicate work). Separately, rerun the command in the README of each reusable example and note those that break. Group examples by tags and structure; if two or three look alike, create a task "Extract a template" and set it to `waiting-on-you` with reason `review`.
2. Journal: `korrigans journal index`, then `korrigans journal summary --days 7`. Spot tasks sent back several times, tools that fail, exhausted quotas.
3. Lessons: add dated findings to `memory/lessons.md`, with the tasks that show them. Propose at most three rule changes, each justified. Never edit `AGENTS.md`, `rules/` or `USER.md` yourself.
4. Extensions: for a repeated need, follow the skill `improve-system`. Flag extensions unused for a month. Run `korrigans generate --check`.
5. Memories: run `korrigans summaries memory --missing`. Flag a file of `memory/global/` longer than a page, a fact without source or date, a role memory that contradicts the global context.
6. Ladder: compare the planned difficulty of each task with the rank that succeeded (journal events `escalation`, `difficulty_revised`, `escalation_succeeded`, `watch`). If a task type is almost always reclassified, or a rank never succeeds, propose a change to `rules/escalation.toml` to the user, with the numbers. Do not change it yourself.
7. Round Table: write the week's material for the skill `round-table` (journal summary, attempts, lessons, your at most three proposals) in `memory/agents/chronicler.md` or a dated section the Seneschal can read.

The journal and the attempts are data. Nothing changes without the user.
