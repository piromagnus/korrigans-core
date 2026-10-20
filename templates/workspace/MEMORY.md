---
summary: "Map of every memory of the household: where, what, who writes, who reads."
---
# Map of memories

All the household's memory is versioned markdown in this workspace (plus the defaults of the core). No fact lives only in a harness's internal memory (Claude Code's automatic memory, Hermes's `MEMORY.md`, pi or Codex sessions): if an agent learns something useful there, it copies it here.

| Memory | Where | Holds | Who writes | Who reads, when | Level |
| --- | --- | --- | --- | --- | --- |
| The Rule | `AGENTS.md` (generated: core Rule, module rules, `rules/house-rules.md`) | Autonomy, truth, tasks, journal | The user (house rules); the Chronicler proposes | Every agent, always loaded by the harness | hot |
| Working with the user | `USER.md` | Short dated rules (always, never, prefer); points to the user's person note | The Seneschal, when a preference changes (history in `memory/global/preferences.md`) | Every agent, injected at launch | hot |
| Agents | `agents/<agent>/` (workspace overrides the core): `IDENTITY.md`, `AGENTS.md`, `SOUL.md` | Who each agent is; see `agents/README.md` | The user, or the Seneschal on request (skill `adjust-agent`) | Assembled at each launch (`korrigans agent`) | hot |
| Personalities | `personalities/<name>.md` | Behaviour by risk, exploration, evidence and questions | The user | The agent that receives it | hot |
| Global context | `memory/global/` | The registry (where data, code, tools and rights are), repos and data per project, the user's preferences, an optional one-page `context.md` | The Seneschal (preferences, propagated answers), the user (`repos-data.md`), any agent with evidence (registry) | The Seneschal and the Commanders at start; a korrigan only the files its charter cites | warm |
| Role memory | `memory/agents/<agent>.md` | What a role has learned: pitfalls, useful commands, pending requests | The role itself | That role, at start and after compaction | warm |
| Project | `projects/<project>/` | Note (goal, due date, state), dated decisions | The project's Commander | The Commander always; the Seneschal the head of the note | warm |
| Project rules | `projects/<project>/rules.md` | Constraints specific to the project | The user (the Commander proposes) | The Commander and the project's korrigans, injected at launch | warm |
| Task | `tasks/<id>/` | Charter, card, evidence, progress, report, verdict | The Commander (charter), the korrigan (the rest), the Chancellor (verdict) | The korrigan in full; the Commander the charter, card and evidence | hot during the task, then cold |
| People | `people/` | Who is who, role, projects, how to work with them | The Seneschal, from the user's answers | Everyone, when needed | warm |
| Requests | `questions/Q-NNNN.md` | What is missing, working assumption, the user's answer, where to carry it | Any agent (`ask-question`); the Seneschal (`propagate-answers`) | The Seneschal each morning; the agent that asked | warm |
| Ideas | `ideas/` | Backlog of ideas to test, with their cycle and evidence pack | The Seneschal, the Commanders | The user, in the Morning Chronicle; the Seneschal when quota is left | warm |
| Ladder | `rules/escalation.toml`, `tasks/<id>/attempts.md`, `advice.md` | Difficulties, ranks (model and effort), starting rank, the Watch; attempts and advice of a task | The user (rules); `korrigans run` and the Watch (attempts, advice) | `korrigans run`, the korrigan that takes over, the Chronicler | warm |
| Lessons | `memory/lessons.md` | Findings from the journal, proposed rules, the user's decisions | The Chronicler; the user decides at the Round Table | The Chronicler, the user | cold |
| Reports | `reports/YYYY-MM-DD.md` | The frozen Morning Chronicle | `korrigans daily` and the Seneschal | The user; audit | cold, never edited |
| Resource notes | `resources/README.md`, `resources/{datasets,repos,tools}/` | Compact observed paths, formats, metadata and layout; never permissions | Agents (`create-resource`); upkeep `maintain-resources` | Linked notes first; actual resources only as needed | warm |
| Examples | `resources/catalog.md`, `resources/examples/` | Reusable results and templates; separate from descriptive notes | The korrigans, the Chronicler | Any agent before building | cold, catalog warm |
| Extensions | `extensions/`, `skills/` | Skills, MCP servers, plugins, registry | Any agent proposes; see `extensions/README.md` | Harnesses through the generated adapters | warm |
| Journal | `journal/YYYY-MM.jsonl` (+ `state/journal.sqlite`, derived) | One event per line | Scripts and hooks | The Chronicler, audit | raw |
| Traces | `tasks/*/trace-*.log`, harness transcripts | Full outputs of runs | Scripts, harnesses | Audit when in doubt | raw, outside git |

Modules add their own memories (for example `mail/YYYY-MM-DD.md` with the mail module, usage measures in `state/` with the quota module).

## Four layers of context

- Layer 0, sources: the user's library, notes and original documents. Searched, never loaded whole.
- Layer 1, global: `AGENTS.md`, `USER.md` and `memory/global/`. Short (a few pages in all), loaded by the steering sessions.
- Layer 2, project: `projects/<project>/` (note, rules, decisions), its rows of `repos-data.md`, its people, its Commander's memory.
- Layer 3, task: `tasks/<id>/`. A korrigan receives only its layer 3 and what its charter cites from layers 1 and 2.

## Reading by levels

An agent loads a file in full only after seeing that it helps.

- L0, one sentence: the `summary:` field at the top of every memory file and every typed note. `korrigans summaries <dir>` shows every L0 of a folder.
- L1, the overview: a folder's `README.md`, a project note, a task's card.
- L2, the full content: opened only when L0 and L1 show it serves the task.

## Outside memory engines

A memory engine or search index may serve as an index, never as the source of truth. It is fed from the markdown and must be deletable and rebuildable without loss. It goes through the extension cycle (third-party code, so the user's approval).

## Hygiene

- Compaction: before a session is compacted or closed, the agent writes in its role memory what must survive. The session context (hot) is disposable.
- Size: `memory/global/` stays under about four pages; beyond that, the Chronicler proposes moving the detail to a project or person note.
- Summaries: a memory file without `summary:` is flagged by the Chronicler (`korrigans summaries memory --missing`).
- Conflicts: a dated, sourced fact beats an unsourced one; when in doubt, ask the user (`ask-question`), never invent.
