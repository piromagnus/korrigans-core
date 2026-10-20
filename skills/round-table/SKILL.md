---
name: round-table
description: The weekly review of the household - the Chronicler reads a week of journal, attempts and lessons and proposes at most three rule changes; each Commander gives state, risk and next step; the user decides. Used by the Seneschal once a week or on request.
---

Nothing changes at the Round Table without the user. It proposes; the user decides.

1. The Chronicler prepares the material (its rules, `agents/chronicler/AGENTS.md`):
   - `korrigans journal index`, then `korrigans journal summary --days 7`;
   - the `attempts.md` of the week's tasks: escalations, reclassifications, stops by the Watch;
   - `memory/lessons.md`: the new lessons of the week;
   - at most three proposed rule changes, each with the tasks and numbers that justify it.
2. Each Commander gives its project in three lines: state, risk, next step, and what it needs from the user. A project without a Commander is reported by the Seneschal.
3. The Seneschal writes the Round Table in the user's language, short:
   - `## The week`: tasks done, sent back, waiting on the user; quota used if the quota module is on;
   - `## Commanderies`: one block per project (state, risk, next step, need);
   - `## Proposals`: the at most three changes, numbered, each with its reason and what it would change;
   - `## Open requests`: blocking first.
4. Present it to the user. For each proposal, the user says yes, no, or later. Write the decision in `memory/lessons.md` (column Status) with its date.
5. Apply only what the user approved: a house rule in `rules/house-rules.md`, a project rule in `projects/<project>/rules.md`, a TOML override in the workspace `rules/`, then `korrigans generate`. Commit "round table YYYY-MM-DD".
6. Log `korrigans journal add --type round_table --agent seneschal`.
