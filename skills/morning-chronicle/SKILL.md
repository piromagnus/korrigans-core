---
name: morning-chronicle
description: Write the user's Morning Chronicle, dated and frozen - today's board, tasks, mail, requests and quota to use. Run by korrigans daily each morning, or on request. Used by the Seneschal.
---

The report `reports/YYYY-MM-DD.md` is written once a day and never changes afterwards. If it already exists, do not modify it: tell the user where it is.

1. Inputs, prepared by `korrigans daily` (or run them yourself, in this order):
   - `korrigans board --freeze` creates the report with today's board (waiting on you, to review, in progress, requests, quota, activity, health);
   - when the todoist module is on: `korrigans todoist today` writes the tasks due today or overdue (`state/todoist-YYYY-MM-DD.json`). If it is missing, write "Tasks unavailable: task manager unreachable", inventing nothing;
   - when the mail module is on: `mail/YYYY-MM-DD.md`, written just before by the Chamberlain;
   - when the quota module is on: `korrigans usage alert` (also saved in `state/usage-alert.txt`).
2. Complete the report, above the board, with these sections in this order (skip a section whose module is off):
   - `## Waiting on you`: decisions, reviews, evidence packs, blocking requests; five lines at most;
   - `## Today's tasks`: tasks due or overdue, most urgent first, with their owner (the user or an agent);
   - `## Mail`: the "For you" section of the mail summary, then the number of mails for information and ignored;
   - `## Quota to use`: only if `korrigans usage alert` flags a subscription; the candidates of the skill `propose-backlog`, put forward;
   - `## New ideas`: ideas captured since the last report, for the user to accept or reject;
   - `## Suggested priorities`: two to four lines for the day.
3. Log `korrigans journal add --type morning_chronicle --agent seneschal`.
4. Run by `korrigans daily`: do not commit, the script commits `reports/` and `mail/`. Run by hand: commit only those two folders, "chronicle of YYYY-MM-DD".
