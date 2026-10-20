#!/usr/bin/env python3
"""Task difficulty, the ladder of ranks and the Watch, from rules/escalation.toml.

    korrigans ladder classify T-0002             difficulty (charter, else rules, else the Constable)
    korrigans ladder classify T-0002 --write     write it in the charter's difficulty field
    korrigans ladder classify T-0002 --dry-run   show the call to the Constable without making it
    korrigans ladder show T-0002                 ranks that will be tried, in order, with harnesses and watch
    korrigans ladder show --difficulty medium

korrigans run uses it to pick the first rank, climb one rank when an attempt fails, and run the Watch
during an attempt. A rank is a name from the ladder (knight) or a raw "model:effort" (mid:high).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from task import read_field, task_dir, write_field  # noqa: E402

VERDICTS = ("continue", "advise", "escalate", "stop")
CLASSIFIER = "constable"
WATCHER = "watch"
CLASSIFY_REQUEST = "Rate the difficulty of this task."
VERDICT_REQUEST = "Answer with a single JSON object:"


def rules():
    return common.read_toml("rules/escalation.toml")


def rank(name, r=None):
    """A rank name ("knight") or a raw "model:effort" ("mid:high") ->
    {"name", "spec", "model", "effort", "label"}; the model is a short name from [models]."""
    r = r or rules()
    ranks = r.get("ranks", {})
    spec = ranks.get(name, name)
    short, _, effort = spec.partition(":")
    if short not in r.get("models", {}):
        raise SystemExit(f"Rank {name}: not a rank of [ranks] ({', '.join(ranks)}) and model {short} is not in "
                         "[models] of rules/escalation.toml")
    effort = effort or r.get("default_effort", "medium")
    spec = f"{short}:{effort}"
    return {"name": name, "spec": spec, "model": short, "effort": effort,
            "label": f"{name} ({spec})" if name in ranks else spec}


def rank_index(name, r):
    """Position on the ladder of a rank name or of a raw "model:effort"; None if it is not on it."""
    names = r["ladder"]
    if name in names:
        return names.index(name)
    spec = rank(name, r)["spec"] if name else ""
    return next((i for i, n in enumerate(names) if rank(n, r)["spec"] == spec), None)


def label(name, r=None):
    """"knight (mid:medium)" for a rank name, the raw spec otherwise; "" for nothing."""
    return rank(name, r)["label"] if name else ""


def harness_command(harness, rk, r, values):
    """Run command of a harness for a rank, or None when the harness has no model for it."""
    model = r["models"][rk["model"]].get(harness["name"])
    if not model:
        return None
    effort = harness.get("efforts", {}).get(rk["effort"], rk["effort"])
    return common.fill(harness["run"], values | {"model": model, "effort": effort})


def classify(charter, dry_run=False):
    """(difficulty, source). The charter first, then the rules, then the Constable, then the default."""
    r = rules()
    known = list(r["difficulties"])
    d = read_field(charter, "difficulty")
    if d in known:
        return d, "charter"
    c = r.get("classify", {})
    cost = read_field(charter, "cost")
    if cost in c.get("by_cost", {}):
        return c["by_cost"][cost], f"rule: cost {cost}"
    type_ = read_field(charter, "task_type")
    if type_ in c.get("by_type", {}):
        return c["by_type"][type_], f"rule: type {type_}"
    if c.get("rank"):
        answer = ask_model(c["rank"], CLASSIFIER, classify_prompt(charter, r), Path(charter).parent, dry_run)
        word = next((w for w in re.findall(r"[a-z]+", (answer or "").lower()) if w in known), None)
        if word:
            return word, f"the Constable, {label(c['rank'], r)}"
    return c.get("default", "medium"), "default"


def classify_prompt(charter, r):
    lines = "\n".join(f"- {d}: {text}" for d, text in r["difficulties"].items())
    return (f"{CLASSIFY_REQUEST} Answer with one word among: {', '.join(r['difficulties'])}.\n\n"
            f"{lines}\n\n---\n\n{Path(charter).read_text(encoding='utf-8')}")


def ask_model(rank_name, agent, prompt, folder, dry_run=False):
    """Short non-interactive call of a model (Constable, Watch). Returns its text output, or None."""
    r = rules()
    rk = rank(rank_name, r)
    harnesses = common.read_toml("harness/harness.toml")
    choice = r.get("short_calls", {}).get("harness", ["pi"])
    choice = [choice] if isinstance(choice, str) else choice
    name = next((h for h in choice if h in harnesses and r["models"][rk["model"]].get(h)
                 and shutil.which(harnesses[h]["run"][0])), None)
    if not name:
        return None
    harness = harnesses[name] | {"name": name}
    try:
        _, role = common.assemble_agent(agent)
    except SystemExit as e:
        print(f"warning: {e}; calling without the role text", file=sys.stderr)
        role = ""
    text = f"{role}\n---\n\n{prompt}" if role else prompt
    role_file = Path(folder) / f".{agent.replace('/', '-')}-prompt.md"
    command = harness_command(harness, rk, r, {"prompt": text, "role_text": text, "role_file": role_file,
                                               "workspace": common.WS})
    if not command:
        return None
    if dry_run:
        print(f"  {agent}: " + " ".join("<prompt>" if part == text else part for part in command))
        return None
    role_file.write_text(text, encoding="utf-8")
    try:
        out = subprocess.run(command, cwd=common.WS, capture_output=True, text=True,
                             timeout=r.get("short_calls", {}).get("timeout_seconds", 120))
        return out.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def ladder(difficulty, harness_order, r=None):
    """The steps tried, in order: one ladder, the difficulty gives the starting rank.

    Each step: {"rank" (see rank()), "harnesses" (those with a model for it), "difficulty" (the one whose
    start it is or passes), "watch" (rank name of the Watch, above the korrigan's)}."""
    r = r or rules()
    names = r["ladder"]
    starts = {}
    for d in r["difficulties"]:
        i = rank_index(r["start"][d], r)
        if i is None:
            raise SystemExit(f"[start] {d} = {r['start'][d]} is not on the ladder of rules/escalation.toml")
        starts[d] = i
    if difficulty not in starts:
        raise SystemExit(f"Unknown difficulty: {difficulty} (known: {', '.join(starts)})")
    first = starts[difficulty]
    w = r.get("watch", {})
    floor = rank_index(w["minimum"], r) if w.get("minimum") else 0
    floor = floor or 0
    steps = []
    for i in range(first, min(len(names), first + r.get("max_attempts", len(names)))):
        rk = rank(names[i], r)
        harnesses = [h for h in harness_order if r["models"][rk["model"]].get(h)]
        if not harnesses:
            continue
        level = max((d for d, j in starts.items() if j <= i), key=lambda d: starts[d])
        watch = names[min(len(names) - 1, max(floor, i + int(w.get("gap", 2))))]
        steps.append({"rank": rk, "harnesses": harnesses, "difficulty": level, "watch": watch})
    return steps


class Watch(threading.Thread):
    """Follows a running attempt and asks a model stronger than the korrigan for a verdict.

    It does not reread the whole conversation: it gets the progress (progress.md, kept by the korrigan), the
    changed files, signs of a loop taken from the trace, and the end of the trace. The start of its prompt
    (role, charter) does not change between calls, so the provider can keep it in cache; only the progress
    changes, at the end. It calls the model only when something moved, or when nothing has moved for
    `silence_minutes`.

    continue: nothing; advise: the advice is appended to advice.md, which the korrigan rereads between
    steps; escalate: the attempt is stopped and the next rank takes over; stop: everything stops and the
    task goes back to the user. The verdict is logged in the journal and shown in the watchtower."""

    def __init__(self, proc, trace, folder, context, watch_rank, workdir, dry_run=False):
        super().__init__(daemon=True)
        w = rules().get("watch", {})
        self.proc, self.trace, self.folder, self.context = proc, trace, folder, context
        self.workdir = workdir
        self.every = float(w.get("every_minutes", 5)) * 60
        self.silence = float(w.get("silence_minutes", 15)) * 60
        self.lines = int(w.get("lines", 40))
        self.rank = watch_rank
        self.dry_run = dry_run
        self.verdict = None
        self.halt = threading.Event()
        self.fingerprint, self.last_call = None, time.time()
        self.reported = False

    def run(self):
        while not self.halt.wait(self.every):
            if self.proc.poll() is not None:
                return
            fingerprint = (self.trace.stat().st_size, _size(self.folder / "progress.md"))
            quiet = fingerprint == self.fingerprint
            if quiet and time.time() - self.last_call < self.silence:
                continue
            self.fingerprint, self.last_call = fingerprint, time.time()
            v = self.check(quiet)
            if v and v["verdict"] in ("escalate", "stop") and not self.halt.is_set():
                self.verdict = v
                self.proc.terminate()
                return

    def check(self, quiet=False):
        from journal import add
        from track import write_state
        ident = self.folder.name[:6]
        lines = self.trace.read_text(encoding="utf-8", errors="replace").splitlines()
        repeated = _repetitions(lines)
        progress = self.folder / "progress.md"
        prompt = (
            f"{self.context}\n\n---\n\n## Progress check\n\n"
            f"Trace: {len(lines)} lines."
            + (" Nothing has moved since the last check." if quiet else "") + "\n\n"
            "### progress.md (kept by the korrigan)\n\n"
            + ("\n".join(progress.read_text(encoding="utf-8").splitlines()[-25:]) if progress.exists()
               else "(missing: the korrigan has not written it yet)") + "\n\n"
            f"### Files changed in the working folder\n\n{_changes(self.workdir)}\n\n"
            "### Repeated lines in the trace (sign of a loop)\n\n" + (repeated or "none") + "\n\n"
            f"### End of the trace ({self.lines} lines at most)\n\n```text\n" + "\n".join(lines[-self.lines:])
            + "\n```\n\n"
            f'{VERDICT_REQUEST} {{"verdict": "continue|advise|escalate|stop", '
            '"reason": "one sentence", "advice": "one to three sentences for the korrigan, or empty"}')
        out = ask_model(self.rank, WATCHER, prompt, self.folder, self.dry_run)
        v = read_verdict(out)
        if not v:
            if not self.reported:
                self.reported = True
                add("watch_unavailable", ident, agent=WATCHER,
                    detail={"rank": self.rank, "reason": "no harness available or unreadable answer"})
                write_state(ident, verdict={"verdict": "unavailable", "reason": f"watch {self.rank} unreachable"})
            return None
        add("watch", ident, agent=WATCHER, detail=v | {"rank": self.rank})
        write_state(ident, verdict=v | {"time": datetime.now().strftime("%H:%M")})
        if v["verdict"] == "advise" and v.get("advice"):
            with (self.folder / "advice.md").open("a", encoding="utf-8") as f:
                f.write(f"\n## {datetime.now():%H:%M} (watch)\n\n{v['advice']}\n")
        return v


def _size(path):
    return path.stat().st_size if path.exists() else 0


def _repetitions(lines, threshold=3):
    """Non-empty lines seen at least `threshold` times in the last 300, digits ignored."""
    normal = [re.sub(r"\d+", "#", l.strip()) for l in lines[-300:] if len(l.strip()) > 8]
    return "\n".join(f"- {n} times: {l[:160]}" for l, n in Counter(normal).most_common(5) if n >= threshold)


def _changes(workdir):
    r = subprocess.run(["git", "-C", str(workdir), "status", "--short"], capture_output=True, text=True)
    if r.returncode != 0:
        return "(not a git repository)"
    return "\n".join(r.stdout.splitlines()[:30]) or "(none)"


def read_verdict(out):
    """The last JSON object of the output that carries a known verdict, or None."""
    for raw in reversed(re.findall(r"\{[^{}]*\}", out or "", re.S)):
        try:
            v = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(v, dict) and v.get("verdict") in VERDICTS:
            return v
    return None


def main():
    p = argparse.ArgumentParser(prog="korrigans ladder", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="command", required=True)
    c = sp.add_parser("classify", help="difficulty of a task")
    c.add_argument("id")
    c.add_argument("--write", action="store_true", help="write it in the charter")
    c.add_argument("--dry-run", action="store_true", help="show the call to the Constable without making it")
    s = sp.add_parser("show", help="ranks that will be tried")
    s.add_argument("id", nargs="?")
    s.add_argument("--difficulty")
    args = p.parse_args()
    r = rules()
    if args.command == "classify":
        charter = task_dir(args.id) / "charter.md"
        d, source = classify(charter, args.dry_run)
        print(f"{d} ({source})")
        if args.write:
            write_field(charter, "difficulty", d)
        return
    if args.id:
        charter = task_dir(args.id) / "charter.md"
        difficulty = args.difficulty or classify(charter)[0]
        order = common.read_toml("rules/routing.toml").get("types", {}).get(read_field(charter, "task_type"), [])
    else:
        difficulty = args.difficulty or r.get("classify", {}).get("default", "medium")
        order = list(common.read_toml("harness/harness.toml"))
    if difficulty not in r["difficulties"]:
        sys.exit(f"Unknown difficulty: {difficulty} (known: {', '.join(r['difficulties'])})")
    print(f"Difficulty {difficulty}: {r['difficulties'][difficulty]}")
    for i, step in enumerate(ladder(difficulty, order, r), 1):
        print(f"  {i}. {step['rank']['label']:<24} ({step['difficulty']:<6}) on {', '.join(step['harnesses']):<26} "
              f"watch {label(step['watch'], r)}")


if __name__ == "__main__":
    main()
