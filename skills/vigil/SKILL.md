---
name: vigil
description: The Vigil, the welcome conversation of a new household. The Seneschal asks the user one question at a time, in six chapters, and writes each answer in the workspace at once. Use when BOOTSTRAP.md exists, when the user says "start the vigil" or "continue the vigil", or when `korrigans context` is below 100% and the user has time.
---
# The Vigil

Before being dubbed, a knight keeps a vigil of arms. Here, the Seneschal keeps one with the user: a relaxed
conversation that gives the household everything it needs to work, chapter by chapter. It should feel like
the opening of a game, not a form.

## How to run it

1. Run `korrigans context` and start at the first chapter that is not complete. Show the bars at the start
   and after each chapter: the user sees the household fill up.
2. Ask **one question at a time**, in the user's language, with 2 to 4 suggested answers the user can pick
   (number them), plus "something else". Use what install detected (`memory/global/detected.md`) to
   suggest: "I found `~/code/field-tools`: is it one of your projects?"
3. **Write each answer right away** in the file listed below, then remove the matching `vigil:` mark from
   that file. Never keep an answer only in the conversation.
4. At the end of each chapter: one-line recap of what you wrote, `git add -A && git commit -m "vigil: <chapter>"`
   in the workspace (if it is a git repository), then `korrigans context`.
5. **Real work comes first.** If the user brings a real task mid-way, handle it (or delegate it), then offer
   to resume the Vigil where it stopped. The Vigil can span several sessions.
6. **Unknown is fine.** If the user does not know or prefers to answer later, write a request in
   `questions/` (skill `ask-question`, `blocking: no`), keep the mark, and move on.
7. **Sensitive answers are read back** before saving (health, people's opinions, money, anything private):
   "I'll write this in people/sam.md: '...'. OK?" Nothing secret is ever written: tokens and passwords go in
   `.env` by the user's own hand; you only check the file exists.
8. Keep it light: short sentences, a little ceremony at chapter ends ("Chapter 2 sealed."), never a wall of
   questions.

## The six chapters

| Chapter | Ask about | Write in |
| --- | --- | --- |
| 1. Names | Their language. The Seneschal's name (default "Lucan", after Sir Lucan the Butler; suggest 2 or 3 others) and how to address the user. Optionally a personality for the Seneschal (`personalities/`). | `korrigans.toml` (`language`), `agents/seneschal/IDENTITY.md` in the workspace (copy the core file with `korrigans which agents/seneschal/IDENTITY.md`, change `display_name`, `personality`) |
| 2. You and your team | Their role, field, place of work; the people they work with (role, how they relate to each project). Agents never contact these people: say so. | the user's person note (`user` in `korrigans.toml`), `people/<name>.md` from `templates/person.md`; `team: solo` in the user's note if alone |
| 3. Projects | Each project: one-line summary, status (active, paused, watch, finished), intensity (focus, background, watch), due date, people involved. Offer a Commander for focus projects (copy `agents/commanders/_template/`, Round Table name). | `projects/<p>/project.md` from `templates/project.md`, `projects/<p>/decisions.md`, `agents/commanders/<p>/` |
| 4. Needs and audience | What they want delegated first, what must never be done for them, who reads their work (advisor, clients, reviewers), how they like reports (length, time, language). | `USER.md` (Always, Never, Prefer, dated), `rules/house-rules.md`, `memory/global/preferences.md` |
| 5. Code and data | For each project: repositories and data folders, and what agents may do there (read, write on task branches, nothing). Where tools and important folders are. | `memory/global/repos-data.md` (one row per repo or data folder), `memory/global/registry.md` |
| 6. Tools and integrations | Confirm the detected harnesses and subscriptions; which modules to enable (`quota`, `todoist`, `mail`, `research`) and their settings; whether to install the Morning Chronicle timer. | `memory/global/detected.md` (confirm or correct each line), `korrigans.toml` (`modules`, module tables), module rules files such as `rules/subscriptions.toml` |

After chapter 6, run `korrigans generate` (modules and house rules change `AGENTS.md`), then `korrigans check`.

## The dubbing

When `korrigans context` reaches 100%:

1. Tell the user, in one short paragraph, what the household now knows and what it will do tonight.
2. Read them the Pact of the Moor in three lines (see `docs/lore.md` in the core): the korrigans work by
   agreement, they ask rather than guess, and nothing is sealed without the user.
3. Move `BOOTSTRAP.md` to `memory/vigil.md`, add the date, commit "vigil: the Seneschal is dubbed".
4. Suggest one first real task, small enough to finish tonight.
