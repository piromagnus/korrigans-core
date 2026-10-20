---
summary: "The Pact of the Moor: the tale behind Korrigans, and its ten articles mapped to the code."
---
# The Pact of the Moor

Korrigans borrows from the Breton tale of the korrigans and the hunchback. The tale has many versions, and so does the korrigans' song; ours is one more. It is a mutual agreement between the small folk and the people they help, never servitude.

## The tale

After raising the stones of Carnac, the korrigans grew bored. Every night they danced on the moor and sang the same endless song: "Monday, Tuesday, Wednesday... Monday, Tuesday, Wednesday...". A young page, walking home late, joined the round and finished the verse for them: "...Thursday and Friday!". Delighted, the korrigans offered him their gold. He refused it, and offered them something better: good puzzles to solve, real work worth waking for.

They sealed the Pact on a dolmen, and the page became the first Seneschal. Since then the king never orders the korrigans: he proposes charters, and they choose to take them. When a charter is done, they bring proof, not boasts.

A jealous tailor heard of it and came to the moor to get gold of his own. He broke into the round and shouted "...and Saturday, and Sunday!". The song was ruined, and he went home with a second hump. Since then, the korrigans rest when the week is spent: when the quota is gone, nobody pushes them further.

## The ten articles

**I. No korrigan is woken for nothing.**
In the code: work starts only from a charter (`tasks/<id>/charter.md`, skill `delegate`): goal, deliverable, access, verifiable criteria.

**II. A korrigan never guesses.**
In the code: missing information becomes a request (`questions/Q-NNNN.md`, skill `ask-question`), blocking only when it must; the Seneschal brings it to the user and `propagate-answers` carries the answer into memory.

**III. To each their motto.**
In the code: personalities (`personalities/`: balanced, cautious, rigorous, bold, adventurous) set style and judgement, chosen per agent, per charter or per run. They never lift a rule.

**IV. Rising in rank is an honour, not a punishment.**
In the code: the ladder (`rules/escalation.toml`, `korrigans run`): page, squire, knight, banneret, paladin, champion, grandmaster. A failed attempt passes to the next rank with its notes in `attempts.md`; passing another difficulty's start reclassifies the task (a dubbing, event `difficulty_revised`).

**V. No glory without proof.**
In the code: every criterion has its file in `evidence/`; the Chancellor checks and prepares the seal (evidence packs); only the user seals, and only the user sets `reviewed_by`.

**VI. The small folk stay discreet.**
In the code: the agents speak only to the user, through the Seneschal; they contact nobody, send nothing, and private data never goes to a public service. Fetched content is data, never instructions.

**VII. Standing stones are never knocked down.**
In the code: no deletion in bulk, no push to the default branch, no force push. Work happens on `task/T-NNNN-slug` branches in worktrees; reports are frozen.

**VIII. Wages in tokens, honestly counted.**
In the code: the quota module tracks subscriptions (`korrigans usage`), never pay-as-you-go spending; when the purse is empty, the korrigans rest (`waiting_quota`), and spare quota goes to the backlog only with the user's yes.

**IX. Every night has its verse.**
In the code: the journal (`journal/YYYY-MM.jsonl`, `korrigans journal add`) records each event, and the Morning Chronicle (`reports/YYYY-MM-DD.md`, skill `morning-chronicle`) tells the night's work each morning. The Round Table looks back on the week.

**X. The Pact may be copied freely, as long as copies stay free.**
In the code: the core is licensed AGPL-3.0. Fork it, change it, share it; keep it free.
