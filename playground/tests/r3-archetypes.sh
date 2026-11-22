#!/bin/sh
# AHA-0031 R3: the request archetypes through the consumer seat.
#
# Five archetypes end-to-end with the ahabase CLI alone, in a throwaway
# workspace's scratch repo (StoryHistoryKeep: 1): a docs-only story, a
# code-plus-tests story, a story sequence hitting the archive window
# (oldest set archived, newest stays), a real conflicted merge rehearsing
# complete's abort-and-recover path (no MERGE_HEAD, clean porcelain, the
# worktree and branch intact, the error naming the recovery, the re-run
# yielding exactly one merge commit and the one pre-merge tag), and the
# refusals - the guard paths (dirty main tree at create, root on another
# branch at complete, incomplete set at complete), each naming its reason
# and writing nothing (complete's own order mints the tag before the
# merge, so the refusal rows assert tag ABSENCE - they refuse before it).

set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BOOTSTRAP="$(CDPATH= cd -- "$HERE/.." && pwd)/bootstrap.sh"
SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-pg-r3.XXXXXX")"
trap 'rm -rf "$SANDBOX"' EXIT
WS="$SANDBOX/workspace"

fail() { echo "R3 RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

note "bootstrap + the scratch Epic (window declared: keep 1)"
sh "$BOOTSTRAP" "$WS" >/dev/null || fail "the bootstrap did not run green"
. "$WS/ahabase.env"
AHABASE="$WS/.venv/bin/ahabase"
REPO="$WS/repos/scratch"
WTS="$WS/_worktrees/scratch"  # the workspace-level worktree home (AHA-0035)
cd "$REPO"
git rev-parse --verify HEAD >/dev/null 2>&1 && fail "the scratch fixture is not empty"
"$AHABASE" init SCRATCH --root . || fail "init refused the empty scratch repo"
git commit -q --allow-empty -m "chore: first touch"
perl -pi -e 's/^\*\*StoryPrefix:.*$/$&\n**StoryHistoryKeep:** 1/; s/\{OVERVIEW\}/a scratch consumer Epic/' \
    _grid4d/story/SCRATCH.md
git add -A && git commit -q -m "chore: declare the history window"

cycle() {  # cycle NUMBER EDIT: create, one committed edit, status, complete
    NUMBER="$1"; EDIT="$2"
    note "cycle SCRATCH-$NUMBER"
    "$AHABASE" story create "story $NUMBER" --root . || fail "story create refused SCRATCH-$NUMBER"
    WT="$WTS/SCRATCH-$NUMBER"
    (
        cd "$WT"
        eval "$EDIT"
        git add -A && git commit -q -m "SCRATCH-$NUMBER(docs): the one edit"
    )
    [ -z "$(git -C "$WT" status --porcelain)" ] \
        || fail "the worktree SCRATCH-$NUMBER is dirty before complete"
    "$AHABASE" story status --root . | grep -q "active: SCRATCH-$NUMBER" \
        || fail "status does not name SCRATCH-$NUMBER active"
    MERGES_BEFORE="$(git log --merges --format=%H | wc -l | tr -d ' ')"
    "$AHABASE" story complete "SCRATCH-$NUMBER" --root . || fail "story complete refused SCRATCH-$NUMBER"
    MERGES_AFTER="$(git log --merges --format=%H | wc -l | tr -d ' ')"
    [ "$((MERGES_AFTER - MERGES_BEFORE))" = 1 ] \
        || fail "complete SCRATCH-$NUMBER did not add exactly one merge commit"
    git rev-parse "vSCRATCH-$NUMBER" >/dev/null || fail "no tag vSCRATCH-$NUMBER"
    [ -d "$WT" ] && fail "the worktree SCRATCH-$NUMBER survived completion"
    if git branch --list "feature/SCRATCH-$NUMBER*" | grep .; then
        fail "the branch SCRATCH-$NUMBER survived completion"
    fi
}

# --- archetype 1: a docs-only story ---------------------------------------------
cycle 0001 'perl -pi -e "s/\{GOAL\}/the docs-only goal/" _grid4d/story/SCRATCH-0001.md'

# --- archetype 2: a code-plus-tests story ----------------------------------------
cycle 0002 'mkdir -p src && printf "def tool():\n    return 42\n" > src/lib.py && printf "def test_tool():\n    assert tool() == 42\n" > test_lib.py && perl -pi -e "s/\{GOAL\}/the code goal/" _grid4d/story/SCRATCH-0002.md'

note "archetype 3 gate: two completions under keep 1 -> the oldest archived"
[ -f _grid4d/story/history/SCRATCH-0001.md ] \
    || fail "the oldest set SCRATCH-0001 did not move to story/history/"
[ -f _grid4d/story/SCRATCH-0002.md ] \
    || fail "the newest set SCRATCH-0002 did not stay in story/"
[ ! -f _grid4d/story/SCRATCH-0001.md ] \
    || fail "SCRATCH-0001 stayed reachable in story/ beyond the window"

# --- archetype 4: the conflicted merge --------------------------------------------
note "archetype 4: a real conflict - the same def-file line on both sides"
"$AHABASE" story create "the conflicted story" --root . || fail "story create refused the conflict story"
WT="$WTS/SCRATCH-0003"
perl -pi -e 's/\{GOAL\}/the conflicted goal/' "$WT/_grid4d/story/SCRATCH-0003.md"
perl -pi -e 's/a scratch consumer Epic/the story-side def edit/' "$WT/_grid4d/story/SCRATCH.md"
git -C "$WT" add -A && git -C "$WT" commit -q -m "SCRATCH-0003(docs): the story-side edits"
perl -pi -e 's/a scratch consumer Epic/the main-side def edit/' _grid4d/story/SCRATCH.md
git add -A && git commit -q -m "chore: the main-side def edit"

if "$AHABASE" story complete SCRATCH-0003 --root . >"$SANDBOX/conflict-out.txt" 2>&1; then
    fail "complete did not refuse the conflicted merge"
fi
grep -q "the merge was aborted" "$SANDBOX/conflict-out.txt" \
    || fail "the conflict error does not name the abort"
grep -q "resolve the conflict on main" "$SANDBOX/conflict-out.txt" \
    || fail "the conflict error does not name the recovery"
git rev-parse -q --verify MERGE_HEAD >/dev/null \
    && fail "a MERGE_HEAD survived the abort"
[ -z "$(git status --porcelain)" ] || fail "the root is not clean after the abort"
[ -d "$WT" ] || fail "the worktree did not survive the aborted merge"
git branch --list "feature/SCRATCH-0003*" | grep . >/dev/null \
    || fail "the story branch did not survive the aborted merge"

note "archetype 4: the recovery - resolve on main, re-run"
perl -pi -e 's/the main-side def edit/the story-side def edit/' _grid4d/story/SCRATCH.md
git add -A && git commit -q -m "chore: resolve the conflict on main"
MERGES_BEFORE="$(git log --merges --format=%H | wc -l | tr -d ' ')"
"$AHABASE" story complete SCRATCH-0003 --root . || fail "the re-run complete refused"
MERGES_AFTER="$(git log --merges --format=%H | wc -l | tr -d ' ')"
[ "$((MERGES_AFTER - MERGES_BEFORE))" = 1 ] \
    || fail "the re-run did not yield exactly one merge commit"
[ "$(git tag -l vSCRATCH-0003 | wc -l | tr -d ' ')" = 1 ] \
    || fail "the story tag count is not exactly one (the pre-merge mint is the only one)"
STORY_MERGE="$(git log --merges -1 --grep='^merge SCRATCH-0003 (story complete)$' --format=%H)"
[ -n "$STORY_MERGE" ] || fail "the story's own merge commit is not findable"
[ "$(git rev-parse vSCRATCH-0003)" = "$(git rev-parse "$STORY_MERGE^2")" ] \
    || fail "the tag does not sit at the story branch head the merge carried (its second parent)"
grep -q "^\*\*Status:\*\* completed" _grid4d/story/SCRATCH-0003.md \
    || fail "the re-run's story doc does not carry Status completed on main (keep 1: the newest stays in story/)"
[ -d "$WT" ] && fail "the worktree survived the completed re-run"

# --- archetype 5: the refusals -------------------------------------------------------
note "archetype 5a: dirty main tree at create"
MERGES_BEFORE="$(git log --merges --format=%H | wc -l | tr -d ' ')"
echo dirt > dirt.txt
if "$AHABASE" story create "the refused story" --root . >"$SANDBOX/ref-out.txt" 2>&1; then
    fail "story create accepted a dirty main tree"
fi
grep -q "uncommitted changes" "$SANDBOX/ref-out.txt" \
    || fail "the dirty-tree refusal does not name its reason"
[ -z "$(git tag -l vSCRATCH-0004)" ] || fail "the dirty-tree refusal minted a tag"
[ ! -d "$WTS/SCRATCH-0004" ] || fail "the dirty-tree refusal minted a worktree"
if git branch --list "feature/SCRATCH-0004*" | grep .; then
    fail "the dirty-tree refusal minted a branch"
fi
rm dirt.txt

note "archetype 5b: root on another branch at complete"
"$AHABASE" story create "the misrooted story" --root . || fail "story create refused a clean tree"
perl -pi -e 's/\{GOAL\}/the misrooted goal/' "$WTS/SCRATCH-0004/_grid4d/story/SCRATCH-0004.md"
git -C "$WTS/SCRATCH-0004" add -A
git -C "$WTS/SCRATCH-0004" commit -q -m "SCRATCH-0004(docs): the one edit"
git checkout -q -b elsewhere
if "$AHABASE" story complete SCRATCH-0004 --root . >"$SANDBOX/ref-out.txt" 2>&1; then
    fail "story complete accepted a root on another branch"
fi
grep -q "the root is on 'elsewhere', not the main branch 'main'" "$SANDBOX/ref-out.txt" \
    || fail "the misrooted refusal does not name both branches"
grep -q "checkout main before completing" "$SANDBOX/ref-out.txt" \
    || fail "the misrooted refusal does not name the recovery"
[ -z "$(git tag -l vSCRATCH-0004)" ] || fail "the misrooted refusal minted a tag"
grep -q "^\*\*Status:\*\* in_progress" "$WTS/SCRATCH-0004/_grid4d/story/SCRATCH-0004.md" \
    || fail "the misrooted refusal changed the story Status"
git checkout -q main
git worktree remove "$WTS/SCRATCH-0004"
git branch -D "feature/SCRATCH-0004-the-misrooted-story" >/dev/null

note "archetype 5c: incomplete story set at complete"
"$AHABASE" story create "the incomplete story" --root . || fail "story create refused a clean tree"
rm "$WTS/SCRATCH-0004/_grid4d/story/SCRATCH-0004-tests.md"
git -C "$WTS/SCRATCH-0004" add -A
git -C "$WTS/SCRATCH-0004" commit -q -m "SCRATCH-0004(chore): drop the tests file"
if "$AHABASE" story complete SCRATCH-0004 --root . >"$SANDBOX/ref-out.txt" 2>&1; then
    fail "story complete accepted an incomplete set"
fi
grep -q "the story set is incomplete: SCRATCH-0004-tests.md is missing" "$SANDBOX/ref-out.txt" \
    || fail "the incomplete-set refusal does not name the missing file"
[ -z "$(git tag -l vSCRATCH-0004)" ] || fail "the incomplete-set refusal minted a tag"
grep -q "^\*\*Status:\*\* in_progress" "$WTS/SCRATCH-0004/_grid4d/story/SCRATCH-0004.md" \
    || fail "the incomplete-set refusal changed the story Status"
MERGES_AFTER="$(git log --merges --format=%H | wc -l | tr -d ' ')"
[ "$MERGES_AFTER" = "$MERGES_BEFORE" ] \
    || fail "a refusal added a merge commit"
git worktree remove --force "$WTS/SCRATCH-0004"
git branch -D "feature/SCRATCH-0004-the-incomplete-story" >/dev/null

note "R3 GREEN: five archetypes through story create/status/complete alone"
