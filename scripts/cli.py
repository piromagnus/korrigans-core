#!/usr/bin/env python3
"""korrigans <command> [args]: run scripts/<command>.py or .sh from the workspace, a module or the core.

    korrigans help                  list the commands available in this workspace
    korrigans which <rel/path>      the file actually used for a relative path (workspace, module or core)
    korrigans update                pull the core, then regenerate the harness files
"""
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def commands():
    found = {}
    for layer in reversed(common.layers()):
        d = layer / "scripts"
        if d.is_dir():
            for p in d.iterdir():
                if p.suffix in (".py", ".sh") and not p.stem.startswith("_") and p.stem not in ("common", "cli"):
                    found[p.stem] = p
    return dict(sorted(found.items()))


def summary(path):
    for line in path.read_text(encoding="utf-8").splitlines()[:6]:
        line = line.strip().strip('"').lstrip("#").strip()
        if line and not line.startswith(("!", "/usr", "-*-")) and "env " not in line:
            return line
    return ""


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        print(__doc__)
        print(f"workspace: {common.WS}\ncore:      {common.CORE}\nmodules:   {', '.join(common.modules()) or 'none'}\n")
        for name, path in commands().items():
            print(f"  {name:<12}{summary(path)}")
        return
    name, rest = args[0], args[1:]
    if name == "which":
        if not rest:
            sys.exit("korrigans which <relative/path>")
        p = common.find(rest[0])
        print(p if p else f"not found: {rest[0]}")
        sys.exit(0 if p else 1)
    if name == "update":
        r = subprocess.run(["git", "-C", str(common.CORE), "pull", "--ff-only"])
        if r.returncode != 0:
            sys.exit("git pull failed: the core was not updated")
        name, rest = "generate", []
    script = commands().get(name)
    if not script:
        sys.exit(f"Unknown command: {name}. Try: korrigans help")
    env = os.environ | {"KORRIGANS_WORKSPACE": str(common.WS), "KORRIGANS_CORE": str(common.CORE),
                        "PYTHONPATH": os.pathsep.join(filter(None, [str(common.CORE / "scripts"),
                                                                    os.environ.get("PYTHONPATH")]))}
    runner = ["bash"] if script.suffix == ".sh" else [sys.executable]
    sys.exit(subprocess.run(runner + [str(script)] + rest, env=env).returncode)


if __name__ == "__main__":
    main()
