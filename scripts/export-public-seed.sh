#!/bin/sh
# AHA-0034: build the scrubbed public seed from a source ref.
# Usage: scripts/export-public-seed.sh [SRC [DEST_DIR]]
#   SRC: a git ref (archived via git archive) OR an existing working-tree
#   directory (copied without .git - a review copy with no git metadata can
#   run the gate directly; review round 1, AHA-0034).
# Replacement patterns and mirror markers come from
# ${AHA_WORKSPACE:-$HOME/ahabase}/_config/ahabase-scrub-patterns.txt
# (uncommitted config - this script deliberately carries no literals).
# Matching is CASE-INSENSITIVE and CONTIGUOUS: every class token is replaced
# and re-verified in any case form, stems ordered after their longer forms
# (review round 1, AHA-0034).
# Exclusion rule: a story-history artifact map whose lines mentioning a mirror
# marker exceed MIRROR_THRESHOLD is dropped from the seed (generated
# foreign-tree mirror; the private archive keeps the full record) - and the
# rule is re-verified over the kept maps, fail closed.
# Secret scan: a fixed list of public token shapes runs over the whole seed
# and fails closed on any hit (github pat/oauth, AWS, sk-, slack, gitlab,
# google, PEM private-key headers; review round 1, AHA-0034).
set -eu

SRC=${1:-HEAD}
DEST=${2:-${AHA_WORKSPACE:-$HOME/ahabase}/_temp/ahabase-public-seed}
CONFIG="${AHA_WORKSPACE:-$HOME/ahabase}/_config/ahabase-scrub-patterns.txt"
MIRROR_THRESHOLD=${MIRROR_THRESHOLD:-100}

[ -f "$CONFIG" ] || { echo "config not found: $CONFIG" >&2; exit 2; }

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
if [ -d "$SRC" ]; then
  (cd "$SRC" && tar -cf - --exclude .git .) | tar -xf - -C "$WORK"
else
  git archive "$SRC" | tar -x -C "$WORK"
fi

MARKERS=$(sed -n 's/^# markers: //p' "$CONFIG")
[ -n "$MARKERS" ] || { echo "no markers line in config" >&2; exit 2; }
MARKER_RE=$(printf '%s' "$MARKERS" | tr ' ' '|')

# 1) exclude mirror-class artifact maps (history only; the active set keeps
#    its shape); then re-verify the rule over what stayed (fail closed).
HIST="$WORK/_grid4d/story/history"
[ -d "$HIST" ] || { echo "history directory not found in source" >&2; exit 2; }
excluded=0
for f in "$HIST"/*-artifact-map.md; do
  [ -e "$f" ] || break
  n=$(grep -c -i -E "$MARKER_RE" "$f" || true)
  if [ "$n" -gt "$MIRROR_THRESHOLD" ]; then
    rm "$f"
    excluded=$((excluded + 1))
    echo "excluded mirror-class ($n markers): ${f#"$HIST"/}"
  fi
done
kept_max=0
for f in "$HIST"/*-artifact-map.md; do
  [ -e "$f" ] || break
  n=$(grep -c -i -E "$MARKER_RE" "$f" || true)
  [ "$n" -le "$MIRROR_THRESHOLD" ] || {
    echo "mirror re-verify FAILED: kept map above threshold (${f#"$HIST"/}, $n markers)" >&2
    exit 1
  }
  [ "$n" -gt "$kept_max" ] && kept_max=$n
done
echo "mirror rule verified: $excluded excluded, kept maps at $kept_max markers or fewer (threshold $MIRROR_THRESHOLD)"

# 2) string replacements in config order (longest first), case-insensitive;
#    perl instead of sed -i so the gate runs on macOS and Linux alike.
TAB=$(printf '\t')
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in \#*|"") continue;; esac
  pat=${line%%"$TAB"*}
  rep=${line#*"$TAB"}
  [ "$pat" = "$rep" ] && continue
  case "$pat" in
    -*) echo "pattern starts with a dash, refusing: row ${pat#-}*" >&2; exit 2;;
  esac
  grep -rl -i -F -- "$pat" "$WORK" | while IFS= read -r f; do
    perl -pi -e 'BEGIN { $p = shift @ARGV; $r = shift @ARGV } s/\Q$p\E/$r/gi' "$pat" "$rep" "$f"
  done
done < "$CONFIG"

# 3) verify zero remaining per class - case-insensitive, the same population
#    the replacement matched (counts only, no literals in output)
fail=0
while IFS= read -r line || [ -n "$line" ]; do
  case "$line" in \#*|"") continue;; esac
  pat=${line%%"$TAB"*}
  n=$(grep -r -i -F -- "$pat" "$WORK" | wc -l | tr -d ' ')
  echo "class remaining: $n"
  [ "$n" -gt 0 ] && fail=1
done < "$CONFIG"
[ "$fail" -eq 0 ] || { echo "scrub verify FAILED" >&2; exit 1; }

# 4) secret-shape scan over the whole seed (public token prefixes, fail closed)
SECRET_RE='gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|glpat-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|BEGIN [A-Z ]*PRIVATE KEY'
s=$(grep -r -E -- "$SECRET_RE" "$WORK" | wc -l | tr -d ' ')
[ "$s" -eq 0 ] || { echo "secret-shape scan FAILED: $s candidate lines" >&2; exit 1; }
echo "secret-shape scan: 0 candidate lines (github pat/oauth, aws, sk-, slack, gitlab, google, pem shapes)"

mkdir -p "$DEST"
rsync -a --delete --exclude '.git' "$WORK"/ "$DEST"/
echo "seed ready at $DEST"
