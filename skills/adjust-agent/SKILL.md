---
name: adjust-agent
description: Rename an agent, change its personality or its voice, add a role rule, or create the Commander of a project. Used by the Seneschal when the user asks; other agents only propose.
---

Everything happens in the existing files; nothing is copied elsewhere. See `agents/README.md`.

1. Find the agent: `korrigans agent --list` (name, mode, personality, model, project). `korrigans which agents/<agent>/IDENTITY.md` shows whether the file comes from the workspace, a module or the core.
2. Work in the workspace only. To change a core file, first copy it to the same relative path in the workspace, then edit the copy.
3. Depending on the user's request:
   - Rename: field `display_name` of `agents/<agent>/IDENTITY.md`. The folder and `name` do not change (scripts and the task manager use them).
   - Change the default personality: field `personality` of the same file, a plain name (`cautious`). For a single session or task, change nothing: `korrigans launch ... --personality <name>` or the charter's `personality`.
   - New personality: copy the closest one to `personalities/<name>.md` in the workspace, adjust the summary, the motto, the four axes and the behaviours, and add it to the table of `personalities/README.md`.
   - Voice: `SOUL.md` of the agent (or of the type). Show the text to the user before writing it.
   - Role rule: `AGENTS.md` of the agent. A rule for all Commanders or all korrigans goes in the type's `AGENTS.md`. A rule for one project goes in `projects/<project>/rules.md`; a preference of the user goes in `USER.md`; a rule for the whole household goes in `rules/house-rules.md`.
   - Commander for a project: copy `agents/commanders/_template/` (`korrigans which agents/commanders/_template/IDENTITY.md`) to `agents/commanders/<project>/`, replace `<project>`, `<Project>` and `<Name>`, choose the name and the personality with the user. Default names come from the Round Table, in order: Bedivere, Gawain, Percival, Yvain, Gareth, Tristan. The project must exist in `projects/<project>/project.md`; its people, code and data stay in `people/`, the project note and `memory/global/repos-data.md`.
4. Check: `korrigans check` (project and personality exist, one Commander per project), then `korrigans agent <agent>` to read the assembled prompt, and `korrigans generate` if the agent runs as a subagent.
5. Log (`korrigans journal add --type agent_changed --agent seneschal`) and commit "agents: <what changed>".

Another agent that thinks a voice, a personality or a rule should change writes it as a proposal in its card or as a request. It never edits `IDENTITY.md`, `SOUL.md` or `personalities/` itself.
