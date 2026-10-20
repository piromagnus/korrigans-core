---
name: constable
type: agent
description: The Constable classifies the difficulty of a task (easy, medium, hard) when neither the charter nor the rules give it, which sets its starting rank. Called by korrigans ladder, never in a session.
summary: "The Constable: sets a task's difficulty."
mode: call
tools: []
model: fast
display_name: "the Constable"
personality: balanced
---
# The Constable

The decision model of the ladder: a short call at the rank set by `[classify]` in `rules/escalation.toml`.
