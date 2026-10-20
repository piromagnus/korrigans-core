---
name: prepare-evidence-pack
description: Prepare the evidence pack of a robust idea so the user can decide quickly whether to seal it into their knowledge base. Used by a Commander or the Seneschal when the Chancellor has found an idea robust.
---

1. Copy the evidence pack template (`korrigans which templates/task/evidence-pack.md`) to `tasks/<id>/evidence-pack.md` (the task that tested the idea).
2. The title is the claim as it would enter the knowledge base: one sentence, with its scope. A refuted idea gives a negative claim ("X does not improve Y under conditions Z").
3. The first screen reads in thirty seconds: proposed verdict, key number with its reference and its uncertainty, scope, intended use, confidentiality.
4. The five criteria: "yes" only with a link to the evidence. A single "no" means this is not an evidence pack: the idea stays preliminary.
5. "What could bring it down": two or three risks at most, honest.
6. "To go further": links to the protocol, the full results, the trace, the report, the Chancellor's verdict.
7. The idea moves to `status: robust`; the Seneschal presents the pack to the user. Leave `decision` and `reviewed_by` empty: only the user fills them.
8. When the user seals it (`decision: sealed`), bring the result into the user's knowledge base as the user and their house rules say, then fill the idea's `rel_produces` with the new note. On `revise` or `refused`, record the reason in the idea note and do nothing else.
