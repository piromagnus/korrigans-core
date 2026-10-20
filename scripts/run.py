#!/usr/bin/env python3
"""Run the korrigan of a task, climbing the ladder of ranks when an attempt fails.

    korrigans run T-0002                        the ladder, starting rank from the difficulty (rules/escalation.toml)
    korrigans run T-0002 --harness pi           force a harness
    korrigans run T-0002 --rank knight          force a single rank (a name, or "model:effort"), no climbing
    korrigans run T-0002 --role virgil          another agent (default: from the task type)
    korrigans run T-0002 --personality cautious for this run (else the charter's personality field)
    korrigans run T-0002 --no-watch
    korrigans run T-0002 --dry-run              show the ladder and the commands without running anything

The prompt is the assembled agent (the user, the korrigans' rules, the task's project, the personality)
followed by the charter, which works with any harness.

One ladder (model and reasoning effort); the difficulty gives the starting rank. For each rank, the
harnesses of rules/routing.toml that have its model are tried. Quota exhausted: next harness, same rank.
Failure, the charter's `verify` command failing, time limit passed or the Watch saying "escalate": next
rank, with a summary of the attempts in tasks/<id>/attempts.md. Climbing past the start of a higher
difficulty reclassifies the task (field difficulty, event difficulty_revised). The Watch saying "stop", or
max_attempts reached: the task becomes waiting-on-you (review).
"""
import argparse
import json
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import atexit
import os
import signal
import time
from datetime import timedelta
import common  # noqa: E402

_ACTIVE_CHILD_PIDS = set()


def _kill_active_children():
    for pid in list(_ACTIVE_CHILD_PIDS):
        try:
            os.killpg(pid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            pass
    _ACTIVE_CHILD_PIDS.clear()


def _signal_handler(signum, frame):
    _kill_active_children()
    sys.exit(128 + signum)


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)
atexit.register(_kill_active_children)

from journal import add  # noqa: E402
from ladder import Watch, classify, harness_command, label, ladder, rank, rules  # noqa: E402
from task import read_field, task_dir, write_field  # noqa: E402
from track import write_state  # noqa: E402

ROLE_BY_TYPE = {"code": "korrigans/code", "research": "korrigans/research", "mail": "chamberlain"}
DEFAULT_ROLE = "korrigans/code"


def agent_exists(agent):
    return any(common.find(f"agents/{agent}/{f}") for f in ("AGENTS.md", "IDENTITY.md"))


def read_access(charter):
    """[(path, mode)] from the charter's access field; mode is read or write."""
    raw = read_field(charter, "access").strip("[]")
    result = []
    for part in raw.split(","):
        part = part.strip().strip('"').strip("'")
        if part:
            path, _, mode = part.rpartition(":")
            result.append((str(Path(path or part).expanduser()), mode if path else "read"))
    return result


def build_prompt(agent_text, folder, access):
    lines = "\n".join(f"- {path}: {mode}" for path, mode in access) or "- none"
    charter = (folder / "charter.md").read_text(encoding="utf-8")
    card = common.find("templates/task/card.md")
    attempts = folder / "attempts.md"
    previous = ""
    if attempts.exists():
        previous = ("\n---\n\n## Previous attempts\n\nAn attempt with a lighter model did not succeed. "
                    "Start from its work (commits, evidence, partial card) without redoing it, and avoid what failed.\n\n"
                    + attempts.read_text(encoding="utf-8"))
    return (
        f"{agent_text}\n---\n\n"
        f"Workspace: {common.WS}\n"
        f"Task folder (charter, card, evidence): {folder}\n"
        f"Write card.md and evidence/ in this folder, not in the code repository. Keep progress.md there up to date, "
        f"and reread advice.md between steps when it appears.\n"
        + (f"Card template: {card}\n" if card else "")
        + f"Access besides the working folder (read: never modify):\n{lines}\n\n"
        f"{charter}{previous}"
    )


def note_attempt(folder, rk, name, result, reason, trace):
    end = trace.read_text(encoding="utf-8", errors="replace").splitlines()[-15:] if trace and trace.exists() else []
    with (folder / "attempts.md").open("a", encoding="utf-8") as f:
        f.write(f"\n### {datetime.now():%Y-%m-%d %H:%M}: {rk['label']} on {name}: {result}\n\n{reason}\n")
        if end:
            f.write("\nEnd of the trace:\n\n```text\n" + "\n".join(end) + "\n```\n")


def launch(name, harness, command, folder, workdir, rk, max_seconds, watch_rank, context):
    """One attempt. Returns (result, reason, trace); result: ok, quota, failed, missing, escalate, stop."""
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    trace = folder / f"trace-{name}-{rk['name'].replace(':', '-')}-{stamp}.log"
    ident = folder.name[:6]
    add("run_start", ident, tool=name, detail={"rank": rk["name"], "trace": trace.name, "workdir": str(workdir)})
    output = []
    with trace.open("w", encoding="utf-8") as f:
        try:
            proc = subprocess.Popen(command, cwd=workdir, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True,
                                    start_new_session=True)
            _ACTIVE_CHILD_PIDS.add(proc.pid)
        except FileNotFoundError:
            add("run_failed", ident, tool=name, detail={"reason": "harness not found"})
            print(f"{name}: command not found ({command[0]})")
            return "missing", "harness not found", None
        timed_out = threading.Event()

        def cut():
            timed_out.set()
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except (ProcessLookupError, OSError):
                proc.terminate()

        timer = threading.Timer(max_seconds, cut) if max_seconds else None
        if timer:
            timer.start()
        watch = Watch(proc, trace, folder, context, watch_rank, workdir) if watch_rank else None
        if watch:
            watch.start()
        for line in proc.stdout:
            f.write(line)
            f.flush()
            output.append(line)
            print(line, end="")
        code = proc.wait()
        _ACTIVE_CHILD_PIDS.discard(proc.pid)
        if timer:
            timer.cancel()
        if watch:
            watch.halt.set()
    text = "".join(output[-200:]).lower()
    if watch and watch.verdict:
        v = watch.verdict
        add("watch_stop", ident, tool=name, detail=v | {"rank": rk["name"]})
        return v["verdict"], f"The Watch: {v.get('reason', '')} {v.get('advice', '')}".strip(), trace
    if timed_out.is_set():
        add("run_failed", ident, tool=name, detail={"reason": "time", "rank": rk["name"]})
        return "failed", f"Time limit passed ({max_seconds // 60} min).", trace
    if any(pattern.lower() in text for pattern in harness.get("quota_patterns", [])):
        add("quota_exhausted", ident, tool=name, detail={"code": code})
        return "quota", "quota exhausted", trace
    if code != 0:
        add("run_failed", ident, tool=name, detail={"code": code, "rank": rk["name"]})
        return "failed", f"The harness stopped with an error (code {code}).", trace
    add("run_end", ident, tool=name, detail={"trace": trace.name, "rank": rk["name"]})
    return "ok", "", trace


def verify(charter, workdir):
    """The charter's `verify` command (e.g. pytest -q): (passed, end of output). No command: passed."""
    command = read_field(charter, "verify")
    if not command:
        return True, ""
    r = subprocess.run(command, shell=True, cwd=workdir, capture_output=True, text=True)
    end = "\n".join((r.stdout + r.stderr).splitlines()[-20:])
    return r.returncode == 0, f"`{command}` failed (code {r.returncode}):\n\n```text\n{end}\n```"


def get_next_reset(harness_names):
    """Estimate next quota reset time for given harnesses."""
    try:
        import importlib.util
        script_path = common.find("modules/quota/scripts/usage.py")
        if not script_path:
            alt = common.CORE / "modules" / "quota" / "scripts" / "usage.py"
            if alt.exists():
                script_path = alt
        if script_path:
            spec = importlib.util.spec_from_file_location("usage", script_path)
            usage_mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(usage_mod)
            rows = usage_mod.state()
            resets = []
            for r in rows:
                sub_harnesses = r.get("harness", [])
                if isinstance(sub_harnesses, str):
                    sub_harnesses = [sub_harnesses]
                if any(h in sub_harnesses for h in harness_names):
                    resets.append(datetime.fromisoformat(r["reset"]))
            if resets:
                return min(resets)
    except Exception:
        pass
    return datetime.now().astimezone() + timedelta(hours=1)


def resume_waiting_tasks():
    """Scan state/execution/*.json for tasks waiting for quota and resume them."""
    state_dir = common.WS / "state" / "execution"
    if not state_dir.exists():
        print("No execution state found.")
        return
    resumed = 0
    now = datetime.now().astimezone()
    for sf in sorted(state_dir.glob("T-*.json")):
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("state") == "waiting for quota":
            ident = data.get("id")
            next_retry = data.get("next_retry_at")
            ready = True
            if next_retry:
                try:
                    dt = datetime.fromisoformat(next_retry)
                    if dt.tzinfo is None:
                        dt = dt.astimezone()
                    if now < dt:
                        ready = False
                except Exception:
                    pass
            if ready:
                print(f"Resuming {ident} (was waiting for quota)...")
                resumed += 1
                cmd = [sys.executable, str(Path(__file__).resolve()), ident]
                subprocess.Popen(cmd, cwd=common.WS, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    if not resumed:
        print("No task waiting for quota is ready to resume.")


def hand_back(charter, ident, cause, state):
    """The task waits on the user for a review."""
    write_field(charter, "status", "waiting-on-you")
    write_field(charter, "waiting_on", '"review"')
    add("status_change", ident, detail={"to": "waiting-on-you", "reason": "review", "cause": cause})
    write_state(ident, state=state)


def main():
    p = argparse.ArgumentParser(prog="korrigans run", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("id", nargs="?", default="", help="task id (e.g. T-0002)")
    p.add_argument("--harness", help="force a harness of harness/harness.toml")
    p.add_argument("--rank", help="force one rank (name, or model:effort from rules/escalation.toml), no climbing")
    p.add_argument("--role", help="agent of agents/, e.g. virgil (default: from the task type)")
    p.add_argument("--personality", help="for this run (see personalities/)")
    p.add_argument("--no-watch", action="store_true", help="run without the Watch")
    p.add_argument("--dry-run", action="store_true", help="show without running")
    p.add_argument("--wait-quota", action="store_true", help="wait and retry when all harnesses hit quota")
    p.add_argument("--resume-waiting", action="store_true", help="resume tasks in state/execution/*.json that are waiting for quota")
    args = p.parse_args()

    if args.resume_waiting:
        resume_waiting_tasks()
        return

    if not args.id:
        p.error("the following arguments are required: id")

    r = rules()
    harnesses = common.read_toml("harness/harness.toml")
    folder = task_dir(args.id)
    charter = folder / "charter.md"
    ident = folder.name[:6]
    type_ = read_field(charter, "task_type")
    routing = common.read_toml("rules/routing.toml")
    default_dir = routing.get("workdirs", {}).get(type_) or common.WS
    workdir = Path(read_field(charter, "workdir") or default_dir).expanduser()
    role = args.role
    if not role:
        role = ROLE_BY_TYPE.get(type_, DEFAULT_ROLE)
        if not agent_exists(role):
            role = DEFAULT_ROLE
    project = common.target(read_field(charter, "project")) or None
    personality = args.personality or common.target(read_field(charter, "personality")) or None
    agent_ident, agent_text = common.assemble_agent(role, personality, project)
    order = [args.harness] if args.harness else routing.get("types", {}).get(type_, [])
    if not order:
        sys.exit(f"No harness planned for task type '{type_}' in rules/routing.toml")
    unknown = [h for h in order if h not in harnesses]
    if unknown:
        sys.exit(f"Unknown harness: {', '.join(unknown)} (known: {', '.join(harnesses)})")

    difficulty, source = classify(charter, dry_run=args.dry_run)
    steps = ladder(difficulty, order, r)
    forced = args.rank or read_field(charter, "rank")
    if forced:
        rk = rank(forced, r)
        steps = [{"rank": rk, "harnesses": [h for h in order if r["models"][rk["model"]].get(h)],
                  "difficulty": difficulty, "watch": steps[0]["watch"] if steps else ""}]
    if not any(s["harnesses"] for s in steps):
        sys.exit(f"No rank has a model for {', '.join(order)} (rules/escalation.toml)")
    active = r.get("watch", {}).get("active", {})
    access = read_access(charter)
    if not args.dry_run:
        write_state(ident, title=read_field(charter, "title"), folder=str(folder), difficulty=difficulty,
                    link=common.link_to(charter)[2:-2], state="starting", verdict=None)
    print(f"{ident}: difficulty {difficulty} ({source}), {role} as {agent_ident['personality']}, "
          f"starting at {steps[0]['rank']['label']}, in {workdir}")

    for number, step in enumerate(steps, 1):
        rk, names, level = step["rank"], step["harnesses"], step["difficulty"]
        watch_rank = step["watch"] if active.get(level) and not args.no_watch else ""
        max_seconds = 60 * r.get("max_minutes", {}).get(level, 0)
        if level != difficulty and not args.dry_run:
            add("difficulty_revised", ident, detail={"from": difficulty, "to": level, "rank": rk["name"]})
            write_field(charter, "difficulty", level)
            write_state(ident, difficulty=level)
            difficulty = level
        prompt = build_prompt(agent_text, folder, access)
        role_file = folder / "prompt.md"
        if not args.dry_run:
            role_file.write_text(prompt, encoding="utf-8")
        context = (f"{charter.read_text(encoding='utf-8')}\n\n"
                   f"Task {ident}, difficulty {difficulty}, rank {number}/{len(steps)} ({rk['label']}).")
        outcome = None
        for position, name in enumerate(names):
            harness = harnesses[name] | {"name": name}
            values = {"prompt": prompt, "role_text": prompt, "role_file": role_file, "workspace": common.WS}
            command = harness_command(harness, rk, r, values)
            if harness.get("extra_dir_option"):
                for path, _mode in access:
                    command += [harness["extra_dir_option"], path]
            if args.dry_run:
                print(f"  {number}. {rk['label']} ({level}) on {name} ({harness.get('subscription', '')})"
                      + (" if the quota ran out before" if position else f", watch {label(watch_rank, r) or 'none'}")
                      + ":")
                print("     " + " ".join("<prompt>" if part == prompt else part for part in command))
                continue
            write_field(charter, "assigned_to", f"{role}@{name}:{rk['name']}")
            write_state(ident, state="running", rank=rk["label"], step=number, steps=len(steps), harness=name,
                        attempt_start=datetime.now().isoformat(timespec="seconds"))
            result, reason, trace = launch(name, harness, command, folder, workdir, rk, max_seconds,
                                           watch_rank, context)
            if result == "ok":
                ok, reason = verify(charter, workdir)
                if ok:
                    write_state(ident, state="done", end=datetime.now().isoformat(timespec="seconds"))
                    if number > 1:
                        add("escalation_succeeded", ident, tool=name, detail={"rank": rk["name"], "step": number})
                    return
                result = "failed"
            if result in ("quota", "missing"):
                print(f"{name} unavailable ({result}), next harness")
                continue
            note_attempt(folder, rk, name, result, reason, trace)
            outcome = result
            break
        if args.dry_run:
            continue
        if outcome == "stop":
            hand_back(charter, ident, "watch", "stopped")
            sys.exit(f"The Watch stopped the task: see {folder.relative_to(common.WS)}/attempts.md")
        if outcome is None:
            reset_dt = get_next_reset(names)
            next_retry_str = reset_dt.isoformat(timespec="seconds")
            add("waiting_quota", ident, detail={"rank": rk["name"], "order": names, "next_retry_at": next_retry_str})
            write_state(ident, state="waiting for quota", next_retry_at=next_retry_str)
            proj_fm, _ = common.read_note(common.WS / "projects" / project / "project.md") if project else ({}, "")
            is_low_priority = proj_fm.get("intensity") in ("background", "watch")
            if args.wait_quota or is_low_priority:
                print(f"Every harness of this rank is unavailable (quota). Waiting for quota until {next_retry_str}...")
                while True:
                    now = datetime.now().astimezone()
                    if now >= reset_dt:
                        print("Quota reset time reached! Retrying rank...")
                        break
                    sleep_secs = min(30, max(1, int((reset_dt - now).total_seconds())))
                    time.sleep(sleep_secs)
                continue
            sys.exit("Every harness of this rank is unavailable: the task waits for a quota to come back.")
        if number < len(steps):
            following = steps[number]["rank"]
            add("escalation", ident, detail={"from": rk["name"], "to": following["name"], "reason": outcome})
            write_state(ident, state="climbing", rank=following["label"])
            print(f"\n{rk['label']} did not succeed ({outcome}): climbing to {following['label']}\n")
    if not args.dry_run:
        hand_back(charter, ident, "ladder_exhausted", "ladder exhausted")
        sys.exit(f"Ladder exhausted ({len(steps)} ranks tried): see {folder.relative_to(common.WS)}/attempts.md")


if __name__ == "__main__":
    main()
