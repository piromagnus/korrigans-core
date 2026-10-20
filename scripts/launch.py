#!/usr/bin/env python3
"""Launch a steering session (the Seneschal or a Commander) on any harness, inside tmux.

    korrigans launch seneschal                              default harness (rules/routing.toml, [sessions])
    korrigans launch seneschal --harness pi
    korrigans launch commander --project lab --harness codex
    korrigans launch commander --project lab --personality adventurous
    korrigans launch seneschal --no-tmux                    in this terminal, without tmux
    korrigans launch seneschal --dry-run                    print the command without launching

If the harness stops at once, its window stays open with the exit code; state/roles/<agent>.sh reruns it by hand.

The prompt is assembled like `korrigans agent` from agents/seneschal/ or agents/commanders/<project>/, USER.md,
the project note, its people, its repos and data, and the personality. It is passed as a system prompt when
the harness allows it, otherwise as the first message (see harness/harness.toml).
"""
import argparse
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
from agent import write_role  # noqa: E402

STARTUP = ("At startup, read MEMORY.md, the files in memory/global/ and your role memory ({memory}), "
           "then introduce yourself in one line and wait for the user's messages.")


def agent_for(role, project):
    if role == "seneschal":
        return "seneschal"
    if not common.find(f"agents/commanders/{project}/IDENTITY.md"):
        sys.exit(f"No commander for {project}: copy agents/commanders/_template/ into "
                 f"agents/commanders/{project}/ in your workspace (`korrigans which agents/commanders/_template` "
                 f"shows where it is), or ask the Seneschal (skill adjust-agent).")
    return f"commanders/{project}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("role", choices=["seneschal", "commander"])
    p.add_argument("--project")
    p.add_argument("--harness")
    p.add_argument("--personality", help="for this session only (see `korrigans agent --personalities`)")
    p.add_argument("--no-tmux", action="store_true", help="run in this terminal instead of a tmux session")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    if args.role == "commander" and not args.project:
        sys.exit("A commander needs --project")

    agent = agent_for(args.role, args.project)
    sessions = common.read_toml("rules/routing.toml").get("sessions", {})
    harness_name = args.harness or sessions.get(args.role)
    if not harness_name:
        sys.exit(f"No harness for {args.role}: give --harness or set [sessions] {args.role} in rules/routing.toml")
    harness = common.read_toml("harness/harness.toml").get(harness_name)
    if not harness or "interactive" not in harness:
        sys.exit(f"Unknown harness or no interactive command: {harness_name} (see harness/harness.toml)")

    ident, text, role_file = write_role(agent, args.personality, args.project)
    role_text = text + "\n" + STARTUP.format(memory=ident.get("memory") or "none") + "\n"
    role_file.write_text(role_text, encoding="utf-8")
    session = agent.replace("/", "-")

    marker = "@@KORRIGANS_ROLE_TEXT@@"
    values = {"role_text": marker, "role_file": role_file, "prompt": marker, "workspace": common.WS,
              "model": harness.get("models", {}).get(ident.get("model") or "standard", ""), "effort": "high"}
    interactive = common.fill(harness["interactive"], values)
    program = interactive[0]
    # The role text is read from its file at launch: no giant argument in tmux, no quoting trouble.
    inline = f'"$(cat {shlex.quote(str(role_file))})"'

    def shell_of(command):
        return shlex.join(command).replace(shlex.quote(marker), inline).replace(marker, inline)

    shell = shell_of(interactive)
    if harness.get("resume"):
        shell = f"{shell_of(common.fill(harness['resume'], values))} || {shell}"

    tmux_name = f"{session}-{harness_name}"
    script = role_file.with_suffix(".sh")
    script.write_text(
        "#!/usr/bin/env bash\n"
        f"# Written by korrigans launch {args.role}. Run it by hand to see the harness directly: bash {script}\n"
        f"export PATH={shlex.quote(os.environ.get('PATH', ''))}\n"
        f"cd {shlex.quote(str(common.WS))} || exit 1\n"
        f"{shell}\n"
        "status=$?\n"
        'if [ "$status" -ne 0 ]; then\n'
        f'  echo; echo "korrigans: {harness_name} stopped with exit code $status."\n'
        '  read -r -p "Press Enter to close this window. " _\n'
        "fi\n", encoding="utf-8")
    script.chmod(0o755)

    if args.dry_run:
        print(f"[{harness_name}] {ident.get('display_name', agent)}, personality {ident['personality']}, "
              f"tmux session '{tmux_name}' in {common.WS}")
        print(f"assembled role: {role_file.relative_to(common.WS)}")
        print(f"launcher: {script.relative_to(common.WS)}")
        print(shell.replace(inline, "<role>"))
        return
    if not shutil.which(program):
        sys.exit(f"{program} not found in your PATH: install {harness_name}, or choose another harness with "
                 f"--harness (or [sessions] {args.role} in rules/routing.toml).")
    if args.no_tmux or not shutil.which("tmux"):
        if not args.no_tmux:
            print("tmux not found: the session runs in this terminal and ends with it.")
        os.execvp("bash", ["bash", str(script)])
    if subprocess.run(["tmux", "has-session", "-t", tmux_name], capture_output=True).returncode != 0:
        subprocess.run(["tmux", "new-session", "-d", "-s", tmux_name, "-c", str(common.WS), f"bash {shlex.quote(str(script))}"],
                       check=True)
        time.sleep(1)
        if subprocess.run(["tmux", "has-session", "-t", tmux_name], capture_output=True).returncode != 0:
            sys.exit(f"The {harness_name} session ended at once. To see why: bash {script}")
    if os.environ.get("TMUX"):
        subprocess.run(["tmux", "switch-client", "-t", tmux_name])
    else:
        subprocess.run(["tmux", "attach", "-t", tmux_name])

if __name__ == "__main__":
    main()
