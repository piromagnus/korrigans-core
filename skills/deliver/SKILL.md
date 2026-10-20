---
name: deliver
description: Finish a task - put one piece of evidence per criterion, write the card, set the task to to-review. Used by every korrigan at the end of a task.
---

1. For each criterion of the charter, check that evidence exists in `tasks/<id>/evidence/`, in the announced format. If one is missing, produce it or write why it is impossible.
2. Copy the card template (`korrigans which templates/task/card.md`) to `tasks/<id>/card.md` and fill it in. One line per field, no jargon: the user must understand it in ten seconds. Cite any working assumption (`assumption Q-NNNN`).
3. Add a last line to `tasks/<id>/progress.md`: delivered.
4. Set the status: `korrigans task status <id> to-review`. When the todoist module is on, the task manager follows.
5. The script logs the delivery. Never set `reviewed_by` and never set `done` yourself.
