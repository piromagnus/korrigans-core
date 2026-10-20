---
name: ask-question
description: Ask the user a request when information is missing, instead of inventing it; block only when it is indispensable. Used by every agent of the household.
---

1. Check that the answer does not exist already: `grep -ril "<keywords>" questions/ memory/ projects/ people/` and `korrigans summaries questions`. If an open request covers it, add your case to it instead of creating a new one.
2. Create `questions/Q-NNNN.md` (the next free number) from the request template (`korrigans which templates/question.md`):
   - `title`: the question, answerable in one line, with the options if you know them;
   - `summary`: the same in a few words;
   - `blocking: yes` only if the next step is impossible or risky without the answer;
   - `assumption`: what you assume in order to carry on (required when not blocking);
   - `propagate_to`: the files where the answer must be written (registry, person, project, preferences);
   - `asked_by`, `asked_on`, `project`, `task` when they apply.
3. Not blocking: carry on with the assumption and cite it in your card ("assumption Q-NNNN"). Blocking: set the task to `waiting-on-you` with reason `info` (`korrigans task status <id> waiting-on-you --reason info`) and stop cleanly.
4. Never contact anyone but the user to get the information. The Seneschal brings the request to the user.
