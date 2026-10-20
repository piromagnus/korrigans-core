#!/usr/bin/env python3
"""The core must not carry anybody's personal data.

Generic checks: home paths, real-looking email addresses, secrets, and non-English text (the core is in English).
Personal words: list them, one per line, in a file outside the repository and point KORRIGANS_DENYLIST at it
(default ~/.config/korrigans/denylist.txt). The list itself never enters the repository.

    python3 tests/test_no_personal_data.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", "node_modules", "target"}
SKIP_FILES = {"LICENSE"}
TEXT = {".md", ".py", ".sh", ".toml", ".yaml", ".yml", ".json", ".base", ".txt", ""}
CHECKS = [
    ("home path", re.compile(r"/(?:home|Users)/(?!user\b|you\b|me\b)[a-z][\w.-]+")),
    ("email", re.compile(r"[\w.+-]+@(?!example\.(?:org|com)\b|localhost\b|users\.noreply\.github\.com\b)"
                         r"[\w-]+(?:\.[\w-]+)*\.(?!md\b|py\b|toml\b|json\b|sh\b|ya?ml\b|txt\b)[a-z]{2,}\b")),
    ("secret", re.compile(r"(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|xox[bp]-[\w-]{10,}|_TOKEN=\S+)")),
    ("non-English letters", re.compile(r"[éèêëàâäçùûüîïôöœÉÈÀÇ]")),
]


def files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not SKIP_DIRS & set(p.relative_to(ROOT).parts) and p.name not in SKIP_FILES \
                and p.suffix in TEXT and p.name != Path(__file__).name:
            yield p


def denylist():
    path = Path(os.environ.get("KORRIGANS_DENYLIST", "~/.config/korrigans/denylist.txt")).expanduser()
    if not path.exists():
        return []
    words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines() if w.strip() and not w.startswith("#")]
    return [(f"personal word ({w[:2]}...)", re.compile(rf"(?i)(?<![\w]){re.escape(w)}(?![\w])")) for w in words]


def main():
    checks = CHECKS + denylist()
    problems = 0
    for p in files():
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for label, rx in checks:
                m = rx.search(line)
                if m:
                    problems += 1
                    shown = m.group(0) if not label.startswith("personal") else "***"
                    print(f"{p.relative_to(ROOT)}:{n}: {label}: {shown}")
    print(f"{'FAIL' if problems else 'PASS'}: personal data check ({problems} finding(s), {len(checks) - len(CHECKS)} personal word(s) checked)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
