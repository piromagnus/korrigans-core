#!/usr/bin/env bash
# The Morning Chronicle: mail, task manager, quota, frozen board, then the Chamberlain and the Seneschal.
#   korrigans daily              everything
#   korrigans daily --dry-run    print the commands without running them (only the agents' roles are assembled)
# Steps: mail extract (module mail), today's tasks (module todoist), quota alert (module quota), frozen board
# (reports/YYYY-MM-DD.md), then the Chamberlain (module mail, skill sort-mail) and the Seneschal (skill
# morning-chronicle) through the harness of [daily] in rules/routing.toml, then a commit limited to reports/,
# mail/ and journal/ if the workspace is a git repository.
# Secrets (TODOIST_API_TOKEN...) are loaded from the workspace's .env, never printed.
# Run it every morning with a timer: cron, systemd, launchd (docs/).
set -uo pipefail
CORE="${KORRIGANS_CORE:-$(cd "$(dirname "$0")/.." && pwd)}"
export KORRIGANS_CORE="$CORE"
WS="${KORRIGANS_WORKSPACE:-$(python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import common; print(common.WS)' "$CORE/scripts")}"
export KORRIGANS_WORKSPACE="$WS"
cd "$WS" || exit 1
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
DAY="$(date +%F)"
export PATH="$HOME/.local/bin:$HOME/bin:$PATH"
[ -s "$HOME/.nvm/nvm.sh" ] && . "$HOME/.nvm/nvm.sh" >/dev/null 2>&1
mkdir -p state

korrigans() { python3 "$CORE/scripts/cli.py" "$@"; }
MODULES=" $(python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import common; print(" ".join(common.modules()))' "$CORE/scripts") "
has() { case "$MODULES" in *" $1 "*) return 0 ;; esac; return 1; }
step() {  # run a data step, or print it with --dry-run
  if [ "$DRY" = 1 ]; then printf '   korrigans'; printf ' %q' "$@"; echo; return 0; fi
  korrigans "$@"
}
log() { [ "$DRY" = 1 ] || korrigans journal add --type "$1" --agent "$2" --tool daily >/dev/null 2>&1 || true; }

if [ -f "$WS/.env" ]; then
  set -a; . "$WS/.env" >/dev/null 2>&1; set +a
fi

# The agent command: the harness's `run` command (harness/harness.toml) filled with the assembled role and
# the instruction. Prints NUL-separated arguments, or a readable line with --show.
agent_command() {  # agent, instruction, [--show]
  local role
  role="$(korrigans agent "$1" --write)" || return 1
  python3 - "$CORE/scripts" "$role" "$2" "${3:-}" <<'PY'
import shlex, sys
sys.path.insert(0, sys.argv[1])
import common
role_file, instruction, show = sys.argv[2], sys.argv[3], sys.argv[4] == "--show"
daily = common.read_toml("rules/routing.toml").get("daily", {})
name = daily.get("harness", "claude")
harness = common.read_toml("harness/harness.toml").get(name) or sys.exit(f"unknown harness {name}")
role_text = open(role_file, encoding="utf-8").read()
run = harness["run"]
uses_role = any("{role_text}" in a or "{role_file}" in a for a in run)
prompt = instruction if uses_role else f"{role_text}\n---\n\n{instruction}"
if not any("{prompt}" in a for a in run):   # the harness reads its whole prompt from the role file
    role_file = role_file[:-3] + "-daily.md"
    role_text += f"\n---\n\n{instruction}\n"
    open(role_file, "w", encoding="utf-8").write(role_text)
model = daily.get("model") or harness.get("models", {}).get("standard", "")
values = {"prompt": prompt, "role_text": role_text, "role_file": role_file, "workspace": common.WS,
          "model": model, "effort": daily.get("effort") or "high"}
command = common.fill(run, values)
if show:
    shown = "<role>" if uses_role else f"<role> {instruction}"
    line = shlex.join(common.fill(run, values | {"role_text": "<role>", "prompt": instruction if uses_role else shown}))
    print(f"   [{name}] {line}")
else:
    sys.stdout.write("\0".join(command) + "\0")
PY
}

run_agent() {  # agent, instruction
  if [ "$DRY" = 1 ]; then agent_command "$1" "$2" --show; return; fi
  local cmd=() arg
  while IFS= read -r -d '' arg; do cmd+=("$arg"); done < <(agent_command "$1" "$2")
  [ "${#cmd[@]}" -gt 0 ] || { echo "   could not build the command for $1"; return 1; }
  command -v "${cmd[0]}" >/dev/null || { echo "   ${cmd[0]} not found"; return 1; }
  "${cmd[@]}" > "state/daily-$1-$DAY.log" 2>&1
}

INPUTS="reports/$DAY.md (frozen board)"
if has mail; then
  echo "Mail"
  step mail || echo "   mail extract failed, the Chronicle will say so"
  INPUTS="$INPUTS, mail/$DAY.md"
fi
if has todoist; then
  echo "Task manager"
  step todoist today || echo "   task manager unreachable, the Chronicle will say so"
  INPUTS="$INPUTS, state/todoist-$DAY.json"
fi
if has quota; then
  echo "Quota"
  if [ "$DRY" = 1 ]; then step usage alert
  else korrigans usage alert > state/usage-alert.txt 2>&1 || true; cat state/usage-alert.txt; fi
  INPUTS="$INPUTS, state/usage-alert.txt"
fi

echo "Frozen board"
step board --freeze || true
step board >/dev/null || true

if has mail; then
  echo "The Chamberlain"
  if run_agent chamberlain "Follow the skill sort-mail for $DAY. The mail extract is done: read the newest file in state/mail/. Send nothing, delete nothing."; then
    log mail_sorted chamberlain
  else
    log run_failed chamberlain
  fi
fi

echo "The Seneschal"
if run_agent seneschal "Follow the skill morning-chronicle for $DAY. Ready: $INPUTS. Do not commit: the script does it."; then
  log morning_chronicle seneschal
else
  log run_failed seneschal
fi

[ "$DRY" = 1 ] && exit 0
echo "Commit"
if git -C "$WS" rev-parse --git-dir >/dev/null 2>&1; then
  paths=()
  for d in reports mail journal; do [ -e "$d" ] && paths+=("$d"); done
  if [ "${#paths[@]}" -gt 0 ]; then
    git add -- "${paths[@]}" 2>/dev/null
    if git diff --cached --quiet -- "${paths[@]}"; then
      echo "   nothing to commit"
    elif git commit -q -m "korrigans: Morning Chronicle of $DAY" -- "${paths[@]}"; then
      echo "   committed"
    else
      echo "   commit failed (see above): the files are staged"
    fi
  fi
fi
echo "Chronicle: $WS/reports/$DAY.md"
