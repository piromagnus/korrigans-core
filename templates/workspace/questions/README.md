---
summary: "The agents' requests for the user, one per file; the Seneschal groups them and carries the answers into memory."
---
# Requests for the user

- One request per file `Q-NNNN.md`, created with the skill `ask-question` (template `templates/question.md`).
- `blocking: yes` only if the next step is impossible or risky without the answer; otherwise the agent writes its `assumption` and carries on.
- To answer: fill `answer:` (or answer the Seneschal, who does it), set `status: answered`. The skill `propagate-answers` carries the answer into the files of `propagate_to`, then sets `status: closed`.
- The Requests view of `Household.base` lists open requests, blocking first.
