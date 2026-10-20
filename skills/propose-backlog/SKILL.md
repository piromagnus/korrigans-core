---
name: propose-backlog
description: When a subscription is underused before its reset, put forward one to three backlog ideas or tasks that fit in the remaining quota. Used by the Seneschal when the quota module is on.
---

1. `korrigans usage alert --json`. Nothing to do if the list is empty.
2. For each subscription flagged, list the candidates:
   - ideas with `status: accepted` (`ideas/`), with their `cost` and `preferred_harness`;
   - tasks with `status: todo` and `when: quota-free` (`tasks/`).
3. Sort: projects with intensity `focus` first, then `background`, then `watch`; at equal priority, the cost that fits what is left (S if less than 12 hours before the reset, M or L otherwise). Keep one to three candidates that can be routed to the harnesses of that subscription (`rules/routing.toml`).
4. Put them forward, without launching anything: at the top of the Morning Chronicle (section "Quota to use") and in your answer to the user, one line per candidate: title, project, cost, harness, what will be ready afterwards.
5. On the user's yes: an idea becomes a test task (skill `delegate`, `rel_part_of` toward the project, `rel_tests` taken from the idea, the idea moves to `testing`); a quota-free task is launched with `korrigans run <id> --harness <harness>`.
