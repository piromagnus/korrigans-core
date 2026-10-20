---
summary: "How the household improves itself: forms of extension, the cycle drafts -> checked -> active, the registry."
---
# Extensions: how the household improves itself

An extension adds a capability to the agents. Four forms, from the safest to the riskiest:

| Form | Where (in the workspace) | Read by |
| --- | --- | --- |
| Skill (instructions and scripts, Agent Skills format `SKILL.md`) | `skills/<name>/` | Every harness, through the generated `.agents/skills/` (and `.claude/skills`) |
| Local script | `scripts/<name>.py` or `.sh`, or the `scripts/` of a skill | Everyone, as `korrigans <name>` or through the shell |
| MCP server | `mcp/servers.toml` | Every harness, through the files written by `korrigans generate` |
| Harness-specific plugin (pi extension, Claude Code plugin, Hermes tool) | `harness/<name>/extensions/` | That harness only |

Always prefer the highest form in the table: a skill works on every harness, a plugin on one.

## The cycle

1. **Spot a need.** An agent stumbles twice on the same thing, or the Chronicler sees in the journal a task sent back, a repeated failure, a sequence of commands copied by hand. It writes `extensions/proposed/<name>.md` with the skill `improve-system`: the need, the tasks that show it, what exists already, the chosen form.
2. **Look for what exists before creating.** Vendor skills, the MCP registry, skill hubs, harness packages. Note the source, the license, the date of the last commit.
3. **Create or adapt, on a branch `extension/<name>`, in `extensions/drafts/<name>/`.** A skill has a "Check" section and, if possible, a test script.
4. **Check.**
   - A skill or script written by an agent, with no outside dependency: the Chancellor reads it and runs the test. If it passes, the extension becomes active and appears in the user's Morning Chronicle. It can be undone with `git revert`.
   - Any third-party code (MCP server, npm or pip package, downloaded skill, plugin): status `waiting-on-you` (decision). The user approves before any install. Malicious skills have circulated on public hubs.
   - Any change to the Rule, the permissions or the routing: the user only.
5. **Register** it in `extensions/registry.toml`, then run `korrigans generate` to reach every harness.
6. **Measure.** The Chronicler follows its use in the journal. An extension unused for a month is proposed for removal.

Never edit a generated file by hand; change the source, then `korrigans generate`.

## Extensions written by the harnesses themselves

Some harnesses can write their own skills. To keep them in this cycle, point their skill folder to `extensions/drafts/` with write approval on (for Hermes: `skills.create_dir` and `skills.write_approval`). For the others, the Rule requires drafts to go to `extensions/drafts/`, never directly to `skills/` or `.agents/skills/`.
