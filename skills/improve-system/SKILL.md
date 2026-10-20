---
name: improve-system
description: Propose, create or install an extension (skill, script, MCP server, plugin) when a need keeps coming back. Used by any agent that stumbles twice on the same thing, and by the Chronicler.
---

## When to use it

- The same sequence of commands was done by hand in two tasks.
- A task failed or was sent back for lack of a tool.
- The user asks for a new capability.

## Procedure

1. Check `extensions/registry.toml` and the skills already available (`korrigans which skills/<name>/SKILL.md`): the extension may already exist.
2. Write `extensions/proposed/<name>.md`:

```markdown
---
summary: "<the need in one sentence>"
status: proposed        # proposed, testing, active, refused
form: skill             # skill, script, mcp, plugin
origin: internal        # or a URL
---
# <name>
- Need: <one sentence>
- Tasks that show it: <ids>
- Existing found: <links, license, last commit> or none
- Choice: create / adapt / install, and why
- Check: <command or test that proves it works>
```

3. For an internal skill or script: write it in `extensions/drafts/<name>/` on a branch `extension/<name>`, with its Check section, then create a checking task for the Chancellor.
4. For third-party code, or a change to the rules: create a task set to `waiting-on-you` with reason `decision`, and stop. Nothing is installed before the user agrees.
5. Once validated: move it to `skills/<name>/` in the workspace (or add it to `mcp/servers.toml`), add its entry to `extensions/registry.toml`, run `korrigans generate`, commit, and log `korrigans journal add --type extension_activated --agent <you>`.

## Check

`korrigans generate --check` reports no extension missing from the registry.
