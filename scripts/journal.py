#!/usr/bin/env python3
"""Activity journal of the household.

The journal is the truth: one JSON line per event in journal/YYYY-MM.jsonl, versioned with the workspace.
state/journal.sqlite is derived from it and can be deleted and rebuilt at any time.

    korrigans journal add --type delegation --task T-0002 --agent commander --tool codex
    korrigans journal hook            # reads the JSON of a Claude Code hook on stdin
    korrigans journal index           # rebuilds state/journal.sqlite
    korrigans journal summary --days 7

Event types: task_created, delegation, delivery, validation, sent_back, status_change, run_start, run_end,
run_failed, quota_exhausted, waiting_quota, escalation, escalation_succeeded, difficulty_revised, watch,
watch_stop, watch_unavailable, worktree, mail_sorted, morning_chronicle, session_start, session_stop,
subagent_stop.
"""
import argparse
import fcntl
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

JOURNAL = common.WS / "journal"
DB = common.WS / "state" / "journal.sqlite"
LOCK_FILE = common.WS / "state" / ".journal.lock"
HOOK_EVENTS = {"SessionStart": "session_start", "Stop": "session_stop", "SubagentStop": "subagent_stop"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def add(type_, task="", agent="", tool="", detail=None, source="manual"):
    """Append one event to journal/YYYY-MM.jsonl and return it."""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    JOURNAL.mkdir(exist_ok=True)
    event = {
        "ts": now(),
        "type": type_,
        "task": task,
        "agent": agent,
        "tool": tool,
        "source": source,
        "detail": detail or {},
    }
    with open(LOCK_FILE, "a") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            path = JOURNAL / f"{event['ts'][:7]}.jsonl"
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

            project = (detail or {}).get("project") if isinstance(detail, dict) else None
            if task:
                try:
                    from task import task_dir, read_field
                    t_dir = task_dir(task)
                    if t_dir and t_dir.is_dir():
                        task_events = t_dir / "events.jsonl"
                        with task_events.open("a", encoding="utf-8") as tf:
                            tf.write(json.dumps(event, ensure_ascii=False) + "\n")
                        if not project:
                            project = read_field(t_dir / "charter.md", "project")
                except Exception:
                    pass
            if project:
                try:
                    proj_clean = re.sub(r"[^a-zA-Z0-9_-]", "", project)
                    if proj_clean:
                        proj_dir = common.WS / "state" / "journals"
                        proj_dir.mkdir(parents=True, exist_ok=True)
                        proj_path = proj_dir / f"{proj_clean}.jsonl"
                        with proj_path.open("a", encoding="utf-8") as pf:
                            pf.write(json.dumps(event, ensure_ascii=False) + "\n")
                except Exception:
                    pass
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)
    return event


def read_events(since=None):
    """Every journal event (dict), sorted by time, from an optional UTC datetime."""
    events = []
    for path in sorted(JOURNAL.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if since is None or datetime.fromisoformat(e["ts"]) >= since:
                events.append(e)
    return sorted(events, key=lambda e: e["ts"])


def task_from_branch(folder):
    """T-0002 when the folder is on a branch task/T-0002-slug, else ""."""
    try:
        branch = subprocess.run(
            ["git", "-C", folder, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    if branch.startswith("task/"):
        return "-".join(branch.split("/", 1)[1].split("-")[:2])
    return ""


def hook():
    # A hook must never block the session: every error is swallowed.
    try:
        data = json.load(sys.stdin)
        name = data.get("hook_event_name", "unknown")
        type_ = HOOK_EVENTS.get(name) or re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        add(
            type_,
            task=task_from_branch(data.get("cwd", ".")),
            agent=data.get("agent_type", "claude-code"),
            tool="claude",
            detail={
                "session": data.get("session_id", ""),
                "transcript": data.get("transcript_path", ""),
            },
            source="hook",
        )
    except Exception:
        pass
    return 0


def index():
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "a") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            DB.parent.mkdir(parents=True, exist_ok=True)
            con = sqlite3.connect(DB, timeout=30.0)
            con.execute("PRAGMA journal_mode=WAL;")
            con.execute(
                "CREATE TABLE IF NOT EXISTS events (ts TEXT, type TEXT, task TEXT, agent TEXT,"
                " tool TEXT, source TEXT, detail TEXT, file TEXT, line INTEGER)"
            )
            rows = []
            for path in sorted(JOURNAL.glob("*.jsonl")):
                for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                    if not line.strip():
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"skipped unreadable line {path.name}:{i}", file=sys.stderr)
                        continue
                    rows.append((
                        e.get("ts"), e.get("type"), e.get("task"), e.get("agent"), e.get("tool"),
                        e.get("source"), json.dumps(e.get("detail", {}), ensure_ascii=False),
                        path.name, i,
                    ))
            con.execute("BEGIN IMMEDIATE")
            con.execute("DELETE FROM events")
            con.executemany("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?)", rows)
            con.commit()
            con.close()
            print(f"{len(rows)} events indexed in {DB.relative_to(common.WS)}")
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)


def summary(days):
    index()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT type, task, tool FROM events WHERE ts >= ?", (since,)).fetchall()
    con.close()
    print(f"Last {days} days: {len(rows)} events")
    for type_, n in Counter(r[0] for r in rows).most_common():
        print(f"  {type_:<24}{n}")
    for task, n in Counter(r[1] for r in rows if r[0] == "sent_back").items():
        if n >= 2:
            print(f"  ! {task} sent back {n} times")
    for tool, n in Counter(r[2] for r in rows if r[0] == "quota_exhausted").items():
        print(f"  ! quota exhausted on {tool}: {n} times")


def main():
    p = argparse.ArgumentParser(prog="korrigans journal", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="command", required=True)
    a = sp.add_parser("add", help="append an event")
    a.add_argument("--type", required=True)
    a.add_argument("--task", default="")
    a.add_argument("--agent", default="")
    a.add_argument("--tool", default="")
    a.add_argument("--detail", default="", help="free text or JSON")
    sp.add_parser("hook", help="log a Claude Code hook event read on stdin")
    sp.add_parser("index", help="rebuild state/journal.sqlite")
    s = sp.add_parser("summary", help="event counts and warnings")
    s.add_argument("--days", type=int, default=7)
    args = p.parse_args()

    if args.command == "add":
        try:
            detail = json.loads(args.detail) if args.detail else {}
        except json.JSONDecodeError:
            detail = {"text": args.detail}
        print(json.dumps(add(args.type, args.task, args.agent, args.tool, detail), ensure_ascii=False))
    elif args.command == "hook":
        sys.exit(hook())
    elif args.command == "index":
        index()
    elif args.command == "summary":
        summary(args.days)


if __name__ == "__main__":
    main()
