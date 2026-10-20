---
summary: "The backlog of ideas to test and their cycle, from capture to the user's knowledge base."
---
# Ideas

One idea per file `YYYY-MM-DD-slug.md`, created by the skill `capture-idea` from the idea template (`korrigans which templates/idea.md`). An idea is never a task: it becomes one only when the user accepts it.

## Cycle

| Status | Meaning | Who decides |
| --- | --- | --- |
| proposed | Captured, not chosen yet | The Seneschal |
| accepted | In the backlog: the user wants it tested | The user |
| rejected | The user does not want it tested | The user |
| testing | A test task exists (`rel_part_of` from the task) | The Seneschal or a Commander |
| preliminary | A first trial, not enough evidence yet | The Chancellor |
| robust | The five criteria are met; the idea is confirmed or refuted | The Chancellor |
| inconclusive | Dropped without a conclusion; the lesson goes in `memory/lessons.md` | The user |

A robust idea gets an evidence pack (skill `prepare-evidence-pack`). It enters the user's knowledge base only after the user seals the pack; the idea's `rel_produces` then points to the new note.

## Criteria of a robust idea

1. Protocol and success criterion written before the trial.
2. Reproducible: commit of the code, version of the data, seed, command.
3. Compared with a reference.
4. Repeated (several samples or seeds) or with a quantified uncertainty.
5. Evidence checked by the Chancellor.

A robustly refuted idea also counts: a solid negative result is knowledge.

## Backlog and quota

An accepted idea carries a `cost` (S, M, L) and a `preferred_harness`. When the quota module is on and a subscription is underused before its reset, the Seneschal puts these ideas forward first (skill `propose-backlog`). It launches nothing without the user.
