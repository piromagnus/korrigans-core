#!/usr/bin/env python3
"""Todoist for the household (API v1; token in TODOIST_API_TOKEN, never written anywhere).

    korrigans todoist today                      tasks due today or overdue -> state/todoist-YYYY-MM-DD.json
    korrigans todoist read ["Project"]           a whole project (sections, tasks, labels), read only
                                                 -> state/todoist-<project>.json ; default: the first read-only project
    korrigans todoist apply <assignment.md> [--from "Project"]
                                                 show what would be done (nothing is sent)
    korrigans todoist apply <assignment.md> --execute
                                                 create the household's project (korrigans.toml [todoist] project) if
                                                 missing, its sections and labels, then copy each kept task with the
                                                 label of its owner and a link to the original

Settings in korrigans.toml:
    [todoist]
    project = "Korrigans"      the project the household writes to
    read_only = []             your own projects: read, never changed, moved or deleted

assignment.md holds a table | id | section | task | owner | reason |, written with the skill todoist-sync and
approved by the user. The script never deletes anything and never writes to a read-only project.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(os.environ.get("KORRIGANS_CORE") or Path(__file__).resolve().parents[3]) / "scripts"))
import common  # noqa: E402

API = "https://api.todoist.com/api/v1"
STATUSES = ["in-progress", "to-review", "waiting-on-you"]


def settings():
    s = common.config().get("todoist", {})
    return s.get("project", "Korrigans"), list(s.get("read_only", []))


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "project"


def call(method, path, data=None, params=None):
    token = os.environ.get("TODOIST_API_TOKEN")
    if not token:
        sys.exit("TODOIST_API_TOKEN missing (set it in the workspace's .env): nothing done.")
    url = f"{API}/{path}" + (f"?{urllib.parse.urlencode(params)}" if params else "")
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=payload, method=method, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f"Todoist answered {e.code} on {method} {path}: nothing more done.")
    except (urllib.error.URLError, OSError) as e:
        sys.exit(f"Todoist unreachable ({getattr(e, 'reason', e)}): nothing done.")
    return json.loads(text) if text else {}


def all_of(path, **params):
    results, cursor = [], None
    for _ in range(50):
        p = dict(params, **({"cursor": cursor} if cursor else {}))
        d = call("GET", path, params=p or None)
        results.extend(d.get("results", []))
        cursor = d.get("next_cursor")
        if not cursor:
            break
    return results


def today():
    day = date.today().isoformat()
    tasks = [t for t in all_of("tasks") if not t.get("checked")
             and (t.get("due") or {}).get("date", "9999")[:10] <= day]
    projects = {p["id"]: p["name"] for p in all_of("projects")}
    out = [{"id": t["id"], "title": t.get("content"), "project": projects.get(t.get("project_id"), ""),
            "due": t["due"]["date"], "priority": t.get("priority"), "labels": t.get("labels", []),
            "link": f"https://app.todoist.com/app/task/{t['id']}"} for t in tasks]
    out.sort(key=lambda t: (t["due"], -(t["priority"] or 1)))
    path = common.state_dir() / f"todoist-{day}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out)} task(s) due or overdue: {path}")


def read(name):
    project = next((p for p in all_of("projects") if p["name"] == name), None)
    if not project:
        sys.exit(f"Project not found: {name}")
    out = {"project": project, "sections": all_of("sections", project_id=project["id"]),
           "tasks": all_of("tasks", project_id=project["id"]), "labels": all_of("labels")}
    path = common.state_dir() / f"todoist-{slug(name)}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out['sections'])} section(s), {len(out['tasks'])} task(s): {path}")


def read_assignment(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.fullmatch(r"\w+", cells[0]) and cells[0] != "id":
            rows.append({"id": cells[0], "section": cells[1], "task": cells[2], "owner": cells[3]})
    return rows


def apply(path, source_name, execute):
    target_name, read_only = settings()
    if target_name in read_only:
        sys.exit(f"{target_name} is both the household's project and read-only in korrigans.toml: nothing done.")
    source_file = common.WS / "state" / f"todoist-{slug(source_name)}.json"
    if not source_file.exists():
        sys.exit(f"Run `korrigans todoist read \"{source_name}\"` first (no {source_file.relative_to(common.WS)}).")
    assignment = read_assignment(path)
    source = json.loads(source_file.read_text(encoding="utf-8"))
    by_id = {t["id"]: t for t in source["tasks"]}
    sections = list(dict.fromkeys(s["name"] for s in source["sections"]))
    labels = sorted({a["owner"] for a in assignment} | set(STATUSES))
    print(f"Project '{target_name}'; sections: {', '.join(sections) or 'none'}")
    print(f"Labels: {', '.join(labels)}")
    print(f"{len(assignment)} task(s) to copy (the original stays in '{source_name}')")
    for a in assignment:
        print(f"  {a['section']:<14} {a['owner']:<18} {a['task'][:60]}")
    if not execute:
        print("Preview only: run again with --execute once the user has agreed.")
        return
    project = next((p for p in all_of("projects") if p["name"] == target_name), None)
    if project is None:
        project = call("POST", "projects", {"name": target_name})
    existing_sections = {s["name"]: s["id"] for s in all_of("sections", project_id=project["id"])}
    section_ids = {name: existing_sections.get(name) or call("POST", "sections", {"name": name,
                                                                                  "project_id": project["id"]})["id"]
                   for name in sections}
    existing_labels = {l["name"] for l in source.get("labels", [])}
    for name in labels:
        if name not in existing_labels:
            call("POST", "labels", {"name": name})
    for a in assignment:
        t = by_id.get(a["id"])
        if not t:
            print(f"  ! task {a['id']} missing from the read, skipped")
            continue
        description = (t.get("description", "") + "\n\n" if t.get("description") else "")
        description += f"Copy of https://app.todoist.com/app/task/{t['id']} ('{source_name}')."
        new = {"content": t["content"], "description": description, "project_id": project["id"],
               "labels": sorted(set(t.get("labels", [])) | {a["owner"]}), "priority": t.get("priority", 1)}
        if section_ids.get(a["section"]):
            new["section_id"] = section_ids[a["section"]]
        if t.get("due"):
            new["due_date"] = t["due"]["date"][:10]
        call("POST", "tasks", new)
    print("Done. Nothing was deleted.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="command", required=True)
    sp.add_parser("today")
    r = sp.add_parser("read")
    r.add_argument("project", nargs="?")
    a = sp.add_parser("apply")
    a.add_argument("assignment")
    a.add_argument("--from", dest="source", help="the project the tasks were read from (default: first read-only)")
    a.add_argument("--execute", action="store_true")
    args = p.parse_args()
    read_only = settings()[1]
    if args.command == "today":
        return today()
    name = (args.project if args.command == "read" else args.source) or (read_only[0] if read_only else None)
    if not name:
        sys.exit("Name the project to read (or set [todoist] read_only in korrigans.toml).")
    if args.command == "read":
        read(name)
    else:
        apply(args.assignment, name, args.execute)


if __name__ == "__main__":
    main()
