---
id: project-<slug>
type: project
title: "<Project name>"
summary: "<purpose; one short line>"
status: active          # active, paused, watch, finished
intensity: background   # focus, background, watch
due: ""                 # absolute, checked date; never relative
todoist_section: ""     # todoist module only: the section of the task manager
tags: []                # from rules/tags.md
rel_involves: []        # ["[[people/<name>]]"]
rel_depends_on: []      # ["[[projects/<other>/project]]"]
rel_uses: []
rel_builds_on: []
source: "<where this comes from, date>"
---
# <Project name>
- Goal: <deliverable>.
- State: <dated fact; blocker if any>.
- Next: <one action; due date if relevant>.
- Limits: <essential exclusions/uncertainties; omit if none>.
- Resources: [<dataset>](../../resources/datasets/<slug>.md) · [<repo>](../../resources/repos/<slug>.md).
- Context: [decisions](decisions.md) · [rules](rules.md). Keep only existing links.

Backlog: `Household.base`, filtered on this project. Paths, formats and architecture belong in resource notes, not here. Remove template guidance and unused placeholders.
