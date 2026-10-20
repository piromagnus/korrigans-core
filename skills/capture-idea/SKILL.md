---
name: capture-idea
description: Turn an idea of the user (message, mail, passing remark) into an idea note in ideas/, never into a task. Used by the Seneschal.
---

1. Check whether the idea already exists: `grep -ril "<keywords>" ideas/` and `korrigans summaries ideas`. Also look in the user's knowledge base: the idea may have been tested already.
2. Copy the idea template (`korrigans which templates/idea.md`) to `ideas/YYYY-MM-DD-<slug>.md` and fill it in: `status: proposed`, project and `rel_part_of`, estimated cost (S, M, L), source (who said it, when), and links to the knowledge base when they exist (`rel_tests` toward what it tests, `rel_builds_on` toward its starting point).
3. Launch nothing. List new ideas in the next Morning Chronicle; the user chooses which ones become `accepted` (backlog).
4. `korrigans check`.
