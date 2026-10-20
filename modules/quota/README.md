# Module quota

Wages in tokens, honestly counted (article VIII of the Pact). This module tells the household how much of
each subscription is used in its current window, and warns when a window is about to reset while it is
still under-used. The Seneschal then proposes work from the backlog (skill `propose-backlog`, tasks with
`when: quota-free` and accepted ideas). It never switches to pay-as-you-go: when a quota is spent, the
korrigans rest.

Enable it with `modules = ["quota"]` in `korrigans.toml`, then copy the examples you need from
`rules/subscriptions.toml` (`korrigans which rules/subscriptions.toml`) into `rules/subscriptions.toml` in
your workspace and set the reset times.

- `korrigans usage state`: every subscription, its usage and where the number comes from.
- `korrigans usage alert`: only those to use before their reset (used by `korrigans daily` and `korrigans board`).
- `korrigans usage set chatgpt 45`: record a usage by hand when nothing can measure it.
- `korrigans usage statusline`: Claude Code's status line. In `~/.claude/settings.json`:
  `"statusLine": {"type": "command", "command": "korrigans usage statusline"}`. It records the 7-day usage
  that Claude Code reports.

State files live in `state/` (`usage-claude.json`, `usage-manual.json`), never versioned.
