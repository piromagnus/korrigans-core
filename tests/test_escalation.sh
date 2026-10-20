#!/usr/bin/env bash
# Escalation test with fake harnesses (tests/fake-harness): no model is called and nothing is written
# outside a throwaway folder. Prints PASS or FAIL per scenario; exits non-zero if one fails.
#
#   bash tests/test_escalation.sh            (PYTHON=python3.10 to pick an interpreter, KEEP=1 to keep the folder)
set -u
CORE="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python3}"
TMP="$(mktemp -d)"
if [ -z "${KEEP:-}" ]; then trap 'rm -rf "$TMP"' EXIT; else echo "temp folder: $TMP"; fi
WS="$TMP/workspace"; WORK="$TMP/work"; LOG="$TMP/log"
export KORRIGANS_WORKSPACE="$WS" KORRIGANS_CORE="$CORE" PATH="$CORE/tests/fake-harness:$PATH"
unset FAKE_SCENARIO

k() { "$PY" "$CORE/scripts/cli.py" "$@"; }
field() { "$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); from task import write_field; write_field(*sys.argv[2:])' \
          "$CORE/scripts" "$C" "$1" "$2"; }
get() { "$PY" -c 'import sys; sys.path.insert(0, sys.argv[1]); from task import read_field; print(read_field(*sys.argv[2:]))' \
        "$CORE/scripts" "$C" "$1"; }
journal_has() { grep -h "\"type\": \"$1\"" "$WS"/journal/*.jsonl 2>/dev/null | grep -q "\"task\": \"$ID\""; }
count() { local n; n=$(grep -c "$1" "$2" 2>/dev/null); echo "${n:-0}"; }

FAILED=0
check() {  # check <name> <condition...>
  local name=$1; shift
  if "$@"; then echo "PASS $name"; else echo "FAIL $name"; FAILED=1; sed 's/^/    /' "$LOG" | tail -15; fi
}

# A minimal workspace ------------------------------------------------------------------------------------
mkdir -p "$WS/projects/demo" "$WS/rules" "$WORK"
cat > "$WS/korrigans.toml" <<EOF
[korrigans]
core = "$CORE"
language = "en"
modules = []
link_root = "."
EOF
cat > "$WS/projects/demo/project.md" <<'EOF'
---
type: project
title: Demo
summary: "A demo project for the tests."
status: active
intensity: focus
---
# Demo
EOF
# The Watch checks every 1.2 seconds instead of every 5 minutes.
cat > "$WS/rules/escalation.toml" <<'EOF'
[watch]
every_minutes = 0.02
EOF
# Agents and the default personality, only if neither the core nor a module has them yet.
for agent in constable watch korrigans/code; do
  if ! k which "agents/$agent/IDENTITY.md" >/dev/null; then
    mkdir -p "$WS/agents/$agent"
    printf -- '---\nname: %s\ntype: agent\ndescription: "Test stand-in."\nmode: call\n---\n' "${agent//\//-}" \
      > "$WS/agents/$agent/IDENTITY.md"
    printf -- '---\nsummary: "Test stand-in."\n---\n# Role: %s\n\nTest stand-in.\n' "$agent" > "$WS/agents/$agent/AGENTS.md"
  fi
done
if ! k which personalities/balanced.md >/dev/null; then
  mkdir -p "$WS/personalities"
  printf -- '---\nsummary: "Test stand-in."\nrisk: medium\n---\nBalanced.\n' > "$WS/personalities/balanced.md"
fi

new_task() {  # new_task <title> <difficulty> [verify command]
  rm -f "$WORK"/done-*
  k task new "$1" --project demo --type code >/dev/null || { echo "korrigans task new failed"; exit 1; }
  C="$(ls -d "$WS"/tasks/T-*/ "$WS"/tasks/*/T-*/ 2>/dev/null | tail -1)charter.md"
  ID="$(basename "$(dirname "$C")" | cut -c1-6)"
  field workdir "$WORK"
  field personality balanced
  [ -n "$2" ] && field difficulty "$2"
  [ -n "${3:-}" ] && field verify "\"$3\""
  return 0
}
attempts() { count '^### ' "$(dirname "$C")/attempts.md"; }

# 0. The Constable classifies a charter that has no difficulty -------------------------------------------
new_task "Export button" ""
k ladder classify "$ID" --write > "$LOG" 2>&1
check "constable classifies (easy, written)" \
  [ "$(get difficulty)" = easy -a "$(count 'the Constable' "$LOG")" = 1 ]

# 1. Fail at page, succeed at squire ---------------------------------------------------------------------
new_task "Loader rework" easy
FAKE_SCENARIO=fail k run "$ID" > "$LOG" 2>&1; rc=$?
ok1() {
  [ $rc = 0 -a "$(attempts)" = 1 -a "$(get assigned_to)" = "korrigans/code@codex:squire" \
    -a "$(count '^## Previous attempts' "$(dirname "$C")/prompt.md")" -ge 1 -a -e "$WORK/done-gpt-6-luna-high" ] \
  && journal_has escalation && journal_has escalation_succeeded
}
check "1. fail then succeed" ok1

# 2. The Watch sees a loop and escalates -----------------------------------------------------------------
new_task "Loop" medium
FAKE_SCENARIO=loop k run "$ID" > "$LOG" 2>&1; rc=$?
ok2() {
  [ $rc = 0 -a "$(attempts)" = 1 -a "$(count ': escalate$' "$(dirname "$C")/attempts.md")" = 1 \
    -a "$(get assigned_to)" = "korrigans/code@codex:banneret" -a -e "$WORK/done-gpt-6.1-sol-high" ] \
  && journal_has watch_stop && journal_has escalation_succeeded
}
check "2. watch escalates on a loop" ok2

# 3. The verify command fails until knight (mid:medium): the task is reclassified medium ------------------
new_task "Evidence" easy "ls done-gpt-6.1-sol-medium"
FAKE_SCENARIO=default k run "$ID" > "$LOG" 2>&1; rc=$?
ok3() {
  [ $rc = 0 -a "$(attempts)" = 2 -a "$(get difficulty)" = medium -a "$(get assigned_to)" = "korrigans/code@codex:knight" ] \
  && journal_has difficulty_revised
}
check "3. verify climbs to mid, task reclassified" ok3

# 4. The Watch stops a korrigan that leaves its access ---------------------------------------------------
new_task "Out of bounds" hard
FAKE_SCENARIO=stop k run "$ID" > "$LOG" 2>&1; rc=$?
check "4. watch stops" \
  [ $rc != 0 -a "$(get status)" = waiting-on-you -a "$(get waiting_on)" = review \
    -a "$(count ': stop$' "$(dirname "$C")/attempts.md")" = 1 ]

# 5. Forced rank, dry run: nothing runs ------------------------------------------------------------------
new_task "Forced" ""
k run "$ID" --rank champion --dry-run > "$LOG" 2>&1; rc=$?
k run "$ID" --rank mid:high --dry-run >> "$LOG" 2>&1; rc2=$?
check "5. forced rank dry run" \
  [ $rc = 0 -a $rc2 = 0 -a "$(count 'champion (large:xhigh)' "$LOG")" -ge 1 \
    -a "$(count 'claude -p <prompt> .*--model opus --effort xhigh' "$LOG")" = 1 \
    -a "$(count 'codex exec --full-auto -m gpt-6.1-sol -c model_reasoning_effort=high <prompt>' "$LOG")" = 1 \
    -a ! -e "$(dirname "$C")/attempts.md" -a -z "$(get assigned_to)" ]

# 6. Every rank fails: the ladder is exhausted and the task waits on the user ----------------------------
new_task "Impossible" easy "false"
FAKE_SCENARIO=default k run "$ID" > "$LOG" 2>&1; rc=$?
check "6. exhausted ladder -> waiting-on-you" \
  [ $rc != 0 -a "$(attempts)" = 4 -a "$(get status)" = waiting-on-you -a "$(get waiting_on)" = review ]

# The watchtower followed the runs -----------------------------------------------------------------------
k track > "$LOG" 2>&1
check "watchtower" [ "$(count '^T-0' "$LOG")" = 5 -a -e "$WS/Watchtower.md" ]

exit $FAILED
