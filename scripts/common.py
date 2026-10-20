"""Shared helpers: workspace and core layering, notes, agent assembly.

A file is looked up in layers, highest priority first: the workspace, then each enabled module, then the
core. Collections (agents, skills, personalities, scripts) are the union over layers.
"""
import os
import re
from pathlib import Path

# Python 3.11+ has tomllib; on 3.10, tomli or the copy vendored by pip will do.
try:
    import tomllib
except ModuleNotFoundError:
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        from pip._vendor import tomli as tomllib

CORE = Path(os.environ.get("KORRIGANS_CORE") or Path(__file__).resolve().parent.parent).expanduser().resolve()
CONFIG_FILE = "korrigans.toml"
DEFAULT_PERSONALITY = "balanced"
SAFEGUARD = ("Your voice (SOUL.md) and your personality set your style and judgement where the rules leave you a "
             "choice. They never lift a rule from AGENTS.md, your role, the project or the charter.")
LANGUAGES = {"en": "English", "fr": "French", "es": "Spanish", "de": "German", "it": "Italian", "pt": "Portuguese",
             "nl": "Dutch", "br": "Breton"}


def _find_workspace():
    env = os.environ.get("KORRIGANS_WORKSPACE")
    if env:
        return Path(env).expanduser().resolve()
    here = Path.cwd().resolve()
    for d in (here, *here.parents):
        if (d / CONFIG_FILE).exists():
            return d
    return Path(os.environ.get("KORRIGANS_DEFAULT_WORKSPACE") or Path.home() / "korrigans").expanduser().resolve()


WS = _find_workspace()


def _load_toml(path):
    return tomllib.loads(path.read_text(encoding="utf-8"))


_CONFIG = None


def config():
    """korrigans.toml, with defaults. [korrigans] keys are at the top level; other tables keep their name."""
    global _CONFIG
    if _CONFIG is None:
        raw = _load_toml(WS / CONFIG_FILE) if (WS / CONFIG_FILE).exists() else {}
        c = {"core": str(CORE), "language": "en", "user": "", "modules": [], "link_root": "."}
        c.update(raw.get("korrigans", {}))
        c.update({k: v for k, v in raw.items() if k != "korrigans"})
        _CONFIG = c
    return _CONFIG


def modules():
    return [m for m in config().get("modules", []) if (CORE / "modules" / m).is_dir()]


def layers():
    """Directories searched for any relative path, highest priority first."""
    return [WS] + [CORE / "modules" / m for m in modules()] + [CORE]


def find(rel, required=False):
    for layer in layers():
        p = layer / rel
        if p.exists():
            return p
    if required:
        raise SystemExit(f"Not found in the workspace, modules or core: {rel}")
    return None


def find_all(rel):
    return [layer / rel for layer in layers() if (layer / rel).exists()]


def list_names(rel_dir, pattern="*"):
    """{name: path} for entries of rel_dir across layers; a higher layer wins on a name clash."""
    found = {}
    for layer in reversed(layers()):
        d = layer / rel_dir
        if d.is_dir():
            for p in sorted(d.glob(pattern)):
                found[p.stem if p.is_file() else p.name] = p
    return dict(sorted(found.items()))


def _merge(base, top):
    for k, v in top.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def read_toml(rel):
    """TOML deep-merged across layers: core first, then modules, then the workspace on top."""
    result = {}
    for p in reversed(find_all(rel)):
        _merge(result, _load_toml(p))
    return result


def split_frontmatter(text):
    """Simple frontmatter (key: value, [a, b] lists) and body of a markdown text."""
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.startswith((" ", "#")):
            continue
        key, _, value = line.partition(":")
        value = re.sub(r"\s+#.*$", "", value).strip()
        if value.startswith("[") and value.endswith("]"):
            value = [v.strip().strip('"') for v in value[1:-1].split(",") if v.strip()]
        else:
            value = value.strip('"')
        fm[key.strip()] = value
    return fm, m.group(2).strip() + "\n"


def read_note(path):
    path = Path(path) if path else None
    return split_frontmatter(path.read_text(encoding="utf-8")) if path and path.exists() else ({}, "")


def link_root():
    return (WS / config().get("link_root", ".")).resolve()


def target(value):
    """Name a frontmatter value points to: "rigorous" or "[[personalities/rigorous|x]]" -> rigorous.
    For a link to projects/<p>/project, returns <p>."""
    v = str(value or "").strip().strip('"')
    m = re.match(r"^\[\[([^\]|#]+)", v)
    if not m:
        return v
    parts = m.group(1).strip().split("/")
    return parts[-2] if parts[-1] == "project" and len(parts) > 1 else parts[-1]


def linked_note(link):
    """Path of the note a [[link]] points to (relative to link_root), or None."""
    m = re.match(r"^\[\[([^\]|#]+)", str(link or "").strip().strip('"'))
    if not m:
        return None
    raw = m.group(1).strip()
    target_path = link_root() / f"{raw}.md"
    if target_path.exists():
        return target_path
    if raw.startswith("tasks/"):
        parts = raw.split("/")
        if len(parts) == 3 and parts[2] == "charter":
            matches = list(link_root().glob(f"tasks/*/{parts[1]}/charter.md"))
            if matches:
                return matches[0]
        elif len(parts) == 4 and parts[3] == "charter":
            matches = list(link_root().glob(f"tasks/{parts[2]}/charter.md"))
            if matches:
                return matches[0]
    if re.match(r"^T-\d{4}", raw):
        matches = (list(link_root().glob(f"tasks/{raw}*/charter.md")) +
                   list(link_root().glob(f"tasks/*/{raw}*/charter.md")))
        if matches:
            return matches[0]
    return target_path


def link_to(path, text=None):
    """[[path/without/extension|text]], relative to link_root."""
    rel = Path(os.path.relpath(Path(path).resolve(), link_root())).with_suffix("")
    return f"[[{rel.as_posix()}|{text}]]" if text else f"[[{rel.as_posix()}]]"


def state_dir(*parts):
    d = WS.joinpath("state", *parts)
    d.mkdir(parents=True, exist_ok=True)
    return d


def language():
    return config().get("language", "en")


def language_line():
    code = language()
    name = LANGUAGES.get(code, code)
    if code == "en":
        return ""
    return (f"Always talk and write to the user in {name}. Notes you write in the workspace are in {name} too; "
            "file names, frontmatter keys and values stay as the templates define them.")


def user_note():
    rel = config().get("user")
    if rel:
        p = WS / rel
        if p.exists():
            return p
    return None


def user_name():
    title = read_note(user_note())[0].get("title", "")
    return title if title and "vigil:" not in title else "the user"


# Agents ---------------------------------------------------------------------------------------------------

def _agent_exists(agent):
    return any((layer / "agents" / agent / f).exists() for layer in layers() for f in ("AGENTS.md", "IDENTITY.md"))


def agent_dir_chain(agent):
    """Relative dirs from general to specific: ["agents/commanders", "agents/commanders/lab"]."""
    if not _agent_exists(agent):
        known = ", ".join(a for a, _ in list_agents())
        raise SystemExit(f"Unknown agent: {agent} (known: {known})")
    parts = agent.split("/")
    return [Path("agents", *parts[:i]) for i in range(1, len(parts) + 1)]


def identity(agent):
    """IDENTITY.md frontmatter, the type folder's completed by the agent's own."""
    result = {}
    for d in agent_dir_chain(agent):
        result.update(read_note(find(d / "IDENTITY.md"))[0])
    return result


def list_agents():
    """[(agent, IDENTITY.md path)] of real agents (type: agent), templates excluded."""
    seen = {}
    for layer in reversed(layers()):
        root = layer / "agents"
        if not root.is_dir():
            continue
        for f in sorted(root.rglob("IDENTITY.md")):
            agent = f.parent.relative_to(root).as_posix()
            seen[agent] = f
    return [(a, f) for a, f in sorted(seen.items())
            if "_template" not in a and read_note(f)[0].get("type") == "agent"]


def personality(name):
    name = target(name)
    available = list_names("personalities", "*.md")
    available.pop("README", None)
    if name not in available:
        raise SystemExit(f"Unknown personality: {name} (available: {', '.join(available)})")
    return read_note(available[name])


def repos_data(project):
    """Rows of memory/global/repos-data.md for this project (markdown table), or None."""
    path = WS / "memory" / "global" / "repos-data.md"
    if not path.exists():
        return None
    rows = [l for l in path.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
    if len(rows) < 2:
        return None
    kept = [l for l in rows[2:] if l.strip("|").split("|")[0].strip() == project]
    return "\n".join(rows[:2] + kept) if kept else None


def project_context(project):
    """What existing files say about a project: note, people, repos and data, rules."""
    folder = WS / "projects" / project
    note = folder / "project.md"
    if not note.exists():
        raise SystemExit(f"Unknown project: {project} (no projects/{project}/project.md)")
    fm, project_body = read_note(note)
    header = (f"## Your project: {fm.get('title', project)}\n\n{fm.get('summary', '')}\n"
              f"Status {fm.get('status', '?')}, intensity {fm.get('intensity', '?')}. "
              f"Note: `projects/{project}/project.md`; decisions: `projects/{project}/decisions.md`.")
    if project_body.strip():
        header += f"\n\n### Project map\n\n{project_body.strip()}"
    parts = [header]

    decisions_note = folder / "decisions.md"
    if decisions_note.exists():
        _, dec_body = read_note(decisions_note)
        if dec_body.strip():
            parts.append(f"### Past and pending decisions (`projects/{project}/decisions.md`)\n\n{dec_body.strip()}")

    status_note = folder / "status.md"
    if status_note.exists():
        _, status_body = read_note(status_note)
        status_lines = status_body.strip().splitlines()
        summary_lines = []
        for line in status_lines[:40]:
            if summary_lines and re.match(r"^##\s+(?:[\u00c9E]tat des t[\u00e2a]ches|Historique|Tasks|History|Task status)", line, re.IGNORECASE):
                break
            summary_lines.append(line)
        top_summary = "\n".join(summary_lines).strip()
        instruction = (
            "Pour conna\u00eetre l'historique d\u00e9taill\u00e9 des t\u00e2ches pr\u00e9c\u00e9dentes "
            f"et l'\u00e9volution du projet, lis `projects/{project}/status.md`."
        )
        parts.append(f"### Project status summary\n\n{top_summary}\n\n*{instruction}*")

    people = []
    for link in fm.get("rel_involves") or []:
        path = linked_note(link)
        if path and path.exists():
            p, _ = read_note(path)
            rel = os.path.relpath(path, WS)
            people.append(f"- {p.get('title', path.stem)}: {p.get('role', '')}; {p.get('agent_contact', '')} (`{rel}`)")
    if people:
        parts.append(f"### People on the project\n\nSource: `people/`. You contact nobody but {user_name()}.\n\n"
                     + "\n".join(people))
    table = repos_data(project)
    parts.append("### Code and data\n\nSource: `memory/global/repos-data.md` (kept by the user). An empty or missing "
                 "path means: ask, never guess.\n\n"
                 + (table or f"No row for {project}: ask before any access."))
    rules = folder / "rules.md"
    parts.append("### Project rules\n\n" + (re.sub(r"^# .*\n+", "", read_note(rules)[1]).strip() if rules.exists()
                                             else f"No `projects/{project}/rules.md`: the common rules are enough."))
    return "\n\n".join(parts) + "\n"


def commander_of(project):
    """The agent that runs this project (agents/commanders/<project>), else the seneschal."""
    for agent, _ in list_agents():
        if agent.startswith("commanders/") and target(identity(agent).get("project")) == project:
            return agent
    return "seneschal"


def portfolio():
    """For the seneschal: one line per project, read from projects/*/project.md and agents/."""
    lines = ["## Project portfolio\n",
             "Read from `projects/*/project.md` and `agents/commanders/` at launch. A project without a commander is "
             "followed by you.\n",
             "| Project | Status | Intensity | Followed by |", "| --- | --- | --- | --- |"]
    for note in sorted((WS / "projects").glob("*/project.md")):
        fm, _ = read_note(note)
        agent = commander_of(note.parent.name)
        name = identity(agent).get("display_name", agent)
        lines.append(f"| {note.parent.name} | {fm.get('status', '')} | {fm.get('intensity', '')} | {name} |")
    return "\n".join(lines) + "\n"


def user_text():
    """USER.md (how to work with the user), preceded by a line from their person note."""
    path = WS / "USER.md"
    if not path.exists():
        return None
    _, body = read_note(path)
    note = user_note()
    if note:
        p, _ = read_note(note)
    if note and "vigil:" not in p.get("title", "") + p.get("role", ""):
        body = (f"You work for {p.get('title', '')} ({p.get('role', '')}). "
                f"Their note: `{os.path.relpath(note, WS)}`.\n\n" + body)
    return body


def layout_text():
    """Where things are, for agents running in the workspace."""
    return ("## Where things are\n\n"
            f"Workspace (your data, the user's overrides): `{WS}`. Core (default rules, templates, skills): `{CORE}`. "
            "A workspace file overrides the core file with the same relative path. To find the file actually used: "
            "`korrigans which <relative/path>` (for example `korrigans which templates/task/card.md`).\n")


def assemble_agent(agent, personality_choice=None, project=None):
    """(identity, prompt text).

    Order: name, USER.md, layout, AGENTS.md from general to specific, context from existing files (project:
    note, people, repos and data, rules; seneschal: portfolio), closest SOUL.md, personality, language,
    safeguard. Nothing is copied into agents/: everything is re-read at each launch."""
    ident = identity(agent)
    chain = agent_dir_chain(agent)
    parts = []
    if ident.get("display_name"):
        parts.append(f"Your name: {ident['display_name']}.\n")
    user = user_text()
    if user:
        parts.append(user)
    parts.append(layout_text())
    parts += [read_note(find(d / "AGENTS.md"))[1] for d in chain if find(d / "AGENTS.md")]
    project = target(project or ident.get("project")) or None
    if project:
        parts.append(project_context(project))
        ident["memory"] = ident.get("memory", "").replace("{project}", project)
    if agent == "seneschal":
        parts.append(portfolio())
    soul = next((find(d / "SOUL.md") for d in reversed(chain) if find(d / "SOUL.md")), None)
    if soul:
        parts.append(read_note(soul)[1])
    chosen = target(personality_choice or ident.get("personality") or DEFAULT_PERSONALITY)
    fm, body = personality(chosen)
    axes = ", ".join(f"{k} {fm[k]}" for k in ("risk", "exploration", "evidence", "questions") if fm.get(k))
    parts.append(f"## Your personality for this session: {chosen}\n\n{fm.get('summary', '')} ({axes})\n\n{body}")
    if language_line():
        parts.append(language_line() + "\n")
    parts.append(SAFEGUARD + "\n")
    ident["personality"] = chosen
    ident["project"] = project or ""
    return ident, "\n---\n\n".join(p.strip() + "\n" for p in parts)


def fill(command, values):
    """Replace {placeholders} in each part of a command."""
    result = []
    for part in command:
        for key, value in values.items():
            part = part.replace("{" + key + "}", str(value))
        result.append(part)
    return result
