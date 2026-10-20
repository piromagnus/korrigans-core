#!/usr/bin/env bash
# Install Korrigans: the core (shared, public) and your workspace (private, yours).
# Safe to run again: every step checks whether it is already done, and no existing file is overwritten.
#
#   bash install.sh                               core here (or cloned), workspace ~/korrigans
#   bash install.sh --workspace ~/notes/household
#   bash install.sh --language fr --modules quota,todoist
#   bash install.sh --dry-run                     show what would be done
#
# Options:
#   --workspace DIR   where your workspace lives (default ~/korrigans)
#   --core DIR        where the core lives (default: this checkout, else ~/.local/share/korrigans-core)
#   --repo URL        core repository to clone when this script is not run from a checkout
#   --language CODE   language your agents use with you (default en; the Vigil can change it)
#   --modules LIST    comma-separated optional modules: quota, todoist, mail, research
#   --no-git          do not create a git repository for the workspace
#   --dry-run         print the steps without doing them
set -euo pipefail

REPO="${KORRIGANS_REPO:-https://github.com/piromagnus/korrigans-core.git}"
WS="$HOME/korrigans"
CORE=""
LANGUAGE=""
MODULES=""
GIT=1
DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) WS="$2"; shift ;;
    --core) CORE="$2"; shift ;;
    --repo) REPO="$2"; shift ;;
    --language) LANGUAGE="$2"; shift ;;
    --modules) MODULES="$2"; shift ;;
    --no-git) GIT=0 ;;
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1 (see --help)"; exit 2 ;;
  esac
  shift
done

ok()   { printf '  \033[32mok\033[0m  %s\n' "$*"; }
todo() { printf '  \033[33m..\033[0m  %s\n' "$*"; }
run()  { if [ "$DRY" = 1 ]; then printf '  would run: %s\n' "$*"; else "$@"; fi; }
expand() { case "$1" in "~"*) printf '%s\n' "$HOME${1#\~}" ;; *) printf '%s\n' "$1" ;; esac; }
WS="$(expand "$WS")"

echo "1. Requirements"
command -v git >/dev/null || { echo "  git is required"; exit 1; }
command -v python3 >/dev/null || { echo "  python3 (3.10 or later) is required"; exit 1; }
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' \
  || { echo "  python3 is $(python3 -V 2>&1 | cut -d' ' -f2); 3.10 or later is required"; exit 1; }
ok "git $(git --version | cut -d' ' -f3), python $(python3 -V 2>&1 | cut -d' ' -f2)"

echo "2. Core"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -z "$CORE" ]; then
  if [ -f "$HERE/scripts/common.py" ]; then CORE="$HERE"; else CORE="$HOME/.local/share/korrigans-core"; fi
fi
CORE="$(expand "$CORE")"
if [ -f "$CORE/scripts/common.py" ]; then
  ok "core at $CORE"
else
  run git clone --depth 1 "$REPO" "$CORE"
  ok "core cloned from $REPO into $CORE"
fi

echo "3. Workspace"
if [ -f "$WS/korrigans.toml" ]; then
  ok "workspace already at $WS: existing files are kept"
else
  run mkdir -p "$WS"
  ok "workspace created at $WS"
fi
copied=0
if [ "$DRY" = 0 ]; then
  while IFS= read -r -d '' f; do
    rel="${f#"$CORE/templates/workspace/"}"
    if [ ! -e "$WS/$rel" ]; then
      mkdir -p "$(dirname "$WS/$rel")"
      cp "$f" "$WS/$rel"
      copied=$((copied + 1))
    fi
  done < <(find "$CORE/templates/workspace" -type f -print0)
  for d in tasks ideas questions projects people reports mail journal skills agents memory/agents resources/examples extensions/drafts extensions/proposed; do
    mkdir -p "$WS/$d"
  done
  [ -e "$WS/BOOTSTRAP.md" ] || [ -e "$WS/memory/vigil.md" ] || { cp "$CORE/BOOTSTRAP.md" "$WS/BOOTSTRAP.md"; copied=$((copied + 1)); }
  # Point the workspace at this core and apply the options, without touching anything else.
  python3 - "$WS/korrigans.toml" "$CORE" "$LANGUAGE" "$MODULES" <<'PY'
import re, sys
path, core, language, modules = sys.argv[1:]
text = open(path, encoding="utf-8").read()
text = re.sub(r'(?m)^core = "[^"]*"', f'core = "{core}"', text, count=1)
if language:
    text = re.sub(r'(?m)^language = "[^"]*"', f'language = "{language}"', text, count=1)
if modules:
    items = ", ".join(f'"{m.strip()}"' for m in modules.split(",") if m.strip())
    text = re.sub(r'(?m)^modules = \[[^\]]*\]', f"modules = [{items}]", text, count=1)
open(path, "w", encoding="utf-8").write(text)
PY
fi
ok "$copied file(s) added from the workspace template"

echo "4. Looking around (written as 'detected, to confirm' for the Vigil)"
DETECTED="$WS/memory/global/detected.md"
if [ -e "$DETECTED" ]; then
  ok "memory/global/detected.md already exists: kept"
elif [ "$DRY" = 0 ]; then
  mkdir -p "$(dirname "$DETECTED")"
  set +e +o pipefail   # detection is best effort: a failed probe must not stop the install
  {
    echo "---"
    echo "summary: \"What install.sh found on this machine on $(date +%F). Each line is a guess until the user confirms it during the Vigil.\""
    echo "---"
    echo "# Detected at install, to confirm"
    echo
    echo "<!-- vigil: tools -->"
    echo
    echo "## Harnesses"
    for h in claude codex pi hermes cursor-agent vibe; do
      if command -v "$h" >/dev/null 2>&1; then echo "- $h: found"; else echo "- $h: not found"; fi
    done
    echo
    echo "## You"
    n="$(git config --global user.name 2>/dev/null || true)"
    [ -n "$n" ] && echo "- git user name: $n"
    echo
    echo "## Git repositories (up to 30, depth 3 under your home)"
    find "$HOME" -maxdepth 4 -type d -name .git -not -path "$WS/*" -not -path "$CORE/*" \
      -not -path "$HOME/.*/*" 2>/dev/null | head -30 | sed "s|/.git\$||; s|^$HOME|- ~|"
    echo
    echo "## Possible data folders"
    find "$HOME" -maxdepth 2 -type d \( -iname data -o -iname datasets -o -iname donnees \) \
      -not -path "$HOME/.*" 2>/dev/null | head -10 | sed "s|^$HOME|- ~|"
    echo
    echo "## Notes and mail"
    find "$HOME" -maxdepth 3 -type d -name .obsidian -not -path "$HOME/.*/*" 2>/dev/null | head -5 \
      | sed "s|/.obsidian\$||; s|^$HOME|- Obsidian vault: ~|"
    ls -d "$HOME"/.thunderbird/*/ >/dev/null 2>&1 && echo "- Thunderbird profile found: the mail module can sort it (read only)"
    command -v qmd >/dev/null 2>&1 && echo "- qmd found: the research module can index your notes"
    command -v tmux >/dev/null 2>&1 && echo "- tmux found: korrigans launch keeps sessions alive" || echo "- tmux not found: korrigans launch needs it"
    [ -e "$WS/.env" ] && echo "- $WS/.env exists (not read)"
    true
  } > "$DETECTED"
  set -e -o pipefail
  ok "memory/global/detected.md"
fi
FIRST=""
for h in claude codex pi hermes; do command -v "$h" >/dev/null 2>&1 && { FIRST="$h"; break; }; done
if [ -n "$FIRST" ] && [ "$FIRST" != claude ] && [ ! -e "$WS/rules/routing.toml" ] && [ "$DRY" = 0 ]; then
  printf '# Written by install.sh: %s is the first harness found here. Overrides the core rules/routing.toml.\n[sessions]\nseneschal = "%s"\ncommander = "%s"\n' \
    "$FIRST" "$FIRST" "$FIRST" > "$WS/rules/routing.toml"
  ok "sessions will open in $FIRST (rules/routing.toml)"
fi
[ -z "$FIRST" ] && todo "no harness found: install Claude Code, Codex, pi or Hermes, then run korrigans generate"

echo "5. Command line"
BIN="$HOME/.local/bin/korrigans"
if [ -e "$BIN" ] && ! grep -q "Korrigans command line" "$BIN" 2>/dev/null; then
  todo "$BIN exists and is not ours: left alone; use $CORE/bin/korrigans"
elif [ "$DRY" = 0 ]; then
  mkdir -p "$(dirname "$BIN")"
  cat > "$BIN" <<SH
#!/usr/bin/env bash
# Korrigans command line, written by install.sh. Default workspace below; inside another workspace, that one wins.
export KORRIGANS_CORE="\${KORRIGANS_CORE:-$CORE}"
export KORRIGANS_DEFAULT_WORKSPACE="\${KORRIGANS_DEFAULT_WORKSPACE:-$WS}"
exec python3 "\$KORRIGANS_CORE/scripts/cli.py" "\$@"
SH
  chmod +x "$BIN"
  ok "korrigans -> $BIN"
  case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) todo "add ~/.local/bin to your PATH" ;; esac
fi

echo "6. Harness files"
if [ "$DRY" = 0 ]; then
  KORRIGANS_CORE="$CORE" KORRIGANS_WORKSPACE="$WS" python3 "$CORE/scripts/cli.py" generate >/dev/null \
    && ok "AGENTS.md and adapters generated (korrigans generate)" \
    || todo "korrigans generate failed: run it by hand to see why"
else
  echo "  would run: korrigans generate"
fi

echo "7. Workspace history"
if [ "$GIT" = 0 ]; then
  todo "no git repository (--no-git)"
elif git -C "$WS" rev-parse --git-dir >/dev/null 2>&1; then
  top="$(git -C "$WS" rev-parse --show-toplevel)"
  if [ "$top" = "$(cd "$WS" && pwd -P)" ]; then ok "git repository already there"; else ok "inside the existing repository $top: nothing to create"; fi
elif [ "$DRY" = 0 ]; then
  git -C "$WS" init -q
  git -C "$WS" add -A
  git -C "$WS" -c user.name="${GIT_AUTHOR_NAME:-$(git config --global user.name || echo Korrigans)}" \
      -c user.email="${GIT_AUTHOR_EMAIL:-$(git config --global user.email || echo korrigans@localhost)}" \
      commit -q -m "Korrigans: the household is founded" && ok "git repository created, first commit"
fi

echo
echo "Done. Next:"
echo "  cd $WS"
echo "  ${FIRST:-claude}            then say: start the vigil"
echo "  korrigans context  shows how much of the household's context is settled"
