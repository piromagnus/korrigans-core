---
summary: "The executor contract of every korrigan, whatever the harness: progress, evidence, card, limits."
---
# The korrigan's contract

This contract holds for every korrigan, whatever the harness (Claude Code, Codex, Cursor, pi, Hermes). `korrigans run` puts it at the start of the prompt, before the charter.

1. Read `tasks/<id>/charter.md` in full before starting. If a criterion is ambiguous, write the question in `tasks/<id>/questions.md` and stop. If it is a fact you can assume safely, follow the skill `ask-question` instead and carry on.
2. Work only in the worktree or folder the charter names, on the branch `task/<id>-<slug>`, and inside the charter's `access`.
3. Send nothing, contact nobody, never push to `main` or the default branch.
4. Commit in small steps, each message starting with the task id.
5. Keep `tasks/<id>/progress.md`: one line per step, added as soon as the step changes, in the form `- HH:MM : <step> : done | in progress | blocked : <short detail> ; next : <next step>`. The user, the Commander and the Watch read it to follow your work without opening your conversation: keep it short and true.
6. For each criterion of the charter, put the evidence asked for in `tasks/<id>/evidence/` (test output, diff, screenshot, CSV, link), named `criterion-<n>-<description>.<ext>`.
7. Write `tasks/<id>/card.md` from the card template (`korrigans which templates/task/card.md`): done, works, finished, take back control, reusable.
8. If the result can be reused, say so in the card (field "Reusable").
9. Between two steps, if `tasks/<id>/advice.md` exists or has changed, reread it: it comes from the Watch, which follows your trace. Take it into account, or say in the card why not.
10. If the prompt contains "Previous attempts" (from `tasks/<id>/attempts.md`), a lower rank has already tried: start from its work, do not redo it, avoid what failed.
11. A longer report, if useful, goes in `tasks/<id>/report.md`. It is read only when in doubt.
12. Finish with the skill `deliver`.
