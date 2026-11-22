#!/bin/sh
# The AHA-0030 R4 consumer leg: the shipped wheel, proven outside this workspace.
#
# Isolation by construction (checkpoint 0, seat b39ec132): HOME points at a
# throwaway directory, AHABASE_WORKSPACE / AHABASE_CONFIG / AHABASE_HOME are
# unset (the documented env keys are the experiment's controls, not its
# result), so every home-default path of the shipped code lands inside the
# sandbox - asserted after the leg by a HOME snapshot that must be unchanged.
#
# The clean venv installs the BUILT WHEEL (never -e, never the source tree);
# every ahabase command runs with cwd outside the source tree; pip show +
# --version witness which distribution ran. The leg initializes a scratch
# Epic in a fresh git repository, validates it (green), proves three seeded
# violations fail-closed with their naming report, runs the R2 lifecycle
# end to end with the git evidence printed, and inventories the scratch repo
# after every step (init, validate, create, complete) against a declared
# allowlist -
# a registry file (a yaml, a json state) appearing anywhere turns the row
# red immediately. The script's exit 0 depends on the expected failures
# failing. One script, exit 0, output into the story's Notes.

set -eu

SRC="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-leg.XXXXXX")"
trap 'rm -rf "$SANDBOX"' EXIT

fail() { echo "LEG RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

# the leg's own tooling key (the shipped code does not read it): which
# Python builds the wheel and hosts the venv - the package needs >=3.11
PYTHON="${AHABASE_LEG_PYTHON:-python3}"
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || fail "$PYTHON is older than 3.11 (the package needs >=3.11) - set AHABASE_LEG_PYTHON"

# --- isolation by construction -------------------------------------------
mkdir -p "$SANDBOX/home"
export HOME="$SANDBOX/home"
unset AHABASE_WORKSPACE AHABASE_CONFIG AHABASE_HOME || true
cd "$SANDBOX"
note "sandbox: $SANDBOX (HOME=$HOME, cwd outside the source tree)"

# --- the wheel, not the checkout ------------------------------------------
note "building the wheel from $SRC"
"$PYTHON" -m pip wheel --quiet --no-deps --wheel-dir "$SANDBOX/dist" "$SRC" \
    || fail "the wheel did not build"
WHEEL="$(ls "$SANDBOX/dist"/ahabase-*.whl)" || fail "no wheel in dist/"
[ -f "$WHEEL" ] || fail "no wheel found"

"$PYTHON" -m venv "$SANDBOX/venv" || fail "the venv did not create"
"$SANDBOX/venv/bin/pip" install --quiet "$WHEEL" || fail "the wheel did not install"
AHABASE="$SANDBOX/venv/bin/ahabase"
[ -x "$AHABASE" ] || fail "no ahabase console script in the venv"

note "witness: which distribution runs"
"$SANDBOX/venv/bin/pip" show ahabase | sed -n '1,3p'
"$AHABASE" --version

# the HOME snapshot from here on: the shipped code must add nothing
find "$HOME" -type f | sort > "$SANDBOX/home-before.txt"

# --- the scratch consumer Epic --------------------------------------------
note "init: a scratch Epic in a fresh git repository"
mkdir -p "$SANDBOX/consumer"
REPO="$SANDBOX/consumer/demo"
cd "$SANDBOX/consumer"
git init -q "$REPO"
cd "$REPO"
git config user.name "Leg Runner"
git config user.email "leg-runner@example.test"
git config init.defaultBranch main
"$AHABASE" init DEMO --root . || fail "init refused the fresh tree"

inventory() {
    # the scratch repo, sorted, git internals pruned, the story worktrees
    # counted one level deep (their checkout is a copy of this very repo)
    find . -name .git -prune -o -path './_worktrees/*/*' -prune -o -print \
        | sed 's|^\./||' | grep -v '^\.$' | LC_ALL=C sort
}
expect_inventory() {
    STEP="$1"; shift
    inventory > "$SANDBOX/inv-actual.txt"
    printf '%s\n' "$@" > "$SANDBOX/inv-expected.txt"
    diff -u "$SANDBOX/inv-expected.txt" "$SANDBOX/inv-actual.txt" \
        || fail "inventory after the $STEP step is not the declared allowlist (see the diff above)"
    if find . -name .git -prune -o -path './_worktrees/*' -prune -o \
        \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) -print | grep .; then
        fail "a registry-shaped file (yaml/json) appeared in the scratch repo"
    fi
}

INIT_ALLOWLIST="_grid4d
_grid4d/idea
_grid4d/implementation
_grid4d/issue
_grid4d/metric
_grid4d/ontology
_grid4d/pattern
_grid4d/playbook
_grid4d/story
_grid4d/story/DEMO.md"
expect_inventory init $INIT_ALLOWLIST

# the consumer shapes the skeleton: declare the history window (keep 1) and
# fill the overview placeholder - init's parting words, followed
perl -pi -e 's/^\*\*StoryPrefix:.*$/$&\n**StoryHistoryKeep:** 1/; s/\{OVERVIEW\}/a scratch consumer Epic for the leg/' _grid4d/story/DEMO.md
git add -A
git commit -q -m "chore: the scratch Epic"

# --- R1: the valid tree holds ----------------------------------------------
note "validate: the initialized tree holds"
"$AHABASE" validate --root . || fail "validate refused the initialized tree"
echo "validate output: $("$AHABASE" validate --root .)"

# --- R1: three seeded violations, fail-closed ------------------------------
expect_red() {
    DESCRIPTION="$1"; PATTERN="$2"
    if "$AHABASE" validate --root . > "$SANDBOX/red-out.txt" 2>&1; then
        fail "seeded violation did NOT fail: $DESCRIPTION (validate exited 0)"
    fi
    grep -q "$PATTERN" "$SANDBOX/red-out.txt" \
        || fail "seeded violation failed without its naming report: $DESCRIPTION"
    echo "expected failure: $DESCRIPTION -> $(cat "$SANDBOX/red-out.txt")"
}

note "violation 1: an unknown knowledge folder"
mkdir _grid4d/experiments
expect_red "unknown folder" "unknown-folder: _grid4d/experiments"
rmdir _grid4d/experiments

note "violation 2: a misnamed knowledge artifact"
echo "notes" > _grid4d/ontology/notes.md
expect_red "misnamed artifact" "misnamed-artifact: _grid4d/ontology/notes.md"
rm _grid4d/ontology/notes.md

note "violation 3: the identity file gone"
mv _grid4d/story/DEMO.md ../DEMO.md.bak
expect_red "missing identity" "identity:"
mv ../DEMO.md.bak _grid4d/story/DEMO.md
"$AHABASE" validate --root . || fail "validate did not recover after the violations were reverted"
# the whole validate section (green, three violations, recovery) leaves the
# declared net unchanged - the fourth inventory point of the R4 contract
expect_inventory validate $INIT_ALLOWLIST

# --- R2: the lifecycle end to end ------------------------------------------
# one_story_cycle NUMBER DESCRIPTION [allowlist...]: the caller declares the
# net the tree must hold right after create (the create-point inventory).
one_story_cycle() {
    NUMBER="$1"; DESCRIPTION="$2"; shift 2
    note "story create: mint DEMO-$NUMBER"
    "$AHABASE" story create "$DESCRIPTION" --root . || fail "story create refused"
    ls "_worktrees/DEMO-$NUMBER/_grid4d/story/" || fail "no minted set in the worktree"
    [ "$(cat .gitignore)" = "_worktrees/" ] || fail "the engine did not ignore _worktrees/ in git"
    note "story create: the minted set validates"
    ( cd "_worktrees/DEMO-$NUMBER" && "$AHABASE" validate --root . ) \
        || fail "the minted story set does not validate"
    expect_inventory "create$NUMBER" "$@"
    note "one document edit, committed"
    ( cd "_worktrees/DEMO-$NUMBER" \
        && perl -pi -e "s/\\{GOAL\\}/the edited goal $NUMBER/" "_grid4d/story/DEMO-$NUMBER.md" \
        && git add -A \
        && git commit -q -m "DEMO-$NUMBER(docs): the one edit" )
    note "story status: the active story"
    "$AHABASE" story status --root .
    note "story complete: tag, merge, archive, clean"
    "$AHABASE" story complete "DEMO-$NUMBER" --root . || fail "story complete refused"
}

CREATE1_ALLOWLIST=".gitignore
_grid4d
_grid4d/idea
_grid4d/implementation
_grid4d/issue
_grid4d/metric
_grid4d/ontology
_grid4d/pattern
_grid4d/playbook
_grid4d/story
_grid4d/story/DEMO.md
_worktrees
_worktrees/DEMO-0001"
one_story_cycle 0001 "first story" $CREATE1_ALLOWLIST

# window 1: the completed set stays reachable in story/, nothing archived yet
COMPLETE1_ALLOWLIST=".gitignore
_grid4d
_grid4d/idea
_grid4d/implementation
_grid4d/issue
_grid4d/metric
_grid4d/ontology
_grid4d/pattern
_grid4d/playbook
_grid4d/story
_grid4d/story/DEMO-0001-knowledge-map.md
_grid4d/story/DEMO-0001-tests.md
_grid4d/story/DEMO-0001.md
_grid4d/story/DEMO.md
_worktrees"
expect_inventory complete1 $COMPLETE1_ALLOWLIST

CREATE2_ALLOWLIST=".gitignore
_grid4d
_grid4d/idea
_grid4d/implementation
_grid4d/issue
_grid4d/metric
_grid4d/ontology
_grid4d/pattern
_grid4d/playbook
_grid4d/story
_grid4d/story/DEMO-0001-knowledge-map.md
_grid4d/story/DEMO-0001-tests.md
_grid4d/story/DEMO-0001.md
_grid4d/story/DEMO.md
_worktrees
_worktrees/DEMO-0002"
one_story_cycle 0002 "second story" $CREATE2_ALLOWLIST

# beyond the window: DEMO-0001 moved to history/ (archived, never deleted),
# DEMO-0002 stays in story/
COMPLETE2_ALLOWLIST=".gitignore
_grid4d
_grid4d/idea
_grid4d/implementation
_grid4d/issue
_grid4d/metric
_grid4d/ontology
_grid4d/pattern
_grid4d/playbook
_grid4d/story
_grid4d/story/DEMO-0002-knowledge-map.md
_grid4d/story/DEMO-0002-tests.md
_grid4d/story/DEMO-0002.md
_grid4d/story/DEMO.md
_grid4d/story/history
_grid4d/story/history/DEMO-0001-knowledge-map.md
_grid4d/story/history/DEMO-0001-tests.md
_grid4d/story/history/DEMO-0001.md
_worktrees"
expect_inventory complete2 $COMPLETE2_ALLOWLIST

note "git evidence"
echo "tags: $(git tag)"
echo "merge: $(git log --oneline --merges -n 1)"
git log --oneline | head -n 12
[ "$(git tag)" = "vDEMO-0001
vDEMO-0002" ] || fail "the tags vDEMO-0001 vDEMO-0002 are not at their heads"
for tag in vDEMO-0001 vDEMO-0002; do
    git merge-base --is-ancestor "$(git rev-parse "$tag")" HEAD \
        || fail "main does not carry the completed story $tag"
done
[ ! -d _worktrees/DEMO-0002 ] || fail "the worktree survived completion"
git branch --list "feature/DEMO-*" | grep . && fail "a story branch survived completion" || true

note "story status after completion"
"$AHABASE" story status --root .

note "story create re-run: the scan mints the next number"
OUT="$("$AHABASE" story create "third story" --root .)" || fail "the re-run refused"
echo "$OUT"
echo "$OUT" | grep -q "DEMO-0003 minted" || fail "the re-run did not mint DEMO-0003"

# --- the HOME snapshot: the shipped code added nothing ----------------------
find "$HOME" -type f | sort > "$SANDBOX/home-after.txt"
diff -u "$SANDBOX/home-before.txt" "$SANDBOX/home-after.txt" \
    || fail "the shipped code wrote into HOME (see the diff above)"
note "HOME: unchanged by every ahabase command"

note "LEG GREEN: the consumer leg holds (exit 0)"
