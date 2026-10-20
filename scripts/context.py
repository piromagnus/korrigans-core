#!/usr/bin/env python3
"""How complete the household's context is: the Vigil's progress, chapter by chapter.

    korrigans context            a bar per chapter and the next thing to settle
    korrigans context --json     the same, for an agent

A "(vigil: <chapter>)" or "<!-- vigil: <chapter> -->" mark in a workspace file means "still to settle".
The Vigil skill removes it once the user has answered.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WS, config, read_note  # noqa: E402

CHAPTERS = [
    ("name", "1. Names", "the Seneschal's name and your language"),
    ("you", "2. You and your team", "who you are, who you work with"),
    ("projects", "3. Projects", "what the household works on"),
    ("needs", "4. Needs and audience", "what to delegate, what never, for whom"),
    ("data", "5. Code and data", "where repositories and data live, and what agents may touch"),
    ("tools", "6. Tools and integrations", "harnesses, subscriptions, modules"),
]
MARK = re.compile(r"vigil:\s*(name|you|projects|needs|data|tools)\b")


def unmarked(rel, chapter):
    p = WS / rel
    return p.exists() and not any(m == chapter for m in MARK.findall(p.read_text(encoding="utf-8")))


def table_rows(rel):
    p = WS / rel
    if not p.exists():
        return 0
    rows = [l for l in p.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
    return max(0, len(rows) - 2)


def checks():
    """(chapter, done, what) for every item."""
    user = config().get("user") or "people/me.md"
    fm, _ = read_note(WS / user)
    people = [p for p in (WS / "people").glob("*.md") if p.name != "README.md"] if (WS / "people").is_dir() else []
    projects = sorted((WS / "projects").glob("*/project.md"))
    filled = [p for p in projects if read_note(p)[0].get("summary") and "vigil:" not in p.read_text(encoding="utf-8")]
    yield "name", (WS / "agents" / "seneschal" / "IDENTITY.md").exists(), "name your Seneschal (agents/seneschal/IDENTITY.md)"
    yield "name", unmarked("korrigans.toml", "name"), "choose your language (korrigans.toml)"
    yield "you", unmarked(user, "you"), f"describe yourself ({user})"
    yield "you", len(people) >= 2 or fm.get("team") == "solo", "add your teammates to people/ (or note team: solo)"
    yield "projects", bool(projects), "describe a first project (projects/<name>/project.md)"
    yield "projects", bool(projects) and len(filled) == len(projects), "give every project a summary and a status"
    yield "needs", unmarked("USER.md", "needs"), "say what you always, never and prefer (USER.md)"
    yield "needs", unmarked("rules/house-rules.md", "needs"), "write your house rules (rules/house-rules.md)"
    yield "data", table_rows("memory/global/repos-data.md") > 0, "list repositories and data (memory/global/repos-data.md)"
    yield "data", (WS / "memory" / "global" / "registry.md").exists() and unmarked("memory/global/registry.md", "data"), \
        "note where your tools and folders are (memory/global/registry.md)"
    yield "tools", unmarked("memory/global/detected.md", "tools"), "confirm what install detected (memory/global/detected.md)"
    yield "tools", unmarked("korrigans.toml", "tools"), "choose your modules (korrigans.toml)"


def report():
    items = list(checks())
    chapters = []
    for key, title, about in CHAPTERS:
        mine = [(done, what) for k, done, what in items if k == key]
        chapters.append({"chapter": key, "title": title, "about": about, "done": sum(d for d, _ in mine),
                         "total": len(mine), "missing": [w for d, w in mine if not d]})
    done = sum(c["done"] for c in chapters)
    total = sum(c["total"] for c in chapters)
    return {"percent": round(100 * done / total) if total else 100, "chapters": chapters,
            "next": next((m for c in chapters for m in c["missing"]), None)}


def bar(done, total, width=12):
    full = round(width * done / total) if total else width
    return "#" * full + "." * (width - full)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    r = report()
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    print(f"The Vigil: {r['percent']}% of the household's context is settled\n")
    for c in r["chapters"]:
        print(f"  [{bar(c['done'], c['total'])}] {c['title']:<26} {c['done']}/{c['total']}")
    print(f"\nNext: {r['next']}" if r["next"] else "\nEverything is settled. The Seneschal can be dubbed.")


if __name__ == "__main__":
    main()
