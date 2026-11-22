#!/bin/sh
# AHA-0031 R2: the plug-and-play seam - an existing repository becomes an Epic.
#
# Bootstraps a throwaway workspace, then the consumer's own acts with the
# ahabase CLI alone: the scratch repo (empty git - no commits, no files)
# and the messy repo (non-empty, own default branch trunk, pre-existing
# v0.1 tag, CI file) each register through init and validate green. The
# messy repo's story lands on its declared branch, measured three ways
# (the merge commit on trunk, the tag resolving to the story branch tip,
# main absent), the pre-existing tag untouched. The red arm: a control
# def file without **Branch:** lands its story on main - the branch check
# can fail, so passing it means something.

set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BOOTSTRAP="$(CDPATH= cd -- "$HERE/.." && pwd)/bootstrap.sh"
SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-pg-r2.XXXXXX")"
trap 'rm -rf "$SANDBOX"' EXIT
WS="$SANDBOX/workspace"

fail() { echo "R2 RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

note "bootstrap"
sh "$BOOTSTRAP" "$WS" >/dev/null || fail "the bootstrap did not run green"
. "$WS/ahabase.env"
AHABASE="$WS/.venv/bin/ahabase"
GITUSER='-c user.name=Consumer -c user.email=consumer@playground.test'

# --- the scratch repo: init from its empty state (no commits, no files) -------
cd "$WS/repos/scratch"
git rev-parse --verify HEAD >/dev/null 2>&1 \
    && fail "the scratch fixture is not empty (HEAD resolves)"
"$AHABASE" init SCRATCH --root . || fail "init refused the empty scratch repo"
"$AHABASE" validate --root . >/dev/null || fail "validate refused the scratch repo"
git $GITUSER commit -q --allow-empty -m "chore: first touch" \
    || fail "the empty scratch repo refuses a first commit (fixture broken)"

# --- the messy repo: init as a non-empty repository ----------------------------
cd "$WS/repos/messy"
"$AHABASE" init MESSY --root . || fail "init refused the non-empty messy repo"
"$AHABASE" validate --root . >/dev/null || fail "validate refused the messy repo"

# the declarations this repo owns: the branch and the code artifacts
perl -pi -e 's/^\*\*StoryPrefix:.*$/$&\n**Branch:** trunk\n**CodeArtifacts:** src/; s/\{OVERVIEW\}/a messy consumer repository/' \
    _grid4d/story/MESSY.md
git add -A && git $GITUSER commit -q -m "chore: declare the branch and the code"
"$AHABASE" validate --root . >/dev/null || fail "validate refused the declarations"

note "story create on the declared branch"
V01_BEFORE="$(git rev-parse v0.1)"
MAIN_ABSENT=0
git rev-parse --verify --quiet main >/dev/null || MAIN_ABSENT=1
[ "$MAIN_ABSENT" = 1 ] || fail "the messy fixture unexpectedly carries a main branch"

"$AHABASE" story create "carry code on the declared branch" --root . \
    || fail "story create refused the messy repo"
WORKTREE="$WS/repos/messy/_worktrees/MESSY-0001"
[ -d "$WORKTREE" ] || fail "no minted worktree"
perl -pi -e 's/\{GOAL\}/carry the code on the declared branch/' "$WORKTREE/_grid4d/story/MESSY-0001.md"
git -C "$WORKTREE" add -A
git -C "$WORKTREE" $GITUSER commit -q -m "MESSY-0001(docs): the one edit"

note "story complete: the landing on trunk"
[ "$(git branch --show-current)" = "trunk" ] || fail "the root left trunk mid-scenario"
"$AHABASE" story complete MESSY-0001 --root . || fail "story complete refused"

# witness 1: the story's own merge commit sits on trunk
MERGE="$(git log --merges -1 --grep='^merge MESSY-0001 (story complete)$' --format=%H)"
[ -n "$MERGE" ] || fail "the story's merge commit is not findable"
git branch --contains "$MERGE" | grep -qx '\* trunk' \
    || fail "the merge commit is not on the declared branch trunk"
# witness 2: the story tag resolves to the story branch head the merge carried
[ "$(git rev-parse "vMESSY-0001")" = "$(git rev-parse "$MERGE^2")" ] \
    || fail "the tag vMESSY-0001 does not resolve to the story branch head the merge carried"
# witness 3: main stays absent
git rev-parse --verify --quiet main >/dev/null \
    && fail "main appeared in the messy repo during the run"
# the tag edge: the pre-existing tag untouched, the story tag distinct
[ "$(git rev-parse v0.1)" = "$V01_BEFORE" ] || fail "the pre-existing v0.1 tag moved"
[ "$(git tag -l | sort)" = "$(printf 'v0.1\nvMESSY-0001')" ] \
    || fail "the tag set is not exactly {v0.1, vMESSY-0001}"

note "the red arm: no Branch declaration lands on main"
cd "$WS/repos/scratch"
perl -pi -e 's/\{OVERVIEW\}/a scratch consumer repository/' _grid4d/story/SCRATCH.md
git add -A && git $GITUSER commit -q -m "chore: shape the scratch Epic"
"$AHABASE" story create "no branch declared" --root . || fail "story create refused the scratch repo"
CTRL="$WS/repos/scratch/_worktrees/SCRATCH-0001"
perl -pi -e 's/\{GOAL\}/land on the default branch/' "$CTRL/_grid4d/story/SCRATCH-0001.md"
git -C "$CTRL" add -A && git -C "$CTRL" $GITUSER commit -q -m "SCRATCH-0001(docs): the one edit"
"$AHABASE" story complete SCRATCH-0001 --root . || fail "the control complete refused"
CTRL_MERGE="$(git log --merges -n1 --format=%H)"
git branch --contains "$CTRL_MERGE" | grep -qx '\* main' \
    || fail "the control story did not land on main - the red arm does not bite"

# --- the hermeticity control (F1, the checkpoint-1 fold) ------------------------
# The whole script re-runs itself under a hostile global git config
# (init.defaultBranch = master): the fixtures pin their defaults
# repo-locally, so a consumer machine's global default must not decide
# where stories land. The guard env stops the recursion; the inner run is
# the ordinary script, only the world under it differs.
if [ "${AHABASE_PG_FOREIGN:-0}" != 1 ]; then
    note "the hermeticity control: the seam under a hostile global git config"
    FOREIGN="$(mktemp "${TMPDIR:-/tmp}/ahabase-pg-r2-foreign.XXXXXX")"
    printf '[init]\n\tdefaultBranch = master\n' > "$FOREIGN"
    # the absolute path: this point sits deep inside the sandbox (cwd left
    # the invocation root), so a relative $0 would not resolve
    SELF="$HERE/$(basename -- "$0")"
    if ! GIT_CONFIG_GLOBAL="$FOREIGN" AHABASE_PG_FOREIGN=1 sh "$SELF" >/dev/null 2>&1; then
        rm -f "$FOREIGN"
        fail "the seam script is not hermetic against the machine's git config"
    fi
    rm -f "$FOREIGN"
fi

note "R2 GREEN: both repos are registered Epics; the landing is declared, witnessed, and falsifiable"
