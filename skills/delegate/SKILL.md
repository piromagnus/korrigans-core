---
name: delegate
description: Write the charter of a task before handing it to a korrigan (goal, deliverable, access, verifiable criteria, expected evidence per criterion). Used by the Seneschal or a Commander before any delegation.
---

1. Create the folder: `korrigans task new "<title>" --project <project> --type <type>`. The script copies the charter template (`templates/task/charter.md`) to `tasks/<id>/charter.md`.
2. Fill in the charter:
   - Goal: one sentence, what will be true after the task.
   - Deliverable: files, branch or document produced.
   - Criteria: three to six, each checkable by someone who has not seen the work. For each, the expected evidence (test output, diff, screenshot, CSV, link, number).
   - A criterion with no possible evidence is rephrased, or marked "to be checked by the user".
   - Context: only the files and decisions needed, with their paths.
   - Access (`access` in the frontmatter and the Access section): what the korrigan may read or write outside the task folder, as `path:read` or `path:write`. Data is read-only. Another repository is writable only if `memory/global/repos-data.md` allows it for that repository. Paths come from that file, never from a guess.
   - Limits: what the korrigan must not do (cost, data, repositories).
   - Difficulty (`difficulty`): `easy`, `medium` or `hard`, per `rules/escalation.toml`. It sets the starting rank on the ladder; the run climbs if an attempt fails, and the task is then reclassified. Leave it empty and `korrigans ladder classify <id>` asks the Constable. When in doubt, the lowest. Use `rank` only to force one rank or one `model:effort`. `verify`: the command that proves the task is finished (`pytest -q`, a check script); if it fails, the next attempt runs at a higher rank.
   - Personality (`personality`, optional): empty keeps the korrigan's own (`rigorous` for code and research). Exploring a lead or a throwaway prototype: `adventurous`, and the result comes back marked preliminary. A number or figure for a publication: `rigorous`. Write access to a shared repository or to someone else's data: `cautious`. `bold` only if the user asked for it on this task. The personality changes neither the access nor the criteria.
   - A backlog task to place when quota is left: `--when quota-free` and a `cost`.
3. When the todoist module is on, mirror the task in the task manager with its owner and project, description = the path of the charter, and put the task manager's id in the charter's frontmatter.
4. Log: `korrigans journal add --type delegation --task <id> --agent <you> --tool <planned harness>`.
5. Launch when ready: `korrigans run <id>` (or `--dry-run` first to see the ladder and the commands).
