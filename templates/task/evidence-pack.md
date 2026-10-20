---
type: evidence-pack
summary: "<the claim in one sentence>"
idea: "[[ideas/<idea>]]"
task: T-0000
proposed_verdict: confirmed     # confirmed or refuted
level: robust
checked_by: chancellor
decision: ""                    # set by the user only: sealed, revise, refused
decision_date: ""               # set by the user only
reviewed_by: ""                 # set by the user only; agents never fill it
---
# <the claim in one sentence, as it would enter the knowledge base>

> **Proposed verdict: confirmed.** <One sentence with the key number, its reference and its uncertainty.>
> **What you decide:** seal it into your knowledge base, ask for a revision, or refuse.

## On one screen

| | |
| --- | --- |
| Result | <metric, value, unit> against <reference> (<uncertainty, number of repetitions>) |
| Scope | <data, conditions; what the result does not say> |
| Intended use | <publication, decision, or none> |
| Confidentiality | private |

## The five criteria

| Criterion | Met | Where to check |
| --- | --- | --- |
| Protocol written before the trial | yes / no | link, commit date |
| Reproducible (code, data, seed, command) | yes / no | `evidence/command.txt` |
| Compared with a reference | yes / no | results table |
| Repeated, or uncertainty quantified | yes / no | `evidence/runs.csv` |
| Checked by the Chancellor | yes / no | `verdict.md` |

## What could bring it down

Two or three risks at most, each with what was done to rule it out.

## To go further

- Protocol: ...
- Full results: `evidence/...`
- Run trace: `trace-...log`
- The korrigan's report: `report.md`
- The Chancellor's verdict: `verdict.md`
