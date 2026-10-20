---
id: T-0000
type: task
title: ""
summary: ""
project: ""
task_type: code         # code, research, writing, proofreading, admin, mail, request
status: todo            # todo, in-progress, to-review, done, waiting-on-you
waiting_on: ""          # decision, review, action, info
when: ""                # empty, or quota-free (backlog task, run when quota is left)
cost: ""                # S, M, L
difficulty: ""          # easy, medium, hard (rules/escalation.toml); empty = set by korrigans ladder classify
rank: ""                # empty = the ladder from the difficulty's start; else one forced rank, e.g. knight or mid:high
verify: ""              # command that must pass at the end, e.g. "pytest -q"; if it fails, the next rank takes over
owner: ""               # user, seneschal, commander, korrigans/code, korrigans/research, chamberlain
todoist: ""             # id of the matching task in your task manager, if any
created: YYYY-MM-DD
assigned_to: ""         # role@harness:rank, set by korrigans run
workdir: ""             # worktree or working folder
access: []              # ["~/data/x:read", "~/code/y:write"]; only paths listed in memory/global/repos-data.md
personality: ""         # empty = the korrigan's own (IDENTITY.md); else cautious, rigorous, bold... (personalities/)
rel_part_of: []
rel_tests: []
rel_produces: []
---
# Charter

## Goal

## Deliverable

## Access

What the korrigan may read or write besides the task folder, and why (field `access`). Data: read only. Another repository in write mode: only if `memory/global/repos-data.md` allows it.

## Criteria and evidence

| # | Verifiable criterion | Expected evidence |
| --- | --- | --- |
| 1 |  |  |

## Needed context

## Limits
