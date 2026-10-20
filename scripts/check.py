#!/usr/bin/env python3
"""Check the typed notes of the workspace (projects, tasks, ideas, people, questions) and the agents.

Checks: unique ids, required fields, rel_* relations declared in rules/relations.yaml, values that are lists of
"[[...]]" links, link targets that exist and have an allowed type. Targets may be outside the workspace (a
library, your notes): their type is read from their frontmatter. Links are relative to `link_root`
(korrigans.toml).
Agents: complete identity, existing personality and project, one commander per project, and the user's
person note (korrigans.toml `user`).

    korrigans check             errors and warnings; exit code 1 if there is an error
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

WS = common.WS
TYPES = {"project", "task", "idea", "person", "question"}
REQUIRED = {"project": ["title", "summary", "status"], "task": ["title", "status"],
            "idea": ["title", "status"], "person": ["title", "summary"], "question": ["title", "status"]}
IGNORED = {"templates", "agents", "resources", "extensions", "journal", "state", "reports", ".agents", "skills",
           "mail", "node_modules"}
MODES = ("session", "subagent", "call")
LINK = re.compile(r"^\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]$")


def _value(raw):
    raw = re.sub(r"\s+#.*$", "", raw).strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        if '"' in inner:
            return re.findall(r'"([^"]*)"', inner)
        return [v.strip().strip("'") for v in inner.split(",") if v.strip()]
    return raw.strip('"').strip("'")


def frontmatter(path):
    """Frontmatter of a note: key: value, inline [a, b] lists and block "- item" lists. {} if none."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    result, block = {}, None
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")):
            if block and stripped.startswith("- "):
                result[block] = (result[block] or []) + [_value(stripped[2:])]
            continue
        key, sep, raw = line.partition(":")
        if not sep:
            continue
        key = key.strip()
        result[key] = _value(raw)
        block = key if result[key] == "" else None
    return result


def load_relations():
    """rel_* -> {meaning, subject_types, object_types} from rules/relations.yaml (simple YAML, stdlib only)."""
    path = common.find("rules/relations.yaml", required=True)
    relations, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^  rel_\w+:", line):
            current = line.strip()[:-1]
            relations[current] = {}
        elif current and re.match(r"^    \w+:", line):
            key, _, value = line.strip().partition(":")
            value = re.sub(r"\s+#.*$", "", value).strip()
            if value.startswith("["):
                value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
            relations[current][key] = value
    return relations


def notes():
    for path in sorted(WS.rglob("*.md")):
        rel = path.relative_to(WS)
        if any(p in IGNORED or p.startswith((".", "_")) for p in rel.parts):
            continue
        yield path


def name_of(path):
    return os.path.relpath(path, WS)


def check_agents(errors, warnings):
    """IDENTITY.md files (type agent) and the user's note point to files that exist."""
    personalities = common.list_names("personalities", "*.md")
    commanded = {}
    for agent, path in common.list_agents():
        i = common.identity(agent)
        name = f"agents/{agent}/IDENTITY.md"
        for field in ("name", "description", "mode", "display_name"):
            if not i.get(field):
                errors.append(f"{name}: field {field} missing (neither here nor in the type folder's IDENTITY.md)")
        if i.get("mode") not in (None, "", *MODES):
            errors.append(f"{name}: mode {i['mode']} (expected: {', '.join(MODES)})")
        personality = common.target(i.get("personality"))
        if personality and personality not in personalities:
            errors.append(f"{name}: unknown personality {personality} (see `korrigans agent --personalities`)")
        if i.get("project"):
            project = common.target(i["project"])
            if not (WS / "projects" / project / "project.md").exists():
                errors.append(f"{name}: unknown project {project} (no projects/{project}/project.md)")
            elif project in commanded:
                errors.append(f"{name}: {project} already has a commander ({commanded[project]})")
            commanded[project] = agent
        elif agent.startswith("commanders/"):
            errors.append(f"{name}: a commander must name its project (field project)")
    user = common.config().get("user")
    if not user:
        warnings.append("korrigans.toml: no `user` (the user's person note, e.g. people/me.md)")
    elif not (WS / user).exists():
        warnings.append(f"korrigans.toml: user = {user}, but that note does not exist")
    elif frontmatter(WS / user).get("type") != "person":
        warnings.append(f"{user}: the user's note should have type: person")
    for note in sorted((WS / "projects").glob("*/project.md")):
        fm = frontmatter(note)
        if fm.get("intensity") == "focus" and note.parent.name not in commanded:
            warnings.append(f"{name_of(note)}: focus project without a commander (followed by the Seneschal)")


def main():
    relations = load_relations()
    errors, warnings, ids, target_types = [], [], {}, {}

    def type_of(link):
        if link not in target_types:
            path = common.linked_note(link)
            target_types[link] = frontmatter(path).get("type") if path and path.exists() else None
        return target_types[link]

    for path in notes():
        fm = frontmatter(path)
        name = name_of(path)
        t = fm.get("type")
        if t not in TYPES:
            continue
        for field in REQUIRED[t]:
            if not fm.get(field):
                errors.append(f"{name}: required field empty or missing: {field}")
        if fm.get("id"):
            if fm["id"] in ids:
                errors.append(f"{name}: id {fm['id']} already used by {ids[fm['id']]}")
            ids[fm["id"]] = name
        for key, value in fm.items():
            if not key.startswith("rel_"):
                continue
            if key not in relations:
                errors.append(f"{name}: unknown relation {key} (declare it in rules/relations.yaml)")
                continue
            r = relations[key]
            if t not in r.get("subject_types", []):
                errors.append(f"{name}: {key} is not allowed on a note of type {t}")
            if not isinstance(value, list):
                errors.append(f"{name}: {key} must be a list of links")
                continue
            for v in value:
                m = LINK.match(str(v).strip())
                if not m:
                    errors.append(f"{name}: {key} holds something other than a [[...]] link: {v}")
                    continue
                link = f"[[{m.group(1).strip()}]]"
                tt = type_of(link)
                if tt is None:
                    errors.append(f"{name}: {key} points to a missing note: {link}")
                elif tt not in r.get("object_types", []):
                    errors.append(f"{name}: {key} to {link} of type {tt} "
                                  f"(expected: {', '.join(r.get('object_types', []))})")
        if t in ("project", "person") and not fm.get("summary"):
            warnings.append(f"{name}: no one-line summary")

    check_agents(errors, warnings)
    for w in warnings:
        print(f"  ? {w}")
    for e in errors:
        print(f"  ! {e}")
    print(f"  {len(ids)} typed notes, {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
