---
summary: "One folder per project: its note, its decisions, its rules; a Commander if the user wants one."
---
# Projects

One folder per project, `projects/<project>/`:

| File | Holds | Who writes |
| --- | --- | --- |
| `project.md` | The note (`type: project`, template `templates/project.md`): goal, due date, state, status, intensity | The Commander, or the Seneschal |
| `decisions.md` | Dated decisions, one per line, with their source and, if one replaces another, why | The Commander, from the user's answers |
| `rules.md` | Constraints specific to the project (data, compute, publication) | The user; the Commander proposes |

- Status: `active`, `paused`, `watch`, `finished`. Intensity: `focus`, `background`, `watch`.
- A project with a folder `agents/commanders/<project>/` has its own Commander; otherwise the Seneschal follows it. To add one: ask the Seneschal (skill `adjust-agent`).
- The code and data of a project are listed in `memory/global/repos-data.md`, kept by the user.
