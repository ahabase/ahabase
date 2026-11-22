#!/bin/sh
# AHA-0031 R1: the workspace bootstrap, versioned as an artifact.
#
# Bootstraps a throwaway workspace (mktemp) and asserts the produced net,
# each part witnessed: the CLAUDE.md declaring ahabase the primary tool,
# the venv serving ahabase from the built wheel (a pip show witness - the
# leg's pattern), the named entrypoint exporting AHABASE_WORKSPACE pinned
# to the workspace root (with the resolution probe: get_workspace_dir()
# returns the root under that environment), the .claude/settings.json
# allowlisting the wheel-installed binary, the seeded-memory absence (the
# seat's memory starts empty by design), the scenarios document, and the
# two R2 fixtures minted as plain git repositories.

set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BOOTSTRAP="$(CDPATH= cd -- "$HERE/.." && pwd)/bootstrap.sh"
WS="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-pg-r1.XXXXXX")/workspace"
trap 'rm -rf "$(dirname -- "$WS")"' EXIT

fail() { echo "R1 RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

note "bootstrap into $WS"
sh "$BOOTSTRAP" "$WS" >/dev/null || fail "the bootstrap did not run green"
WS="$(CDPATH= cd -- "$WS" && pwd)"  # canonical, as the bootstrap pinned it

# --- the CLAUDE.md ----------------------------------------------------------
[ -s "$WS/CLAUDE.md" ] || fail "no workspace CLAUDE.md"
grep -q "ahabase CLI is the primary tool" "$WS/CLAUDE.md" \
    || fail "the CLAUDE.md does not declare ahabase the primary tool"
grep -q "source ahabase.env" "$WS/CLAUDE.md" \
    || fail "the CLAUDE.md does not teach the entrypoint pin"

# --- the wheel-served venv ---------------------------------------------------
[ -x "$WS/.venv/bin/ahabase" ] || fail "no ahabase console script in the venv"
"$WS/.venv/bin/pip" show ahabase | grep -q '^Name: ahabase$' \
    || fail "pip show does not witness the ahabase distribution"
case "$("$WS/.venv/bin/pip" show ahabase | sed -n 's/^Location: //p')" in
    "$WS/.venv/"*) : ;;
    *) fail "the distribution does not live in the workspace venv" ;;
esac
"$WS/.venv/bin/ahabase" --version >/dev/null || fail "ahabase --version refused"

# --- the entrypoint and the resolution probe ---------------------------------
[ -f "$WS/ahabase.env" ] || fail "no entrypoint (ahabase.env)"
grep -q "export AHABASE_WORKSPACE=" "$WS/ahabase.env" \
    || fail "the entrypoint does not export AHABASE_WORKSPACE"
. "$WS/ahabase.env"
[ "$AHABASE_WORKSPACE" = "$WS" ] || fail "the entrypoint does not pin this workspace"
PROBE="$("$WS/.venv/bin/python" -c 'from ahabase.config import get_workspace_dir; print(get_workspace_dir())')"
[ "$PROBE" = "$WS" ] \
    || fail "get_workspace_dir() resolved to '$PROBE', not the workspace root - the seam probe failed"

# --- the permissions allowlist ------------------------------------------------
[ -f "$WS/.claude/settings.json" ] || fail "no .claude/settings.json"
"$WS/.venv/bin/python" -c 'import json,sys; json.load(open(sys.argv[1]))' "$WS/.claude/settings.json" \
    || fail "the settings file is not valid JSON"
grep -q "Bash($WS/.venv/bin/ahabase:\*)" "$WS/.claude/settings.json" \
    || fail "the allowlist does not carry the wheel-installed ahabase binary"

# --- the memory starts empty by design ----------------------------------------
SLUG="$(printf '%s' "$WS" | sed 's|^/|-|; s|/|-|g')"
MEMDIR="$HOME/.claude/projects/$SLUG/memory"
if [ -d "$MEMDIR" ] && [ -n "$(ls -A "$MEMDIR")" ]; then
    fail "the bootstrap seeded memory at $MEMDIR - the seat's memory starts empty by design"
fi

# --- the scenarios document and the R2 fixtures --------------------------------
[ -s "$WS/scenarios.md" ] || fail "no scenarios document in the workspace"

# --- the seven standard folders (AHA-0035) ---------------------------------------
# the census, both polarities: all seven at the workspace root (the
# bootstrap's 'workspace ensure' act), none inside either fixture repo
for FOLDER in _config _data _generated _inbox _temp _wikis _worktrees; do
    [ -d "$WS/$FOLDER" ] || fail "no $FOLDER at the workspace root"
done
for REPO in scratch messy; do
    for FOLDER in _config _data _generated _inbox _temp _wikis _worktrees; do
        [ ! -e "$WS/repos/$REPO/$FOLDER" ] \
            || fail "$FOLDER landed inside the $REPO repository"
    done
done
# a deleted folder reappears on the next ensure (idempotent census act)
rmdir "$WS/_temp"
AHABASE_WORKSPACE="$WS" "$WS/.venv/bin/ahabase" workspace ensure >/dev/null \
    || fail "workspace ensure refused on re-run"
[ -d "$WS/_temp" ] || fail "the deleted _temp did not reappear on re-ensure"

[ -d "$WS/repos/scratch/.git" ] || fail "no scratch repo"
git -C "$WS/repos/scratch" rev-parse --verify HEAD >/dev/null 2>&1 \
    && fail "the scratch repo is not empty (HEAD resolves)"
[ -d "$WS/repos/messy/.git" ] || fail "no messy repo"
[ "$(git -C "$WS/repos/messy" branch --show-current)" = "trunk" ] \
    || fail "the messy repo is not on its own default branch trunk"
[ "$(git -C "$WS/repos/messy" tag -l)" = "v0.1" ] \
    || fail "the messy repo's pre-existing tag is not exactly v0.1"
[ -f "$WS/repos/messy/.github/workflows/ci.yml" ] || fail "the messy repo carries no CI file"
[ -f "$WS/repos/messy/src/lib.py" ] || fail "the messy repo carries no code"

# --- the bootstrap is fail-closed on an existing workspace ---------------------
if sh "$BOOTSTRAP" "$WS" >/dev/null 2>&1; then
    fail "the bootstrap touched an existing workspace - it must refuse"
fi

note "R1 GREEN: the bootstrap produces the witnessed net"
