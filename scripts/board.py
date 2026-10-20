#!/usr/bin/env python3
"""The board: what waits for the user, what is running, what is breaking.

    korrigans board            rewrite Board.md (live note, git-ignored)
    korrigans board --freeze   create reports/YYYY-MM-DD.md with today's board, for the Morning Chronicle;
                               never rewrites an existing report (a report is frozen at its date)
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from check import frontmatter  # noqa: E402
from journal import read_events  # noqa: E402

WS = common.WS
INTENSITY = {"focus": 0, "background": 1, "watch": 2}
YES = ("yes", "true")


def link(path, text):
    return common.link_to(path, text)


def cell(text):
    """A link inside a markdown table: escape the pipe."""
    return text.replace("|", "\\|")


def notes(folder, pattern="*.md", type_=None):
    for path in sorted((WS / folder).glob(pattern)):
        if path.name.startswith("_") or "_template" in path.parts:
            continue
        fm = frontmatter(path)
        if fm and (type_ is None or fm.get("type") == type_):
            yield path, fm


def run(*args):
    """Run `korrigans <args>` in the workspace."""
    env = os.environ | {"KORRIGANS_WORKSPACE": str(WS), "KORRIGANS_CORE": str(common.CORE)}
    return subprocess.run([sys.executable, str(common.CORE / "scripts" / "cli.py"), *args], cwd=WS, env=env,
                          capture_output=True, text=True, timeout=120)


def korrigans(*args):
    """(exit code, last line of output) of `korrigans <args>`."""
    try:
        r = run(*args)
    except (OSError, subprocess.SubprocessError) as e:
        return 1, str(e)
    lines = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    return r.returncode, lines[-1].strip() if lines else ""


def usage_state():
    """Subscriptions from `korrigans usage state --json` (module quota), or None if it failed."""
    try:
        r = run("usage", "state", "--json")
        return json.loads(r.stdout) if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None


def sections():
    tasks = list(notes("tasks", "T-*/charter.md", "task")) + list(notes("tasks", "*/T-*/charter.md", "task"))
    ideas = list(notes("ideas", type_="idea"))
    questions = [(p, fm) for p, fm in notes("questions", type_="question") if fm.get("status") != "closed"]
    projects = {p.parent.name: fm for p, fm in notes("projects", "*/project.md", "project")}
    s = []

    waiting = [(p, fm) for p, fm in tasks if fm.get("status") == "waiting-on-you"]
    review = [(p, fm) for p, fm in tasks if fm.get("status") == "to-review"]
    packs = [p for p, _ in tasks if (p.parent / "evidence-pack.md").exists()
             and not frontmatter(p.parent / "evidence-pack.md").get("decision")]   # set by the user only
    s.append("## Waiting for you\n")
    lines = [f"- {link(p, fm.get('title') or p.parent.name)}: {fm.get('waiting_on') or 'to be specified'}"
             for p, fm in waiting]
    lines += [f"- To review: {link(p.parent / 'card.md', fm.get('title') or p.parent.name)}" for p, fm in review
              if (p.parent / "card.md").exists()]
    lines += [f"- Evidence pack to seal: {link(p.parent / 'evidence-pack.md', p.parent.name)}" for p in packs]
    blocking = [(p, fm) for p, fm in questions if str(fm.get("blocking")).lower() in YES]
    lines += [f"- Blocking request: {link(p, fm.get('title') or p.stem)}" for p, fm in blocking]
    s.append("\n".join(lines) or "Nothing.")

    s.append("\n## In progress\n")
    last_seen = {}
    for ev in read_events():
        if ev.get("task"):
            last_seen[ev["task"]] = ev["ts"]
    now = datetime.now(timezone.utc)
    lines = []
    for p, fm in tasks:
        if fm.get("status") != "in-progress":
            continue
        ident = str(fm.get("id") or p.parent.name[:6])
        age = ""
        if ident in last_seen:
            days = (now - datetime.fromisoformat(last_seen[ident])).days
            age = f", last sign {days} d ago" + (" (stuck?)" if days >= 3 else "")
        lines.append(f"- {link(p, fm.get('title') or p.parent.name)}: {fm.get('assigned_to') or 'not delegated'}{age}")
    s.append("\n".join(lines) or "Nothing.")

    s.append("\n## Projects\n")
    s.append("| Project | Intensity | Status | Due | Open tasks |\n| --- | --- | --- | --- | --- |")
    for name, fm in sorted(projects.items(), key=lambda x: (INTENSITY.get(x[1].get("intensity"), 9), x[0])):
        open_tasks = sum(1 for _, t in tasks if common.target(t.get("project")) == name and t.get("status") != "done")
        note = cell(link(WS / "projects" / name / "project.md", fm.get("title") or name))
        s.append(f"| {note} | {fm.get('intensity', '')} | {fm.get('status', '')} | {fm.get('due') or 'not set'} | "
                 f"{open_tasks} |")

    s.append(f"\n## Open requests ({len(questions)})\n")
    questions.sort(key=lambda x: str(x[1].get("blocking")).lower() not in YES)
    s.append("\n".join(f"- {'**blocking** ' if str(fm.get('blocking')).lower() in YES else ''}"
                       f"{link(p, fm.get('title') or p.stem)}" for p, fm in questions[:10]) or "None.")
    if len(questions) > 10:
        s.append(f"- ... and {len(questions) - 10} more in `questions/`")

    s.append("\n## Quota\n")
    if "quota" in common.modules():
        rows = usage_state()
        if rows is None:
            s.append("- `korrigans usage state` failed")
        elif not rows:
            s.append("- No subscription in rules/subscriptions.toml")
        for r in rows or []:
            used = "?" if r["usage"] is None else f"{r['usage']:.0%}"
            mark = " **use before the reset**" if r["use_before_reset"] else ""
            s.append(f"- {r['subscription']}: {used} ({r['source']}), reset in {r['hours_to_reset']:.0f} h"
                     f"{' (assumed)' if r['reset_assumed'] else ''}{mark}")
    else:
        s.append("- Not tracked (module quota not enabled)")
    backlog = [(p, fm) for p, fm in ideas if fm.get("status") == "accepted"]
    backlog += [(p, fm) for p, fm in tasks if fm.get("when") == "quota-free" and fm.get("status") == "todo"]
    s.append(f"- Backlog ready: {len(backlog)} idea(s) or quota-free task(s)")

    s.append("\n## Ideas\n")
    count = Counter(fm.get("status", "?") for _, fm in ideas)
    s.append(", ".join(f"{n} {status}" for status, n in count.most_common()) or "No idea yet.")

    s.append("\n## Activity of the last 7 days\n")
    events = read_events(now - timedelta(days=7))
    by_type = Counter(ev.get("type") for ev in events)
    s.append(f"- Runs: {by_type['run_start']}, finished: {by_type['run_end']}, failed: {by_type['run_failed']}")
    s.append(f"- Deliveries: {by_type['delivery']}, validations: {by_type['validation']}, "
             f"sent back: {by_type['sent_back']}")
    quotas = Counter(ev.get("tool") for ev in events if ev.get("type") == "quota_exhausted")
    if quotas:
        s.append("- Quota exhausted: " + ", ".join(f"{t} ({n})" for t, n in quotas.items()))

    s.append("\n## Health\n")
    code, line = korrigans("check")
    s.append(f"- Graph: {'ok' if code == 0 else 'errors'} ({line})")
    code, line = korrigans("generate", "--check")
    s.append(f"- Extensions registry: {'ok' if code == 0 else 'to fix'} ({line})")
    try:
        r = run("summaries", ".", "--missing")
        missing = [l.strip() for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        missing = None
    s.append("- Missing summaries: " + ("not checked" if missing is None else
                                        f"{len(missing)} (e.g. {missing[0]})" if missing else "none"))
    return "\n".join(s) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--freeze", action="store_true")
    args = p.parse_args()
    day = date.today().isoformat()
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    if args.freeze:
        path = WS / "reports" / f"{day}.md"
        if path.exists():
            sys.exit(f"reports/{day}.md already exists: a report is frozen, it is never rewritten.")
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"---\ntype: report\ndate: {day}\nsummary: \"Morning Chronicle of {day}, frozen.\"\n---\n"
                        f"# Morning Chronicle, {day}\n\n## Board (frozen at {stamp})\n\n{sections()}",
                        encoding="utf-8")
    else:
        path = WS / "Board.md"
        content = (f"---\nsummary: \"Live board of the household, rewritten by korrigans board.\"\n---\n"
                   f"# Board\n\nUpdated at {stamp}. Frozen version of each morning: `reports/`.\n\n"
                   f"{sections()}")
        tmp = tempfile.NamedTemporaryFile("w", dir=path.parent, delete=False, encoding="utf-8")
        try:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, path)
        except Exception:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise
    print(path.relative_to(WS))


if __name__ == "__main__":
    main()
