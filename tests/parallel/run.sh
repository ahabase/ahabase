#!/bin/sh
# One row per story requirement (AHA-0032-tests): resolve the worktree's
# own venv and run the named test; fail closed with a named reason when
# the substrate is missing.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/../.." && pwd)
PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
    echo "run.sh: no venv python at $PY - create it (python3 -m venv .venv && .venv/bin/pip install -e '.[test]') and retry" >&2
    exit 1
fi
exec "$PY" -m pytest "$ROOT/tests/test_story_parallel.py" -k "$1" -q
