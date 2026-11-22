#!/bin/sh
# AHA-0031 R4: isolation - the real workspace stays untouched.
#
# Two arms, each a scripted row:
#
# 1. The load-bearing arm: with a sandboxed HOME and AHABASE_WORKSPACE
#    unset, a writing probe through the package's own API (config
#    resolution + the on-demand data directory) lands under
#    $HOME/ahabase - witnessing that a forgotten pin targets the
#    real-workspace path, so the entrypoint pin is load-bearing, not
#    cosmetic.
#
# 2. The held-seam arm: with the env pinned to the live playground
#    (bootstrapped at ~/ahabase-playground when absent) and the REAL
#    HOME, a full story cycle runs - and the real development workspace
#    ~/ahabase gains nothing: the _data/ and _config/ trees are
#    snapshot-diffed around the pass and must be unchanged, and the
#    probe resolves the playground root, not ~/ahabase.

set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BOOTSTRAP="$(CDPATH= cd -- "$HERE/.." && pwd)/bootstrap.sh"
SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-pg-r4.XXXXXX")"
SANDBOX="$(CDPATH= cd -- "$SANDBOX" && pwd)"  # canonical: TMPDIR may end in /
trap 'rm -rf "$SANDBOX"' EXIT

fail() { echo "R4 RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

# --- arm 1: the load-bearing arm (a forgotten pin targets the real path) --------
note "arm 1: sandboxed HOME, unset env, a writing probe"
ARM1="$SANDBOX/arm1"
sh "$BOOTSTRAP" "$ARM1/workspace" >/dev/null || fail "the bootstrap did not run green"
mkdir -p "$ARM1/home"
(
    export HOME="$ARM1/home"
    unset AHABASE_WORKSPACE AHABASE_CONFIG AHABASE_HOME
    RESOLVED="$("$ARM1/workspace/.venv/bin/python" -c '
from ahabase.config import get_workspace_dir
print(get_workspace_dir())')"
    [ "$RESOLVED" = "$HOME/ahabase" ] \
        || { echo "arm 1: get_workspace_dir() resolved to '$RESOLVED', not \$HOME/ahabase" >&2; exit 1; }
    "$ARM1/workspace/.venv/bin/python" -c '
from ahabase.config import get_data_dir
get_data_dir(epic="FORGOTTEN")' || { echo "arm 1: the writing probe refused" >&2; exit 1; }
    [ -d "$HOME/ahabase/_data/FORGOTTEN" ] \
        || { echo "arm 1: the would-be write did not land under \$HOME/ahabase/_data" >&2; exit 1; }
) || fail "the load-bearing arm failed (see the probe output above)"

# --- arm 2: the held seam (the real workspace gains nothing) ----------------------
note "arm 2: the live playground, the real HOME, the real workspace unchanged"
PLAYGROUND="$HOME/ahabase-playground"
if [ ! -d "$PLAYGROUND/.venv" ]; then
    sh "$BOOTSTRAP" "$PLAYGROUND" >/dev/null || fail "the live playground did not bootstrap"
fi
. "$PLAYGROUND/ahabase.env"
[ "$AHABASE_WORKSPACE" = "$PLAYGROUND" ] || fail "the entrypoint does not pin the playground"
RESOLVED="$("$PLAYGROUND/.venv/bin/python" -c 'from ahabase.config import get_workspace_dir; print(get_workspace_dir())')"
[ "$RESOLVED" = "$PLAYGROUND" ] \
    || fail "under the pin, get_workspace_dir() resolved to '$RESOLVED', not the playground"

REAL="$HOME/ahabase"
snapshot() {  # every entry under the real workspace's derived trees - files
    # AND directories: a write that creates a directory but no file yet must
    # leave its trace too (the checkpoint-1 fold)
    find "$REAL/_data" "$REAL/_config" 2>/dev/null | LC_ALL=C sort
}
snapshot > "$SANDBOX/real-before.txt"

# a full story cycle in the playground's scratch repo, the consumer's acts
AHABASE="$PLAYGROUND/.venv/bin/ahabase"
REPO="$PLAYGROUND/repos/scratch"
(
    cd "$REPO"
    [ -d _grid4d ] || "$AHABASE" init SCRATCH --root . || exit 1
    git rev-parse --verify HEAD >/dev/null 2>&1 \
        || git commit -q --allow-empty -m "chore: first touch" || exit 1
    if [ -n "$(git status --porcelain)" ]; then
        git add -A && git commit -q -m "chore: the scratch Epic" || exit 1
    fi
) || fail "the playground scratch Epic did not register"
CYCLE="$(
    cd "$REPO"
    NEXT="$("$AHABASE" story create "isolation witness" --root . 2>&1 | sed -n 's/^story: \(SCRATCH-[0-9]*\) minted.*/\1/p')"
    [ -n "$NEXT" ] || { echo "no story minted" >&2; exit 1; }
    perl -pi -e "s/\\{GOAL\\}/the isolation witness/" "_worktrees/$NEXT/_grid4d/story/$NEXT.md"
    git -C "_worktrees/$NEXT" add -A
    git -C "_worktrees/$NEXT" commit -q -m "$NEXT(docs): the one edit"
    "$AHABASE" story complete "$NEXT" --root .
)" || fail "the held-seam story cycle failed"

snapshot > "$SANDBOX/real-after.txt"
if ! diff -u "$SANDBOX/real-before.txt" "$SANDBOX/real-after.txt"; then
    fail "the real workspace ~/ahabase changed during the held-seam pass (see the diff above)"
fi
note "the real workspace's _data/ and _config/: unchanged"

note "R4 GREEN: the pin is load-bearing, and the held seam leaves the real workspace untouched"
