#!/bin/sh
# The AHA-0031 reference shelf: what the development workspace carries.
#
# A development-side script (run it next to bootstrap.sh, not inside the
# playground's daily life): reads the development workspace READ-ONLY and
# writes a sanitized snapshot into the playground's reference/ shelf - the
# material the gap walk (scenarios.md) compares the consumer's own surface
# against. The shelf is a lens, never ambient context: R1's empty-memory
# decision stands, and nothing here flows back into the development
# workspace.
#
# The shelf carries four files, all sanitized (no machine paths, no
# account names - the census measures doors, not people):
#   dev-doors.txt      the door census: both CLI help trees verbatim
#   dev-claude.md      the development workspace CLAUDE.md
#   dev-knowledge.txt  every registered Epic and its _grid4d folder counts
#   dev-memory.txt     the development memory index - titles only, never
#                      bodies (the secrets discipline; the index lines are
#                      slugs and one-line hooks)
#
# Idempotent: a re-run replaces the shelf. Fail-closed when the
# development workspace or its CLI is absent (this script is meaningless
# off the development machine).
#
# Usage: playground/reference.sh [PLAYGROUND]
#        AHABASE_DEV_WORKSPACE overrides the development workspace root

set -eu

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PLAYGROUND="${1:-$HOME/ahabase-playground}"
DEV="${AHABASE_DEV_WORKSPACE:-$HOME/ahabase}"
DEVTCLI="$DEV/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage"

fail() { echo "REFERENCE RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

[ -d "$DEV/evolucean/_grid4d" ] \
    || fail "the development workspace was not found at $DEV (set AHABASE_DEV_WORKSPACE)"
[ -x "$DEVTCLI" ] \
    || fail "the development CLI was not found at $DEVTCLI"
[ -x "$PLAYGROUND/.venv/bin/ahabase" ] \
    || fail "$PLAYGROUND is not a bootstrapped playground (no wheel-served ahabase)"

sanitize() {  # every machine path collapses to ~; an account riding INSIDE
    # an identifier (the corporate sandbox shape <schema>_<name>_manufacturing)
    # is masked by shape, not by name - no account token lands in this repo
    sed -E \
        -e "s|$HOME|~|g" \
        -e 's|/Users/[A-Za-z0-9_-]+|~|g' \
        -e 's|/home/[A-Za-z0-9_-]+|~|g' \
        -e 's|(<schema>_)[A-Za-z0-9_-]+(_manufacturing)|\1<account>\2|g'
}

REF="$PLAYGROUND/reference"
mkdir -p "$REF"

# --- the door census: both help trees verbatim --------------------------------
note "the door census"
{
    echo "# the door census - what each CLI exposes at its top level"
    echo
    echo "## the evolucean CLI (knowledge-usage, the development primary)"
    "$DEVTCLI" --help 2>&1
    echo
    echo "## the ahabase CLI (the playground's primary, from the wheel)"
    "$PLAYGROUND/.venv/bin/ahabase" --help 2>&1
} | sanitize > "$REF/dev-doors.txt"

# --- the development CLAUDE.md -------------------------------------------------
note "the development CLAUDE.md"
sanitize < "$DEV/CLAUDE.md" > "$REF/dev-claude.md"

# --- the knowledge inventory ---------------------------------------------------
note "the knowledge inventory"
{
    echo "# the development workspace knowledge inventory"
    echo
    echo "An Epic registers through its identity file (_grid4d/story/<EPIC>.md);"
    echo "the census below lists every directory under the workspace root that"
    echo "carries a _grid4d/ tree, with its folder counts (.md files, top level)."
    echo
    for d in "$DEV"/*/; do
        [ -d "${d%/}/_grid4d" ] || continue
        name="$(basename "$d")"
        echo "## $name"
        for folder in ontology implementation pattern playbook issue metric story subepic; do
            [ -d "${d%/}/_grid4d/$folder" ] || continue
            count="$(find "${d%/}/_grid4d/$folder" -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
            echo "- $folder: $count"
        done
        echo
    done
} | sanitize > "$REF/dev-knowledge.txt"

# --- the memory index: titles only, never bodies -------------------------------
note "the memory index (titles only)"
SLUG="$(printf '%s' "$DEV" | sed 's|^/|-|; s|/|-|g')"
MEMORY="$HOME/.claude/projects/$SLUG/memory/MEMORY.md"
{
    echo "# the development memory index - titles only, never bodies"
    echo
    if [ -f "$MEMORY" ]; then
        echo "The index lines (memory-file stems and one-line hooks) of the"
        echo "development seat's persistent memory. Bodies stay unread:"
        echo "memory is development practice, not package material."
        echo
        grep -v '^#' "$MEMORY" | grep -v '^[[:space:]]*$'
    else
        echo "(no memory index was found at this workspace slug)"
    fi
} | sanitize > "$REF/dev-memory.txt"

note "the shelf stands at $PLAYGROUND/reference/:"
ls -l "$REF" | awk 'NR > 1 { print "-", $NF }'
note "REFERENCE GREEN: the development surface, sanitized, read-only"
note "next: the gap walk - scenarios.md, chapter 'the comparison lens'"
