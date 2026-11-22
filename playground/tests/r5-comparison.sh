#!/bin/sh
# AHA-0031 R5: the comparison lens - the shelf builds sanitized, and the
# sample walk names every door the census records.
#
# The deterministic substrate of the gap walk (the walk itself is the
# seat's act, the chapter in scenarios.md): the reference shelf builds
# green into a throwaway playground, carries all four files, survives the
# sanitization probes (no machine paths, no account names), is idempotent
# with a stable census, and the versioned sample report names every door
# group of the census - a census row with no report row is a stale walk,
# a red, not a silence.

set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
BOOTSTRAP="$(CDPATH= cd -- "$HERE/.." && pwd)/bootstrap.sh"
REFERENCE="$(CDPATH= cd -- "$HERE/.." && pwd)/reference.sh"
SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-pg-r5.XXXXXX")"
SANDBOX="$(CDPATH= cd -- "$SANDBOX" && pwd)"  # canonical: TMPDIR may end in /
trap 'rm -rf "$SANDBOX"' EXIT
WS="$SANDBOX/workspace"

fail() { echo "R5 RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

# --- the shelf builds into a bootstrapped playground -----------------------------
note "bootstrap + the reference shelf"
sh "$BOOTSTRAP" "$WS" >/dev/null || fail "the bootstrap did not run green"
sh "$REFERENCE" "$WS" >/dev/null || fail "the shelf did not build"

for f in dev-doors.txt dev-claude.md dev-knowledge.txt dev-memory.txt; do
    [ -s "$WS/reference/$f" ] || fail "the shelf file $f is missing or empty"
done
grep -q '^## the evolucean CLI' "$WS/reference/dev-doors.txt" \
    || fail "the census does not carry the evolucean tree"
grep -q '^## the ahabase CLI' "$WS/reference/dev-doors.txt" \
    || fail "the census does not carry the ahabase tree"
grep -q '^Commands:' "$WS/reference/dev-doors.txt" \
    || fail "the census carries no command list"

# --- sanitization: no machine paths, no account names -----------------------------
if grep -R -n -E '/Users/|/home/' "$WS/reference"; then
    fail "machine paths survive in the shelf"
fi
# the account-name class, derived at run time - no account token is written
# into this repo: the current user, plus every account riding the corporate
# sandbox shape in the RAW development CLAUDE.md (the standing witness the
# sanitizer masks by shape; a new shape there widens this class with it)
DEV="${AHABASE_DEV_WORKSPACE:-$HOME/ahabase}"
ACCOUNT_CLASS="$USER $(sed -n -E 's/.*<schema>_([A-Za-z0-9_-]+)_manufacturing.*/\1/p' "$DEV/CLAUDE.md" | sort -u)"
for account in $ACCOUNT_CLASS; do
    if grep -R -F -n "$account" "$WS/reference"; then
        fail "the account token '$account' survives in the shelf"
    fi
done

# --- the inventory names the Epics --------------------------------------------------
grep -q '^## evolucean' "$WS/reference/dev-knowledge.txt" \
    || fail "the inventory does not name the evolucean Epic"
grep -q '^## ahabase' "$WS/reference/dev-knowledge.txt" \
    || fail "the inventory does not name the ahabase Epic"

# --- idempotent: a re-run is green and the census is stable -------------------------
cp "$WS/reference/dev-doors.txt" "$SANDBOX/doors-first.txt"
sh "$REFERENCE" "$WS" >/dev/null || fail "the shelf re-run refused"
cmp -s "$SANDBOX/doors-first.txt" "$WS/reference/dev-doors.txt" \
    || fail "the census is not stable across a re-run"

# --- the chapter carries the three-way classification vocabulary ---------------------
SCEN="$(CDPATH= cd -- "$HERE/.." && pwd)/scenarios.md"
[ -f "$SCEN" ] || fail "the scenarios document is missing"
grep -q 'package gap' "$SCEN" || fail "the chapter does not name the package gap class"
grep -q 'self-description gap' "$SCEN" \
    || fail "the chapter does not name the self-description gap class"
grep -q 'dev-only by design' "$SCEN" \
    || fail "the chapter does not name the dev-only class"

# --- the sample walk names every census door - BOTH trees ---------------------------
# The census records two Commands: blocks (the development CLI and the
# ahabase CLI); the naming check walks them all. The young package moves
# first - a ninth ahabase door must re-walk the sample exactly like a new
# development door (the checkpoint-1 fold: 61-of-68 enforcement was a
# silence the AC forbids).
SAMPLE="$(CDPATH= cd -- "$HERE/.." && pwd)/reports/consumer-gap-sample.md"
[ -f "$SAMPLE" ] || fail "the sample walk is missing from the repository"
DOORS="$(
    awk '/^Commands:/{block=1; next} block && /^  [a-z]/{print $1} block && /^[^ ]/{block=0}' "$WS/reference/dev-doors.txt"
)"
[ -n "$DOORS" ] || fail "the census yielded no door groups"
COUNT=0
for door in $DOORS; do
    COUNT=$((COUNT + 1))
    # a boundary-safe naming check: "test" must not ride inside "test-role"
    grep -qE "(^|[^a-z-])$door([^a-z-]|$)" "$SAMPLE" \
        || fail "the census door '$door' has no row in the sample walk - re-walk (scenarios.md, the comparison lens)"
done
note "$COUNT census doors named by the sample walk (both trees)"

note "R5 GREEN: the shelf stands sanitized and stable; the walk names every door"
