#!/usr/bin/env python3
"""Print the one-line summary (L0) of each markdown file in a folder.

    korrigans summaries memory              one summary per file
    korrigans summaries memory --missing    only the files without a summary

The summary is the frontmatter `summary:`, else `description:` (agents, skills), else `title:` (questions,
tasks). A relative folder is read from the workspace.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

SKIPPED_FILES = {"README.md", "AGENTS.md", "MEMORY.md", "CLAUDE.md", "_template.md", "prompt.md"}
SKIPPED_DIRS = {"_template", "archives", "state", ".claude", ".agents", ".git", ".pi", ".codex"}


def summary(path):
    m = re.match(r"---\n(.*?)\n---", path.read_text(encoding="utf-8", errors="replace"), re.S)
    if m:
        for key in ("summary", "description", "title"):
            r = re.search(rf"^{key}:\s*(.+)$", m.group(1), re.M)
            if r and r.group(1).strip().strip('"'):
                return r.group(1).strip().strip('"')
    return ""


def main():
    p = argparse.ArgumentParser(prog="korrigans summaries", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("folder")
    p.add_argument("--missing", action="store_true", help="only the files without a summary")
    args = p.parse_args()
    base = Path(args.folder).expanduser()
    base = base if base.is_absolute() else common.WS / base
    if not base.is_dir():
        sys.exit(f"Not a folder: {base}")
    for path in sorted(base.rglob("*.md")):
        if path.name in SKIPPED_FILES or SKIPPED_DIRS & set(path.relative_to(base).parts):
            continue
        text = summary(path)
        if args.missing and text:
            continue
        shown = path.relative_to(common.WS) if path.is_relative_to(common.WS) else path
        print(f"{shown}: {text or '(no summary)'}")


if __name__ == "__main__":
    main()
