#!/usr/bin/env python3
"""See, assemble and list the agents (agents/<agent>/IDENTITY.md, AGENTS.md, SOUL.md).

    korrigans agent --list                               every agent: display name, mode, personality, model, project
    korrigans agent seneschal                            print the Seneschal's assembled prompt
    korrigans agent commanders/lab --personality cautious
    korrigans agent chamberlain --write                  write state/roles/chamberlain.md and print its path
    korrigans agent --personalities                      the personalities available

Agents are looked up in the workspace, the enabled modules and the core (the first layer that has a file wins).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def write_role(agent, personality=None, project=None):
    """Assemble the agent and write state/roles/<agent-with-dashes>.md. Returns (identity, text, path)."""
    ident, text = common.assemble_agent(agent, personality, project)
    path = common.state_dir("roles") / f"{agent.replace('/', '-')}.md"
    path.write_text(text, encoding="utf-8")
    return ident, text, path


def print_list():
    print(f"{'agent':<24}{'name':<24}{'mode':<10}{'personality':<14}{'model':<10}project")
    for agent, _ in common.list_agents():
        i = common.identity(agent)
        print(f"{agent:<24}{i.get('display_name', ''):<24}{i.get('mode', ''):<10}"
              f"{common.target(i.get('personality')):<14}{i.get('model', ''):<10}{common.target(i.get('project'))}")


def print_personalities():
    found = common.list_names("personalities", "*.md")
    found.pop("README", None)
    for name, path in found.items():
        print(f"{name:<14}{common.read_note(path)[0].get('summary', '')}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("agent", nargs="?")
    p.add_argument("--personality")
    p.add_argument("--project")
    p.add_argument("--write", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--personalities", action="store_true")
    args = p.parse_args()
    if args.list:
        return print_list()
    if args.personalities:
        return print_personalities()
    if not args.agent:
        p.error("name an agent, or use --list")
    if args.write:
        print(write_role(args.agent, args.personality, args.project)[2])
    else:
        print(common.assemble_agent(args.agent, args.personality, args.project)[1])


if __name__ == "__main__":
    main()
