#!/usr/bin/env bash
# Index the workspace and the library with qmd (local full-text search), if qmd is installed.
#   korrigans index              declare the collections (once), then update the index
# The library is korrigans.toml [research] library (default: library/ in the workspace).
# Semantic search downloads models (about 2 GB): run `qmd embed` yourself if you want it, then `qmd query`.
set -uo pipefail
CORE="${KORRIGANS_CORE:-$(cd "$(dirname "$0")/../../.." && pwd)}"
if ! command -v qmd >/dev/null; then
  echo "qmd is not installed (https://github.com/tobi/qmd): nothing indexed. Agents fall back to grep."
  exit 0
fi
{ IFS= read -r WS; IFS= read -r LIBRARY; } < <(python3 - "$CORE/scripts" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import common
library = Path(common.config().get("research", {}).get("library") or "library").expanduser()
print(common.WS)
print(library if library.is_absolute() else common.WS / library)
PY
)
qmd collection add "$WS" --name workspace --mask "**/*.md" 2>/dev/null || echo "collection workspace already declared"
if [ -d "$LIBRARY" ]; then
  qmd collection add "$LIBRARY" --name library --mask "**/*.md" 2>/dev/null || echo "collection library already declared"
else
  echo "no library at $LIBRARY (korrigans.toml [research] library): only the workspace is indexed"
fi
qmd update
echo "Full-text index ready: try qmd search \"<terms>\" -c library."
