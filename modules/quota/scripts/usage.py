#!/usr/bin/env python3
"""Subscription usage, and the alert "quota to use before the reset".

    korrigans usage state               every subscription (rules/subscriptions.toml)
    korrigans usage alert               only those under the threshold, close to their reset
    korrigans usage set chatgpt 45      record a usage of 45 % by hand
    korrigans usage statusline          plug in as Claude Code's status line: reads its JSON on stdin,
                                        keeps the usage of the 7-day window, prints one line
Add --json to state or alert for a machine-readable answer.

Each value says where it comes from: measured, estimated (journal), set by hand, or unknown.
The Seneschal calls `korrigans usage alert` for the Morning Chronicle and when the user talks to it
(skill propose-backlog). Never pay as you go: when the purse is empty, the korrigans rest.
"""
import argparse
import calendar
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(os.environ.get("KORRIGANS_CORE") or Path(__file__).resolve().parents[3]) / "scripts"))
import common  # noqa: E402
from journal import read_events  # noqa: E402

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def next_reset(sub, now):
    """Local date of the next reset, and the length of the window."""
    when, _, hour = sub["reset"].partition(" ")
    h, m = (int(x) for x in (hour or "00:00").split(":"))
    if sub["window"] == "week":
        day = WEEKDAYS.index(when.lower())
        reset = now.replace(hour=h, minute=m, second=0, microsecond=0)
        reset += timedelta(days=(day - now.weekday()) % 7)
        if reset <= now:
            reset += timedelta(days=7)
        return reset, timedelta(days=7)

    def on(year, month):
        return now.replace(year=year, month=month, day=min(int(when), calendar.monthrange(year, month)[1]),
                           hour=h, minute=m, second=0, microsecond=0)

    reset = on(now.year, now.month)
    if reset <= now:
        reset = on(now.year + (now.month == 12), now.month % 12 + 1)
    return reset, timedelta(days=30)


def reset_date(value, now):
    """resets_at from a harness: ISO date, Unix timestamp, or seconds left."""
    if value in (None, ""):
        return None
    try:
        if isinstance(value, (int, float)):
            if value > 1e9:
                return datetime.fromtimestamp(value, timezone.utc).astimezone()
            return now + timedelta(seconds=value)
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone()
    except (ValueError, OverflowError, OSError):
        return None


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def measure_claude():
    d = read_json(common.WS / "state" / "usage-claude.json")
    if d and d.get("used") is not None:
        return d["used"] / 100, "measured", d.get("resets_at")
    return None


def find_limits(obj, found):
    """Walk a Codex session JSON and keep the blocks that look like a usage limit."""
    if isinstance(obj, dict):
        if "used_percent" in obj:
            found.append(obj)
        for v in obj.values():
            find_limits(v, found)
    elif isinstance(obj, list):
        for v in obj:
            find_limits(v, found)


def measure_codex():
    sessions = sorted(Path("~/.codex/sessions").expanduser().rglob("*.jsonl"),
                      key=lambda f: f.stat().st_mtime, reverse=True)[:5]
    for path in sessions:
        for line in reversed(path.read_text(encoding="utf-8", errors="ignore").splitlines()):
            if "used_percent" not in line:
                continue
            found = []
            try:
                find_limits(json.loads(line), found)
            except json.JSONDecodeError:
                continue
            if found:
                week = max(found, key=lambda b: b.get("window_minutes") or 0)
                reset = week.get("resets_at") or week.get("resets_in_seconds")
                return float(week["used_percent"]) / 100, "measured", reset
    return None


def measure_journal(sub, start):
    cap = sub.get("run_cap")
    if not cap:
        return None
    n = sum(1 for e in read_events(start.astimezone(timezone.utc))
            if e.get("type") == "run_start" and e.get("tool") in sub["harness"])
    return min(n / cap, 1.0), f"estimated ({n} runs / {cap})", None


def measure_manual(name, start):
    d = (read_json(common.WS / "state" / "usage-manual.json") or {}).get(name)
    if d and datetime.fromisoformat(d["on"]) >= start:
        return d["used"] / 100, f"set on {d['on'][:10]}", None
    return None


def state():
    config = common.read_toml("rules/subscriptions.toml")
    default = config.pop("default", {})
    now = datetime.now().astimezone()
    rows = []
    for name, sub in config.items():
        if not isinstance(sub, dict):
            continue
        reset, length = next_reset(sub, now)
        start = reset - length
        measure = None
        if sub.get("measure") == "claude-statusline":
            measure = measure_claude()
        elif sub.get("measure") == "codex-sessions":
            measure = measure_codex()
        measure = measure or measure_manual(name, start) or measure_journal(sub, start)
        used, source, measured_reset = measure or (None, "unknown", None)
        assumed = sub.get("assumed", False)
        measured_reset = reset_date(measured_reset, now)
        if measured_reset:
            reset, assumed = measured_reset, False
        hours = (reset - now).total_seconds() / 3600
        threshold = sub.get("threshold", default.get("threshold", 0.7))
        warn = sub.get("warn_hours", default.get("warn_hours", 48))
        rows.append({
            "subscription": name, "harness": sub["harness"], "window": sub["window"],
            "reset": reset.isoformat(timespec="minutes"), "reset_assumed": assumed,
            "hours_to_reset": round(hours, 1), "usage": None if used is None else round(used, 2),
            "source": source, "threshold": threshold,
            "use_before_reset": used is not None and used < threshold and hours <= warn,
        })
    return rows


def show(rows):
    for r in rows:
        used = "?" if r["usage"] is None else f"{r['usage']:.0%}"
        mark = "  <- use before the reset" if r["use_before_reset"] else ""
        assumed = " (reset assumed)" if r["reset_assumed"] else ""
        print(f"{r['subscription']:<12} {used:>5} of the {r['window']} ({r['source']}), reset in "
              f"{r['hours_to_reset']:.0f} h{assumed}{mark}")


def statusline():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}
    week = (data.get("rate_limits") or {}).get("seven_day") or {}
    if week.get("used_percentage") is not None:
        (common.state_dir() / "usage-claude.json").write_text(json.dumps({
            "used": week["used_percentage"], "resets_at": week.get("resets_at"),
            "on": datetime.now().astimezone().isoformat(timespec="seconds"),
        }), encoding="utf-8")
        print(f"week {week['used_percentage']:.0f} %")
    else:
        print("")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="command", required=True)
    for name in ("state", "alert"):
        sp.add_parser(name).add_argument("--json", action="store_true")
    s = sp.add_parser("set")
    s.add_argument("subscription")
    s.add_argument("percent", type=float)
    sp.add_parser("statusline")
    args = p.parse_args()
    if args.command == "statusline":
        return statusline()
    if args.command == "set":
        path = common.state_dir() / "usage-manual.json"
        data = read_json(path) or {}
        data[args.subscription] = {"used": args.percent, "on": datetime.now().astimezone().isoformat(timespec="seconds")}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return print(f"{args.subscription}: {args.percent:.0f} % recorded")
    rows = state()
    if args.command == "alert":
        rows = [r for r in rows if r["use_before_reset"]]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif rows:
        show(rows)
    elif args.command == "alert":
        print("No subscription to use before its reset.")
    else:
        print("No subscription yet: copy an example from `korrigans which rules/subscriptions.toml` "
              "into rules/subscriptions.toml in your workspace.")


if __name__ == "__main__":
    main()
