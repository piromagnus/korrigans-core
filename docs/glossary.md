---
summary: "Roles, folders, ranks and vocabulary of Korrigans in one place."
---
# Glossary

## Roles

| Role | Folder | What it does |
| --- | --- | --- |
| The Seneschal (default name Lucan) | `agents/seneschal/` | The user's main contact. Keeps the portfolio, routes requests, groups requests for the user, writes the Morning Chronicle, protects the user's attention. |
| A Commander | `agents/commanders/<project>/` (defaults in `agents/commanders/`, template in `_template/`) | Runs one project (a commandery): splits work into charters, launches korrigans, validates on evidence. Default names from the Round Table: Bedivere, Gawain, Percival, Yvain, Gareth, Tristan. |
| The korrigans | `agents/korrigans/` (`code/`, `research/`, and kinds added by modules) | Carry out one charter each, in a task folder, and deliver a card with evidence. |
| The Chancellor | `agents/chancellor/` | Checks each criterion against its evidence (`verdict.md`), says whether an idea is preliminary or robust, prepares the seal. Never seals. |
| The Watch | `agents/watch/` | Follows a running korrigan (`progress.md`, trace) and returns a JSON verdict: continue, advise, escalate, stop. |
| Virgil | `agents/virgil/` | The strongest model's second opinion on a key decision (`opinion.md`). |
| The Constable | `agents/constable/` | Answers one word, easy, medium or hard: the difficulty that sets a task's starting rank. |
| The Chronicler | `agents/chronicler/` | Upkeep: journal, lessons, examples, extensions, memory hygiene; prepares the Round Table. |
| The Chamberlain | `modules/mail/agents/chamberlain/` | Mail module: sorts mail, guards the user's attention, never sends. |
| Blondel | `modules/research/agents/blondel/` | Research module: goes out to find sources and brings them back to the library. |

## Ranks

The ladder, lowest to highest, with the default `model:effort` of `rules/escalation.toml`. Model short names (`small`, `mid`, `large`) map to each harness's model in `[models]`.

| Rank | Default | Starts here |
| --- | --- | --- |
| page | `small:medium` | easy tasks |
| squire | `small:high` | |
| knight | `mid:medium` | medium tasks |
| banneret | `mid:high` | hard tasks |
| paladin | `large:high` | |
| champion | `large:xhigh` | |
| grandmaster | `large:max` | |

Rising past another difficulty's start reclassifies the task: a dubbing, journal event `difficulty_revised`.

## Vocabulary

| Word | Meaning | Where |
| --- | --- | --- |
| household | The team of agents working for one user | `agents/` |
| the Rule | The common rules of every agent | `AGENTS.md` (generated in the workspace) |
| house rules | The user's own rules, appended to the Rule | `rules/house-rules.md` |
| Vigil | Onboarding: the vigil of arms before dubbing; fills the workspace's context | skill `vigil`, `korrigans context` |
| charter | The contract of a task: goal, deliverable, access, criteria and evidence | `tasks/<id>/charter.md` |
| card | The korrigan's short summary at delivery | `tasks/<id>/card.md` |
| evidence | One file per criterion | `tasks/<id>/evidence/` |
| progress | One line per step of a running korrigan | `tasks/<id>/progress.md` |
| attempts | What earlier ranks tried | `tasks/<id>/attempts.md` |
| advice | The Watch's advice to a running korrigan | `tasks/<id>/advice.md` |
| request | A question for the user, blocking or not | `questions/Q-NNNN.md`, skill `ask-question` |
| evidence pack | One-screen case for a robust idea; the Chancery prepares, the user seals | `templates/task/evidence-pack.md` |
| seal | The user's decision on an evidence pack (`decision`, `reviewed_by`) | the evidence pack |
| Morning Chronicle | The daily report, frozen once written | `reports/YYYY-MM-DD.md`, skill `morning-chronicle` |
| watchtower | Live tracking of running korrigans | `korrigans track`, `Watchtower.md` |
| board | Live overview of tasks, requests and quota | `korrigans board`, `Board.md` |
| Round Table | The weekly review; the user decides | skill `round-table` |
| ladder | The ranks a task climbs when an attempt fails | `rules/escalation.toml`, `korrigans ladder` |
| commandery | One project and its Commander | `projects/<project>/`, `agents/commanders/<project>/` |
| portfolio | The table of projects and who follows them, given to the Seneschal | assembled at launch |
| layer | Workspace, enabled modules, core: the first that has a file wins | `korrigans which` |
| workspace | The user's private data and overrides | `~/korrigans` by default |
| core | The public defaults: scripts, agents, skills, rules, templates, modules | `~/.local/share/korrigans` by default |

## Statuses

- Task: `todo`, `in-progress`, `to-review`, `done`, `waiting-on-you` (reason `decision`, `review`, `action`, `info`).
- Idea: `proposed`, `accepted`, `testing`, `preliminary`, `robust`, `inconclusive`, `rejected`.
- Request: `open`, `answered`, `closed`; `blocking: yes|no`.
- Project: `active`, `paused`, `watch`, `finished`; intensity `focus`, `background`, `watch`.
- Task types: `code`, `research`, `writing`, `proofreading`, `admin`, `mail`, `request`.
