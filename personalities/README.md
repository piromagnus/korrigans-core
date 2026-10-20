---
summary: "The personalities of the agents: how an agent takes risks, explores and decides when it has a choice. The user can change them."
---
# Personalities

A personality sets how an agent works where the rules leave it a choice: how much it explores, what risk it accepts, what level of evidence it needs before concluding, when it asks. It never changes what is forbidden or required: the Rule (`AGENTS.md`), the role's rules, the project's rules and the charter come first.

| Personality | Motto | In one sentence | For what |
| --- | --- | --- | --- |
| `rigorous` | Count the stones twice. | Evidence first, small checked steps, no conclusion without a measure. | Results for a publication, evidence packs, checking. |
| `cautious` | Look under the stone before you lift it. | Reversible first, read-only by default, asks before widening. | Precious data, shared repositories, mail, anything that touches the outside. |
| `balanced` | Steady steps, open eyes. | The default: moves alone on what is reversible, stops on the rest. | Running the household, everyday tasks. |
| `adventurous` | Three paths at dusk, one home by dawn. | Explores several leads fast, prototypes, accepts the preliminary. | Ideas to test, spare quota, first explorations. |
| `bold` | One long shot, a fixed purse. | Tries the unlikely high-gain bet, within a bounded budget. | Risky ideas the user wants tried once. |

## Axes

Each file has four axes in its frontmatter, read into the agent's prompt: `risk`, `exploration`, `evidence` (the level of proof needed), `questions` (when to ask). Plus a one-line `summary` and a `motto`.

## Where it is chosen (the most specific wins)

1. `--personality` on the command line (`korrigans launch`, `korrigans run`): for one session or one run.
2. The field `personality` of a task's charter.
3. The field `personality` of the agent's `IDENTITY.md` (for example `agents/commanders/<project>/IDENTITY.md`).
4. The one of the type's `IDENTITY.md` (`agents/commanders/IDENTITY.md`).
5. Otherwise `balanced`.

## Change

- Change an agent's personality: edit the field `personality` of its `IDENTITY.md`. A plain name (`cautious`) works; a link (`"[[personalities/cautious|cautious]]"`) also works and shows in the graph.
- Change what a personality means: put your own `personalities/<name>.md` in the workspace. Every agent that carries it changes.
- Create one: copy a file into the workspace `personalities/`, rename it, adjust it. The file name is the personality's name.
- The Seneschal makes these changes on request (skill `adjust-agent`). An agent may propose to adjust a personality, never its own by itself.
