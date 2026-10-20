#!/usr/bin/env python3
"""Extract the mail received since the last run, for the Chamberlain.

Reads local mailboxes in mbox format (Thunderbird by default), read only. Writes a raw extract in state/mail/
(git-ignored: raw mail is never versioned) and prints its path. The Chamberlain reads it, sorts it, and writes
the summary for the Seneschal in mail/YYYY-MM-DD.md.

    korrigans mail                       since the last run (at most 3 days back; by default since midnight)
    korrigans mail --since 2026-10-12T00:00

Mailboxes: korrigans.toml [mail] mailboxes = ["~/path/to/*/INBOX", ...] (glob patterns), else Thunderbird's inboxes.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timedelta
from email import message_from_bytes
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(os.environ.get("KORRIGANS_CORE") or Path(__file__).resolve().parents[3]) / "scripts"))
import common  # noqa: E402

THUNDERBIRD = ["~/.thunderbird/*/ImapMail/*/INBOX", "~/.thunderbird/*/Mail/*/Inbox"]
TAIL = 16_000_000   # new mail is at the end of an mbox file: read only its last 16 MB


def mailboxes():
    return common.config().get("mail", {}).get("mailboxes") or THUNDERBIRD


def decoded(header):
    try:
        return str(make_header(decode_header(header or "")))
    except Exception:
        return header or ""


def excerpt(msg, limit=600):
    part = None
    if msg.is_multipart():
        for p in msg.walk():
            if p.get_content_type() == "text/plain" and not p.get_filename():
                part = p
                break
    elif msg.get_content_type() == "text/plain":
        part = msg
    if part is None:
        return ""
    try:
        raw = (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", errors="replace")
    except Exception:
        return ""
    return " ".join(raw.split())[:limit]


def extract(since):
    seen, out = set(), []
    paths = sorted(p for pattern in mailboxes() for p in glob.glob(os.path.expanduser(pattern)))
    for path in paths:
        account = os.path.basename(os.path.dirname(path))
        try:
            with open(path, "rb") as f:
                start = max(0, os.path.getsize(path) - TAIL)
                f.seek(start)
                tail = (b"\n" if start == 0 else b"") + f.read()
        except OSError:
            continue
        cut = tail.find(b"\nFrom ")
        if cut == -1:
            continue
        for block in tail[cut + 1:].split(b"\nFrom "):
            try:
                msg = message_from_bytes(block.split(b"\n", 1)[1])
                raw_date = msg.get("Date")
                if not raw_date:
                    continue
                dt = parsedate_to_datetime(raw_date)
                if dt.tzinfo is None:
                    dt = dt.astimezone()
                if dt < since:
                    continue
                ident = msg.get("Message-ID") or f"{raw_date}|{msg.get('Subject')}|{account}"
                if ident in seen:
                    continue
                seen.add(ident)
                try:
                    unread = not (int(msg.get("X-Mozilla-Status", "0"), 16) & 0x0001)
                except ValueError:
                    unread = False
                out.append((dt, {
                    "account": account, "date": dt.isoformat(timespec="minutes"), "from": decoded(msg.get("From")),
                    "to": decoded(msg.get("To")), "subject": decoded(msg.get("Subject")), "unread": unread,
                    "message_id": msg.get("Message-ID", ""), "excerpt": excerpt(msg),
                }))
            except Exception:
                continue
    return [m for _, m in sorted(out, key=lambda x: x[0])], len(paths)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since", help="local ISO date")
    args = p.parse_args()
    folder = common.state_dir("mail")
    last_run = folder / "last-run.json"
    now = datetime.now().astimezone()
    if args.since:
        since = datetime.fromisoformat(args.since).astimezone()
    else:
        try:
            since = datetime.fromisoformat(json.loads(last_run.read_text())["on"])
        except (OSError, ValueError, KeyError):
            since = now.replace(hour=0, minute=0, second=0, microsecond=0)
        since = max(since, now - timedelta(days=3))
    mails, boxes = extract(since)
    path = folder / f"{now:%Y-%m-%dT%H%M}.json"
    path.write_text(json.dumps({"since": since.isoformat(timespec="minutes"), "mailboxes_read": boxes,
                                "mails": mails}, ensure_ascii=False, indent=1), encoding="utf-8")
    last_run.write_text(json.dumps({"on": now.isoformat(timespec="seconds")}), encoding="utf-8")
    print(f"{len(mails)} mail(s) since {since:%Y-%m-%d %H:%M}, {boxes} mailbox(es) read: {path}")


if __name__ == "__main__":
    main()
