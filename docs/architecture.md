---
summary: "How Korrigans is built: core and workspace, layers, generated files, modules, the escalation ladder, and the path of a task from charter to seal."
---
# Architecture

## Core and workspace

Korrigans lives in two git repositories.

- **The core** (this repository, public, AGPL-3.0): scripts, default agents, skills, personalities, rules, templates and modules. Installed at `~/.local/share/korrigans` by default. You update it with `korrigans update`; you never edit it for your own needs.
- **The workspace** (private, one per user): your people, projects, tasks, ideas, requests, memory, reports, journal, and your overrides of the core. `~/korrigans` by default, marked by `korrigans.toml` at its root.

The CLI finds the workspace through `KORRIGANS_WORKSPACE`, else by walking up from the current folder to a `korrigans.toml`, else `~/korrigans`. Scripts write to the workspace only, never to the core.

## Layers

A file is looked up in layers, highest priority first:

1. the workspace;
2. each enabled module (`modules/<m>/` in the core), in the order of `modules` in `korrigans.toml`;
3. the core.

- A relative path (`agents/seneschal/SOUL.md`, `rules/escalation.toml`, `templates/task/charter.md`) resolves to the first layer that has it. The override is per file. `korrigans which <path>` shows the file used.
- Collections (agents, skills, personalities, scripts) are the union of the layers; on a name clash, the higher layer wins. A workspace script `scripts/foo.py` becomes the command `korrigans foo`.
- TOML rules merge: tables are deep-merged, core first, then modules, then the workspace, so a workspace file can override a single key. Top-level arrays are replaced, not merged.
- The Rule is the exception: the workspace `AGENTS.md` is generated (below).

## Generated files

`korrigans generate` writes, in the workspace:

- `AGENTS.md`: the core Rule, then each enabled module's `AGENTS.md`, then `rules/house-rules.md`, then a language line;
- the harness adapters: `CLAUDE.md`, `.claude/`, `.mcp.json`, `.pi/`, `.codex/`, `.agents/skills/` (links to the skills of every layer), `state/hermes.yaml`.

Never edit them by hand: change the source, then regenerate. `korrigans generate --check` reports drift and unregistered extensions.

`state/`, `Board.md` and `Watchtower.md` are derived too, and git-ignored. Markdown in git is the truth; everything derived can be rebuilt.

## Modules

A module is an optional folder `modules/<m>/` of the core with `module.toml` and, as needed, `AGENTS.md` (rules appended to the Rule), `agents/`, `skills/`, `scripts/` and `rules/`. Enable it in `korrigans.toml` (`modules = ["quota", "mail"]`), then run `korrigans generate`.

| Module | Adds |
| --- | --- |
| `quota` | Subscription tracking and alerts (`korrigans usage`), rest when the quota is spent, spare quota to the backlog |
| `mail` | The Chamberlain and mail sorting (`korrigans mail`, skill `sort-mail`); never sends, never deletes |
| `research` | Blondel and source finding (skill `find-sources`), bringing sources back to the library |
| `todoist` | A task manager mirror of the charters (`korrigans todoist`, skill `todoist-sync`); the charter still wins |

## How an agent is assembled

Nothing is copied into an agent's prompt by hand; it is reread at each launch (`korrigans agent <agent>`): display name, `USER.md`, where things are, the `AGENTS.md` of the type folder then the agent's own, the project context (or the portfolio for the Seneschal), the closest `SOUL.md`, the personality with its axes, the language line, and a last line saying that voice and personality never lift a rule. Details: `agents/README.md`.

## The escalation ladder

One ladder of ranks, each a `model:effort` (`rules/escalation.toml`): page, squire, knight, banneret, paladin, champion, grandmaster.

1. **Starting rank.** The charter's `difficulty` (easy, medium, hard) sets where the run starts (`[start]`: page, knight, banneret). Empty, `korrigans ladder classify <id>` decides from the cost and type of the task, else asks the Constable. A charter `rank` forces one rank, or a raw `model:effort`, with no climbing.
2. **Harness.** At each rank, `korrigans run` tries the harnesses of `rules/routing.toml` for the task type that have that model. Quota exhausted on one: the next harness at the same rank.
3. **Watch.** For medium and hard tasks, the Watch reads `progress.md` and the trace every few minutes, at a rank above the korrigan's (`[watch]`), and answers continue, advise (written to `advice.md`), escalate, or stop.
4. **Climb.** A failure, a failing `verify` command, time over `max_minutes`, or the Watch saying escalate: the attempt stops, its summary goes to `attempts.md`, and the next rank takes over from there. Climbing past another difficulty's start reclassifies the task (`difficulty_revised`).
5. **Stop.** The Watch saying stop, or `max_attempts` reached: the task goes to `waiting-on-you` (reason `review`) for its Commander.

`korrigans ladder show <id>` prints the ladder a task would follow; `korrigans run <id> --dry-run` prints the commands without running them.

## A task, from charter to seal

1. **Request.** The user tells the Seneschal. An idea becomes an idea note (`capture-idea`), not a task. A task for a project with a Commander becomes a charter owned by that Commander.
2. **Charter.** The Commander (or the Seneschal) runs `korrigans task new`, then fills the charter with the skill `delegate`: goal, deliverable, `access`, three to six criteria with their expected evidence, difficulty, optional personality and `verify`. For code: `korrigans task worktree <id> --repo <path>` makes a worktree on `task/T-NNNN-slug`.
3. **Run.** `korrigans run <id>` assembles the korrigan's prompt (the korrigan's contract, project context, personality, then the charter), saves it in `prompt.md`, and climbs the ladder as needed. The korrigan keeps `progress.md`; the Watch writes `advice.md`; `korrigans track` and `Watchtower.md` show where it stands. Missing information becomes a request; a blocking one sets `waiting-on-you` (info).
4. **Delivery.** The korrigan puts one file per criterion in `evidence/`, writes `card.md`, and sets `to-review` (skill `deliver`).
5. **Validation.** The Commander checks each criterion against its evidence, reruns cheap commands, and for important tasks asks the Chancellor (`verdict.md`). Then `done`, or sent back with what is missing; after two send-backs, `waiting-on-you` (review).
6. **Seal.** When a task tested an idea and the Chancellor finds it robust, the Commander prepares the evidence pack (`prepare-evidence-pack`); the Seneschal presents it; only the user seals it (`decision`, `reviewed_by`). Then the result may enter the user's knowledge base.
7. **Record.** Each step is in the journal. The next Morning Chronicle reports it; the Round Table looks back on the week.
