#!/bin/sh
# AHA-0034: build the scrubbed public seed from a source ref.
# Usage: scripts/export-public-seed.sh [SRC_REF [DEST_DIR]]
# Replacement patterns and mirror markers come from
# ${AHA_WORKSPACE:-$HOME/ahabase}/_config/ahabase-scrub-patterns.txt
# (uncommitted config - this script deliberately carries no literals).
# Exclusion rule: a story-history artifact map whose lines mentioning a mirror
# marker exceed MIRROR_THRESHOLD is dropped from the seed (generated
# foreign-tree mirror; the private archive keeps the full record).
set -eu

SRC_REF=${1:-HEAD}
DEST=${2:-${AHA_WORKSPACE:-$HOME/ahabase}/_temp/ahabase-public-seed}
CONFIG="${AHA_WORKSPACE:-$HOME/ahabase}/_config/ahabase-scrub-patterns.txt"
MIRROR_THRESHOLD=${MIRROR_THRESHOLD:-100}

[ -f "$CONFIG" ] || { echo "config not found: $CONFIG" >&2; exit 2; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
git archive "$SRC_REF" | tar -x -C "$WORK"

MARKERS=$(sed -n 's/^# markers: //p' "$CONFIG")
[ -n "$MARKERS" ] || { echo "no markers line in config" >&2; exit 2; }
MARKER_RE=$(printf '%s' "$MARKERS" | tr ' ' '|')

# 1) exclude mirror-class artifact maps (history only; the active set keeps its shape)
find "$WORK/_grid4d/story/history" -name '*-artifact-map.md' | while read -r f; do
  n=$(grep -c -i -E "$MARKER_RE" "$f" || true)
  if [ "$n" -gt "$MIRROR_THRESHOLD" ]; then
    rm "$f"
    echo "excluded mirror-class ($n markers): ${f#"$WORK"/}"
  fi
done

# 2) string replacements in config order (longest first)
TAB=$(printf '\t')
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in \#*|"") continue;; esac
  pat=${line%%"$TAB"*}
  rep=${line#*"$TAB"}
  [ "$pat" = "$rep" ] && continue
  grep -rl -F -- "$pat" "$WORK" | while read -r f; do
    sed -i '' -e "s|$pat|$rep|g" "$f"
  done
done < "$CONFIG"

# 3) verify zero remaining per class (counts only, no literals in output)
fail=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in \#*|"") continue;; esac
  pat=${line%%"$TAB"*}
  n=$(grep -r -F -- "$pat" "$WORK" | wc -l | tr -d ' ')
  echo "class remaining: $n"
  [ "$n" -gt 0 ] && fail=1
done < "$CONFIG"

[ "$fail" -eq 0 ] || { echo "scrub verify FAILED" >&2; exit 1; }

mkdir -p "$DEST"
rsync -a --delete --exclude '.git' "$WORK"/ "$DEST"/
echo "seed ready at $DEST"
