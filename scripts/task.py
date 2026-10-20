#!/usr/bin/env python3
"""Create and follow task charters (tasks/T-NNNN-slug/charter.md or tasks/<project>/T-NNNN-slug/charter.md).

    korrigans task new "Inventory of the sequences" --project demo --type code
    korrigans task new "Tidy the backlog" --project demo --type admin --when quota-free
    korrigans task worktree T-0002 --repo ~/code/demo
    korrigans task status T-0002 to-review
    korrigans task status T-0002 waiting-on-you --reason decision
    korrigans task list
"""
import argparse
import fcntl
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from journal import add  # noqa: E402

TASKS = common.WS / "tasks"
CHARTER = "charter.md"
STATUSES = ["todo", "in-progress", "to-review", "done", "waiting-on-you"]
REASONS = ["decision", "review", "action", "info"]
WHEN = ["", "quota-free"]


def slug(text, length=40):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text[:length].rstrip("-")


def task_dir(ident):
    """Folder of a task, from its id (T-0002) or its full folder name."""
    if Path(ident).is_dir():
        return Path(ident).resolve()
    found = (sorted(TASKS.glob(f"{ident}-*")) + sorted(TASKS.glob(ident)) +
             sorted(TASKS.glob(f"*/{ident}-*")) + sorted(TASKS.glob(f"*/{ident}")))
    if not found:
        found = [p for p in TASKS.rglob(f"{ident}*") if p.is_dir() and (p.name == ident or p.name.startswith(f"{ident}-"))]
    if not found:
        sys.exit(f"Task not found: {ident} (in {TASKS})")
    return sorted(found)[0]


def next_id(lock_fd=None):
    if lock_fd is not None:
        numbers = [int(m.group(1)) for d in TASKS.rglob("T-*") if d.is_dir() and (m := re.match(r"^T-(\d{4})", d.name))]
        return f"T-{max(numbers, default=0) + 1:04d}"
    lock_file = common.WS / "state" / ".task-id.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            numbers = [int(m.group(1)) for d in TASKS.rglob("T-*") if d.is_dir() and (m := re.match(r"^T-(\d{4})", d.name))]
            return f"T-{max(numbers, default=0) + 1:04d}"
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def read_field(charter, key):
    """Value of a frontmatter field of the charter, without quotes or trailing comment; "" if absent."""
    m = re.search(rf"^{key}:\s*(.*?)\s*(#.*)?$", Path(charter).read_text(encoding="utf-8"), re.M)
    return m.group(1).strip('"') if m else ""


def write_field(charter, key, value):
    """Set a frontmatter field, keeping its trailing comment. A missing field is added to the frontmatter."""
    charter = Path(charter)
    lock_file = charter.parent / f".{charter.name}.lock"
    with open(lock_file, "a") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            text = charter.read_text(encoding="utf-8")
            text, n = re.subn(rf"^({key}:\s*)[^#\n]*?(\s*#.*)?$",
                              lambda m: f"{m.group(1)}{value}{m.group(2) or ''}", text, count=1, flags=re.M)
            if n == 0:
                m = re.match(r"---\n.*?\n(?=---\n)", text, re.S)
                if not m:
                    sys.exit(f"No frontmatter in {charter}: cannot set {key}")
                text = text[:m.end()] + f"{key}: {value}\n" + text[m.end():]
            tmp = tempfile.NamedTemporaryFile("w", dir=charter.parent, delete=False, encoding="utf-8")
            try:
                tmp.write(text)
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp.close()
                os.replace(tmp.name, charter)
            except Exception:
                if os.path.exists(tmp.name):
                    os.unlink(tmp.name)
                raise
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)


def new(title, project, type_, when=""):
    lock_file = common.WS / "state" / ".task-id.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_file, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            ident = next_id(lock_fd=f)
            folder = (TASKS / project / f"{ident}-{slug(title)}") if project else (TASKS / f"{ident}-{slug(title)}")
            (folder / "evidence").mkdir(parents=True, exist_ok=True)
            (folder / "evidence" / ".gitkeep").touch()
            charter = folder / CHARTER
            template = common.find("templates/task/charter.md", required=True)
            charter.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
            write_field(charter, "id", ident)
            write_field(charter, "title", f'"{title}"')
            write_field(charter, "summary", f'"{title}"')
            write_field(charter, "project", project)
            write_field(charter, "task_type", type_)
            write_field(charter, "created", date.today().isoformat())
            note = common.WS / "projects" / project / "project.md"
            if note.exists():
                write_field(charter, "rel_part_of", f'["{common.link_to(note)}"]')
            if when:
                write_field(charter, "when", when)
            add("task_created", ident, detail={"title": title, "project": project, "type": type_})
            print(folder.relative_to(common.WS))
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def worktree(ident, repo):
    folder = task_dir(ident)
    repo = Path(repo).expanduser().resolve()
    branch = f"task/{folder.name}"
    path = repo.parent / "worktrees" / folder.name
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-b", branch, str(path)], check=True)
    write_field(folder / CHARTER, "workdir", str(path))
    add("worktree", ident, detail={"repo": str(repo), "branch": branch, "path": str(path)})
    print(path)


def status(ident, new_status, reason):
    if new_status not in STATUSES:
        sys.exit(f"Unknown status: {new_status} (expected: {', '.join(STATUSES)})")
    if new_status == "waiting-on-you" and reason not in REASONS:
        sys.exit(f"waiting-on-you needs --reason: {', '.join(REASONS)}")
    charter = task_dir(ident) / CHARTER
    old = read_field(charter, "status")
    write_field(charter, "status", new_status)
    write_field(charter, "waiting_on", f'"{reason}"' if new_status == "waiting-on-you" else '""')
    type_ = {"to-review": "delivery", "done": "validation"}.get(new_status, "status_change")
    if old == "to-review" and new_status == "in-progress":
        type_ = "sent_back"
    add(type_, ident, detail={"from": old, "to": new_status, "reason": reason or ""})
    print(f"{ident}: {old} -> {new_status}")


def list_tasks():
    folders = sorted(set(list(TASKS.glob("T-*")) + list(TASKS.glob("*/T-*"))), key=lambda p: p.name)
    for folder in folders:
        if not folder.is_dir():
            continue
        charter = folder / CHARTER
        if charter.exists():
            print(f"{read_field(charter, 'id'):<8}{read_field(charter, 'status'):<16}"
                  f"{read_field(charter, 'project'):<16}{read_field(charter, 'title')}")


def main():
    p = argparse.ArgumentParser(prog="korrigans task", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="command", required=True)
    n = sp.add_parser("new", help="create a task charter")
    n.add_argument("title")
    n.add_argument("--project", required=True)
    n.add_argument("--type", default="code", help="code, research, writing, proofreading, admin, mail, request")
    n.add_argument("--when", default="", choices=WHEN, help="quota-free for a backlog task")
    w = sp.add_parser("worktree", help="create a git worktree and branch task/<folder> for the task")
    w.add_argument("id")
    w.add_argument("--repo", required=True)
    s = sp.add_parser("status", help="change the status of a task")
    s.add_argument("id")
    s.add_argument("new", metavar="status", help=", ".join(STATUSES))
    s.add_argument("--reason", default="", help="with waiting-on-you: " + ", ".join(REASONS))
    sp.add_parser("list", help="one line per task")
    args = p.parse_args()

    if args.command == "new":
        new(args.title, args.project, args.type, args.when)
    elif args.command == "worktree":
        worktree(args.id, args.repo)
    elif args.command == "status":
        status(args.id, args.new, args.reason)
    elif args.command == "list":
        list_tasks()


if __name__ == "__main__":
    main()
