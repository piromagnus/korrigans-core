---
summary: "Templates born from several similar examples, after the user's approval."
---
# Templates

Empty at first. A template is born from several similar examples, after the user's approval.

Structure of a template:

```text
<name>/
  README.md       when to use it, parameters, limits, version
  copier.yml      questions asked at instantiation
  template/       generic code, without project data
  example.yml     answers that produce example/
  example/        generated from template/, never edited by hand
  SKILL.md        how an agent instantiates and adapts it
```

Instantiate: `copier copy resources/templates/<name>/template <destination>` (copier is third-party code: the user approves installing it).
