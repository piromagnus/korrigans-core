#!/usr/bin/env python3
"""Unified core engine API for Korrigans CLI and UI (server.py).

    korrigans engine scan [--workspace <ws>] [--core <core>] [--json]
    korrigans engine tasks [--workspace <ws>] [--json]
    korrigans engine status [--json]
    korrigans engine module <todoist|mail|quota> [action] [--json]
    korrigans engine run-task <task_id> [--harness ...] [--rank ...] [--dry-run] [--background]
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

ENGINE_BIN = common.CORE / "bin" / "korrigans-engine"
ENGINE_SRC = common.CORE / "engine" / "src" / "main.rs"
CARGO_TOML = common.CORE / "engine" / "Cargo.toml"


def ensure_engine_binary():
    """Ensure the native Rust engine binary is compiled and up-to-date."""
    if not ENGINE_SRC.is_file():
        return False

    needs_build = False
    if not ENGINE_BIN.is_file():
        needs_build = True
    else:
        try:
            if ENGINE_SRC.stat().st_mtime > ENGINE_BIN.stat().st_mtime:
                needs_build = True
        except OSError:
            needs_build = True

    if not needs_build:
        return True

    # Attempt compilation
    ENGINE_BIN.parent.mkdir(parents=True, exist_ok=True)
    home_cargo = Path.home() / ".cargo" / "bin"
    rustc = home_cargo / "rustc" if (home_cargo / "rustc").is_file() else shutil.which("rustc")
    cargo = home_cargo / "cargo" if (home_cargo / "cargo").is_file() else shutil.which("cargo")

    if rustc:
        cmd = [str(rustc), "-C", "opt-level=3", "--edition", "2021", str(ENGINE_SRC), "-o", str(ENGINE_BIN)]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            try:
                ENGINE_BIN.chmod(0o755)
            except OSError:
                pass
            return True

    if cargo and CARGO_TOML.is_file():
        cmd = [str(cargo), "build", "--release", "--manifest-path", str(CARGO_TOML)]
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        target_bin = common.CORE / "engine" / "target" / "release" / "korrigans-engine"
        if r.returncode == 0 and target_bin.is_file():
            shutil.copy2(target_bin, ENGINE_BIN)
            try:
                ENGINE_BIN.chmod(0o755)
            except OSError:
                pass
            return True

    return False


def python_fallback_tasks(workspace: Path) -> list:
    """Python fallback for task discovery if native engine is unavailable."""
    tasks_dir = workspace / "tasks"
    if not tasks_dir.is_dir():
        return []

    charters = list(tasks_dir.glob("T-*/charter.md")) + list(tasks_dir.glob("*/T-*/charter.md"))
    charters.sort()
    out = []
    for charter in charters:
        folder = charter.parent
        meta, _ = common.read_note(charter)
        card = folder / "card.md"
        evidence = folder / "evidence"
        card_present = card.is_file() and card.stat().st_size > 0
        evidence_count = len([e for e in evidence.iterdir() if e.is_file()]) if evidence.is_dir() else 0

        status = meta.get("status", "todo")
        blocking = bool(meta.get("blocking"))
        if status == "todo":
            score = 90 if not blocking else 50
            reasons = ["Contract pending implementation"]
        elif status == "done":
            score = 95 if card_present else 75
            reasons = ["Task completed with confirmed deliverables"]
        elif status == "to-review":
            score = 90 if card_present else 55
            reasons = ["Complete delivery submitted for review"]
        elif status == "in-progress":
            score = 70 if card_present else 45
            reasons = ["In progress"]
        else:
            score = 40
            reasons = ["Pending arbitration"]
        level = "high" if score >= 80 else "medium" if score >= 50 else "low"

        folder_rel = folder.relative_to(workspace).as_posix()
        charter_rel = charter.relative_to(workspace).as_posix()
        tid = meta.get("id") or folder.name[:6]
        out.append({
            "id": tid,
            "path": charter_rel,
            "folder": folder_rel,
            "title": meta.get("title", ""),
            "type": meta.get("type", "code"),
            "status": status,
            "project": meta.get("project", ""),
            "priority": meta.get("priority", ""),
            "difficulty": meta.get("difficulty", ""),
            "blocking": str(meta.get("blocking", "")),
            "waiting_on": meta.get("waiting_on", ""),
            "card_present": card_present,
            "evidence_count": evidence_count,
            "confidence_score": score,
            "confidence_level": level,
            "confidence_reasons": reasons,
            "frontmatter": meta,
        })
    return out


def cmd_tasks(args):
    ws = Path(args.workspace or common.WS).resolve()
    ensure_engine_binary()
    if ENGINE_BIN.is_file():
        r = subprocess.run([str(ENGINE_BIN), "tasks", "--workspace", str(ws)], capture_output=True, text=True)
        if r.returncode == 0:
            print(r.stdout.strip())
            return 0

    data = python_fallback_tasks(ws)
    print(json.dumps(data, ensure_ascii=False, indent=2 if not args.json else None))
    return 0


def python_fallback_scan(workspace: Path, core: Path = None) -> dict:
    """Python fallback for full file scanning."""
    files = []
    roots = [(workspace, "")]
    if core and core != workspace and core.is_dir():
        roots.append((core, "core"))

    for root, prefix in roots:
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            parts = p.relative_to(root).parts
            if any(part.startswith(".") or part in ("node_modules", "target", "__pycache__", "dist", "build") for part in parts):
                continue
            try:
                st = p.stat()
                sha = hashlib.sha256(p.read_bytes()).hexdigest()
                rel = p.relative_to(root).as_posix()
                disp_path = f"{prefix}/{rel}" if prefix else rel
                fm = None
                conf = None
                if p.suffix == ".md":
                    fm, _ = common.read_note(p)
                    if p.name == "charter.md":
                        status = fm.get("status", "todo")
                        card = p.parent / "card.md"
                        has_card = card.is_file() and card.stat().st_size > 0
                        score = 90 if status == "todo" else (95 if has_card else 75)
                        level = "high" if score >= 80 else "medium"
                        conf = {"score": score, "level": level, "reasons": ["Task contract"]}
                files.append({
                    "path": disp_path,
                    "size": st.st_size,
                    "mtime_ns": st.st_mtime_ns,
                    "sha256": sha,
                    "frontmatter": fm,
                    "confidence": conf,
                })
            except Exception:
                continue

    return {
        "workspace": str(workspace),
        "core": str(core) if core else None,
        "count": len(files),
        "files": files,
    }


def cmd_scan(args):
    ws = Path(args.workspace or common.WS).resolve()
    core = Path(args.core or common.CORE).resolve() if args.core else common.CORE
    ensure_engine_binary()
    if ENGINE_BIN.is_file():
        cmd = [str(ENGINE_BIN), "scan", "--workspace", str(ws)]
        if core:
            cmd.extend(["--core", str(core)])
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            print(r.stdout.strip())
            return 0

    data = python_fallback_scan(ws, core)
    print(json.dumps(data, ensure_ascii=False, indent=2 if not args.json else None))
    return 0


def cmd_status(args):
    """Unified status: vigil, quotas, ladder, executions, modules."""
    res = {}

    # Vigil from context.py
    try:
        import context
        res["vigil"] = context.report()
    except Exception as e:
        res["vigil"] = {"error": str(e)}

    # Quotas from usage.py
    try:
        from modules.quota.scripts import usage
        res["quotas"] = usage.state()
    except Exception:
        usage_script = common.find("modules/quota/scripts/usage.py")
        if usage_script:
            try:
                out = subprocess.check_output([sys.executable, str(usage_script), "state", "--json"], text=True)
                res["quotas"] = json.loads(out)
            except Exception as e:
                res["quotas"] = {"error": str(e)}
        else:
            res["quotas"] = []

    # Ladder from ladder.py
    try:
        import ladder
        r = ladder.rules()
        ladder_list = []
        for rank_name in r.get("ladder", []):
            spec = r.get("ranks", {}).get(rank_name, rank_name)
            model, _, effort = spec.partition(":")
            ladder_list.append({
                "rank": rank_name,
                "model": model,
                "effort": effort or "medium",
                "label": ladder.label(rank_name, r),
            })
        res["ladder"] = ladder_list
    except Exception as e:
        res["ladder"] = {"error": str(e)}

    # Executions from track.py
    try:
        import track
        res["executions"] = track.states()
    except Exception as e:
        res["executions"] = {"error": str(e)}

    # Modules status
    enabled_modules = common.modules()
    modules_info = {}
    for m in ("quota", "todoist", "mail", "research"):
        is_enabled = m in enabled_modules
        m_info = {"enabled": is_enabled}
        if is_enabled:
            mod_path = common.find(f"modules/{m}")
            m_info["path"] = str(mod_path) if mod_path else None
        modules_info[m] = m_info
    res["modules"] = modules_info
    res["timestamp"] = datetime.now(timezone.utc).isoformat()

    print(json.dumps(res, ensure_ascii=False, indent=2 if not args.json else None))
    return 0


def cmd_module(args):
    """Inspect or trigger module actions."""
    mod = args.name
    action = args.action or "state"

    if mod == "quota":
        usage_script = common.find("modules/quota/scripts/usage.py")
        if not usage_script:
            sys.exit("Module quota not found.")
        cmd = [sys.executable, str(usage_script), action]
        if args.json and action in ("state", "alert"):
            cmd.append("--json")
        sys.exit(subprocess.run(cmd).returncode)

    elif mod == "todoist":
        todoist_script = common.find("modules/todoist/scripts/todoist.py")
        if not todoist_script:
            sys.exit("Module todoist not found.")
        cmd = [sys.executable, str(todoist_script), action]
        sys.exit(subprocess.run(cmd).returncode)

    elif mod == "mail":
        mail_script = common.find("modules/mail/scripts/mail.py")
        if not mail_script:
            sys.exit("Module mail not found.")
        cmd = [sys.executable, str(mail_script), action]
        sys.exit(subprocess.run(cmd).returncode)

    else:
        sys.exit(f"Unknown module '{mod}'. Supported: quota, todoist, mail.")


def cmd_run_task(args):
    """Invoke run.py cleanly with options."""
    run_script = common.find("scripts/run.py")
    if not run_script:
        sys.exit("run.py script not found.")

    cmd = [sys.executable, str(run_script), args.task_id]
    if args.harness:
        cmd.extend(["--harness", args.harness])
    if args.rank:
        cmd.extend(["--rank", args.rank])
    if args.dry_run:
        cmd.append("--dry-run")

    if args.background:
        proc = subprocess.Popen(cmd, cwd=common.WS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        res = {"ok": True, "task_id": args.task_id, "pid": proc.pid, "background": True}
        print(json.dumps(res, ensure_ascii=False))
        return 0
    else:
        r = subprocess.run(cmd, cwd=common.WS)
        return r.returncode


def main():
    p = argparse.ArgumentParser(prog="korrigans engine", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    # scan
    p_scan = sub.add_parser("scan", help="fast recursive directory walk with SHA-256 and metadata")
    p_scan.add_argument("--workspace", "-w", help="path to workspace")
    p_scan.add_argument("--core", "-c", help="path to core")
    p_scan.add_argument("--json", action="store_true", help="compact JSON output")

    # tasks
    p_tasks = sub.add_parser("tasks", help="fast discovery of tasks with confidence scores")
    p_tasks.add_argument("--workspace", "-w", help="path to workspace")
    p_tasks.add_argument("--json", action="store_true", help="compact JSON output")

    # status
    p_status = sub.add_parser("status", help="unified status of vigil, quotas, ladder, executions, modules")
    p_status.add_argument("--json", action="store_true", help="compact JSON output")

    # module
    p_mod = sub.add_parser("module", help="inspect or trigger modules (quota, todoist, mail)")
    p_mod.add_argument("name", choices=["quota", "todoist", "mail"], help="module name")
    p_mod.add_argument("action", nargs="?", default="", help="subcommand or action")
    p_mod.add_argument("--json", action="store_true", help="json output if supported")

    # run-task
    p_run = sub.add_parser("run-task", help="run a task using run.py")
    p_run.add_argument("task_id", help="task id (e.g. T-0021)")
    p_run.add_argument("--harness", help="harness to force (e.g. pi-durable, pi, codex, claude)")
    p_run.add_argument("--rank", help="rank to force")
    p_run.add_argument("--dry-run", action="store_true", help="dry-run without running")
    p_run.add_argument("--background", action="store_true", help="run asynchronously in background")

    args = p.parse_args()
    if args.command == "tasks":
        sys.exit(cmd_tasks(args))
    elif args.command == "scan":
        sys.exit(cmd_scan(args))
    elif args.command == "status":
        sys.exit(cmd_status(args))
    elif args.command == "module":
        sys.exit(cmd_module(args))
    elif args.command == "run-task":
        sys.exit(cmd_run_task(args))


if __name__ == "__main__":
    main()
