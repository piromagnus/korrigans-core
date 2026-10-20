---
name: propagate-answers
description: Carry the user's answers to open requests into the household's memory, then close the requests. Used by the Seneschal as soon as the user answers.
---

1. For each request the user answered (in the conversation or in `answer:`): write the answer in `answer:`, dated, with its source ("the user, conversation of YYYY-MM-DD"), then `status: answered`.
2. Carry the fact into each file of `propagate_to`, at the right place, dated and sourced: a line of the registry, a field of the project (`due`, next step), a person note (`people/`), a line of `memory/global/repos-data.md` only if the user dictated it (the file is theirs), a preference. A preference goes in `memory/global/preferences.md` (dated history) and, if it changes how to work with the user, in `USER.md` as a short dated rule (the old one is marked "replaced"). Replace the working assumption wherever it was written.
3. If the answer changes a decision, add it to `projects/<project>/decisions.md`.
4. Unblock the tasks in `waiting-on-you` with reason `info` that waited on this request (`korrigans task status <id> in-progress`).
5. `status: closed`, then `korrigans check` and a commit "requests: Q-NNNN propagated".
