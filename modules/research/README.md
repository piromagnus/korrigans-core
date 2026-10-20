# Module research

Adds Blondel, the minstrel who went from castle to castle until he found his king: he goes out to find
sources and brings them back to the library. The library is your knowledge base (papers, notes on them,
results you have sealed): a folder of markdown notes, which can live in your Obsidian notes.

Enable it with `modules = ["research"]` in `korrigans.toml`, and name your library:

```toml
[research]
library = "library"          # relative to the workspace, or an absolute path
```

- Skill `find-sources`: search the library first, then the web through cheap subagents if you allow it for
  the charter, and record every source used with its link and dates in `tasks/<id>/sources.md`.
- `korrigans index`: index the workspace and the library with [qmd](https://github.com/tobi/qmd) if it is
  installed, so agents can run `qmd search`.
- Results (a claim, a measure) enter the library only after you seal their evidence pack.

If your library has its own note types (paper, concept, claim, experiment...), declare the relations you use
in `rules/relations.yaml` of your workspace so that `korrigans check` accepts links to them.
