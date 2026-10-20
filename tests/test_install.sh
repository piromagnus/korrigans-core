#!/usr/bin/env bash
# install.sh in a throwaway home: fresh install, second run changes nothing, the CLI works in the new workspace.
set -u
CORE="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
export HOME="$TMP/home" PATH="$CORE/tests/fake-harness:$TMP/home/.local/bin:/usr/bin:/bin"
mkdir -p "$HOME/code/demo-tool" && git -C "$HOME/code/demo-tool" init -q
fails=0
check() { if eval "$2" >/dev/null 2>&1; then echo "PASS: $1"; else echo "FAIL: $1"; fails=$((fails + 1)); fi; }

bash "$CORE/install.sh" --workspace "$HOME/korrigans" --language fr --modules quota > "$TMP/first.log" 2>&1
check "install exits cleanly" "grep -q '^Done' '$TMP/first.log'"
W="$HOME/korrigans"
check "workspace marked" "test -f '$W/korrigans.toml'"
check "core path written" "grep -q 'core = \"$CORE\"' '$W/korrigans.toml'"
check "language and modules applied" "grep -q 'language = \"fr\"' '$W/korrigans.toml' && grep -q 'modules = \[\"quota\"\]' '$W/korrigans.toml'"
check "bootstrap placed" "test -f '$W/BOOTSTRAP.md'"
check "detection written" "grep -q 'demo-tool' '$W/memory/global/detected.md'"
check "Rule generated" "test -s '$W/AGENTS.md'"
check "skills linked" "test -e '$W/.agents/skills/vigil/SKILL.md'"
check "git history" "git -C '$W' log --oneline | grep -q founded"
check "command line installed" "test -x '$HOME/.local/bin/korrigans'"
echo "# a user's edit" >> "$W/USER.md"
bash "$CORE/install.sh" --workspace "$HOME/korrigans" > "$TMP/second.log" 2>&1
check "second run keeps the user's edits" "grep -q \"a user's edit\" '$W/USER.md'"
check "second run adds no template file" "grep -q '0 file(s) added' '$TMP/second.log'"
cd /tmp
check "korrigans help from anywhere" "korrigans help | grep -q 'workspace: $W'"
check "korrigans context" "korrigans context | grep -q 'The Vigil'"
check "korrigans agent --list" "korrigans agent --list | grep -q seneschal"
check "korrigans check" "korrigans check"
check "registry consistent" "korrigans generate --check"
check "korrigans which" "korrigans which skills/vigil/SKILL.md | grep -q '$CORE'"
echo "$( [ $fails = 0 ] && echo PASS || echo FAIL ): install test ($fails failure(s))"
exit $((fails > 0))
