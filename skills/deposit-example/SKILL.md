---
name: deposit-example
description: Deposit a reusable result (interface, slides, figure, experiment script) in resources/examples with a short README. Used at the end of a task when the card says Reusable yes.
---

1. Check in `resources/catalog.md` that an equivalent example does not exist yet. If one does, improve it instead of adding another.
2. Copy the code into `resources/examples/<form>-<subject>/`, removing absolute paths, project data, names of people, and secrets. Replace the data with a small synthetic or public set.
3. Write the README in five lines:

```markdown
# <name>
What it does: <one or two sentences>
Run: `<one command>`
Origin: <project>, <task>, <date>
Dependencies: <packages>
Tags: <from rules/tags.md>
```

4. Run the README's command in a clean environment. If it fails, fix it before committing.
5. Add a line to `resources/catalog.md` and commit.
