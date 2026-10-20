---
summary: "How an agent of the household is defined: one folder with IDENTITY.md, AGENTS.md and sometimes SOUL.md, plus a personality; how to rename, change or add one."
---
# Agents

One agent is one folder. The file names follow OpenClaw and Hermes (`IDENTITY.md`, `SOUL.md`, `AGENTS.md`) so those tools can read them and they are easy to copy.

| File | Holds | Who changes it |
| --- | --- | --- |
| `IDENTITY.md` | Frontmatter: `name` (slug), `type` (`agent`, or `agent-defaults` for a type folder), `description`, `mode` (`session`, `subagent`, or `call` for a short call such as the Watch or the Constable), `tools`, `model` (`standard`, `strong`, `fast`), `memory`, `display_name`, `personality`, `project` (Commanders only) | The user (the Seneschal on request) |
| `AGENTS.md` | The rules of the role: what it does, what it does not do | The user; an agent may propose |
| `SOUL.md` | Voice and posture (sessions only: the Seneschal, the Commanders) | The user; an agent may propose, never write |

```text
agents/
  seneschal/            IDENTITY, SOUL, AGENTS   (one Seneschal, default name Lucan)
  commanders/           AGENTS shared by all Commanders, default SOUL and IDENTITY
    _template/          to copy for a new Commander
    <project>/          one per project, in the workspace
  korrigans/            AGENTS shared by all korrigans (the korrigan's contract)
    code/  research/    IDENTITY and AGENTS of each kind
  chancellor/  watch/  virgil/  constable/  chronicler/
```

Modules add agents in `modules/<module>/agents/` (the Chamberlain with the mail module, Blondel with the research module).

## Three layers

Agents are looked up in layers, highest priority first: the workspace, then each enabled module, then the core.

- The list of agents is the union of the layers. A workspace folder with the same path as a core folder wins.
- Each file is overridden on its own. To change the Seneschal's voice, put your own `agents/seneschal/SOUL.md` in the workspace; the core `AGENTS.md` and `IDENTITY.md` still apply.
- An override replaces the whole file. To change one field of `IDENTITY.md`, copy the core file into the workspace first, then edit the copy.
- `korrigans which agents/seneschal/SOUL.md` shows which file is used.
- Commanders of the user's projects live only in the workspace: `agents/commanders/<project>/`.

## Linked to existing files

An agent copies nothing that already has a source. Its prompt is reread at each launch from:

| What it must know | Single source | Link |
| --- | --- | --- |
| For whom it works, and how | `USER.md`, which points to the user's person note | `user` in `korrigans.toml` |
| Its project | `projects/<project>/project.md`, `rules.md`, `decisions.md` | field `project` of its `IDENTITY.md` |
| The people of the project | `people/<name>.md` | `rel_involves` of the project note |
| The code and data of the project | `memory/global/repos-data.md` | column Project |
| Where tools are, and the rights | `memory/global/registry.md` | read by the agent when needed |
| Its personality | `personalities/<name>.md` | field `personality` |

## How a prompt is assembled

`korrigans agent <agent>` (used by `korrigans launch`, `korrigans run` and `korrigans daily`) puts together:

1. its display name, then `USER.md`, preceded by a line from the user's person note;
2. where things are (workspace, core, `korrigans which`);
3. the `AGENTS.md` of the type folder (rules shared by the type), then the agent's own;
4. for a Commander, or a korrigan whose task has a project: the project note, its people, its rows of `repos-data.md` and its rules; for the Seneschal: the project portfolio and who follows each project;
5. the closest `SOUL.md` (the agent's, else the type's);
6. the personality: option `--personality`, else the charter's `personality`, else the agent's `IDENTITY.md`, else the type's, else `balanced`;
7. the language line from `korrigans.toml`;
8. a last line: voice and personality set style and judgement, never the rules above.

The workspace `AGENTS.md` (the Rule) is read directly by the harness. The prohibitions are also blocked by harness permissions where possible; a personality never lifts them.

## Change an agent

Ask the Seneschal (skill `adjust-agent`) or edit the workspace files yourself.

- Rename: field `display_name` of `IDENTITY.md`. The folder and `name` do not change: scripts use them.
- Change the default personality: field `personality` of `IDENTITY.md`, a plain name (`cautious`) or a link (`"[[personalities/cautious|cautious]]"`). For one session or one task, change nothing: `--personality <name>` or the charter's `personality`.
- Adjust a voice: `SOUL.md` of the agent (or of the type).
- Add a role rule: `AGENTS.md` of the agent. A rule for all Commanders or all korrigans goes in the type's `AGENTS.md`.
- Add a Commander: copy `agents/commanders/_template/` from the core to `agents/commanders/<project>/` in the workspace, replace the placeholders, pick a name (Round Table names by default: Bedivere, Gawain, Percival, Yvain, Gareth, Tristan) and a personality. The project must exist in `projects/<project>/project.md`. A project without a Commander is followed by the Seneschal.

Then check: `korrigans check` (project and personality exist, one Commander per project), `korrigans agent <agent>` to read the assembled prompt, `korrigans agent --list` to see all agents with their name and personality, and `korrigans generate` if the agent is a subagent.
