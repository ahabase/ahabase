#!/bin/sh
# The TestPyPI dry-run pipeline (AHA-0029 R4).
#
#   build -> containment gate -> upload to TestPyPI -> clean-venv install -> import + doctor
#
# The containment gate stands IN the release path: a finding stops the
# upload, so nothing leaves the tree that the scan has not cleared.
# Nothing beyond TestPyPI happens here - the production publish, the
# PyPI name reservation and the public repository each wait for the
# Human's go (the MVP ruling, EVOLUCEAN-0555).
#
# Token: the upload reads TWINE_USERNAME / TWINE_PASSWORD from the
# environment; run the whole script through the safe so the token never
# rides the command line or a file:
#
#   ahabase safe set testpypi-token --purpose "TestPyPI upload token"   # once, by the Human
#   ahabase safe bind testpypi-token "$(command -v twine)"
#   ahabase safe run \
#     --env TWINE_USERNAME=__token__ --env TWINE_PASSWORD=safe://testpypi-token \
#     -- scripts/testpypi_dryrun.sh
#
# Requirements: python with this repository's test extras (build,
# hatchling) importable as `ahabase`, and twine on PATH for the upload
# leg. SKIP_UPLOAD=1 runs build + gate only (the local rehearsal).
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
outdir=${1:-"$root/dist-dryrun"}
rm -rf "$outdir"
mkdir -p "$outdir"

echo "== 1. build the exact artifacts"
python -m build --no-isolation --outdir "$outdir" "$root"

echo "== 2. the containment gate (a finding stops everything after it)"
python - "$root" "$outdir" <<'EOF'
import sys
from pathlib import Path

from ahabase.artifact_containment import scan_release

root, outdir = Path(sys.argv[1]), Path(sys.argv[2])
wheel = next(outdir.glob("ahabase-*.whl"))
sdist = next(outdir.glob("ahabase-*.tar.gz"))
findings = scan_release(wheel, sdist, root)
for finding in findings:
    print(finding)
if findings:
    sys.exit(f"containment gate: {len(findings)} findings - nothing uploads")
print("containment gate: 0 findings")
EOF

if [ "${SKIP_UPLOAD:-0}" = "1" ]; then
    echo "== gate green; upload skipped (SKIP_UPLOAD=1)"
    exit 0
fi

echo "== 3. upload to TestPyPI (the ruled dry-run channel)"
# the token never touches the process list or the log: it enters only
# the child's environment through the safe (safe://testpypi-token);
# --non-interactive fails closed instead of prompting
ahabase safe run --env TWINE_PASSWORD=safe://testpypi-token -- \
    twine upload --non-interactive -u __token__ \
    --repository-url https://test.pypi.org/legacy/ \
    "$outdir"/ahabase-*.whl "$outdir"/ahabase-*.tar.gz

echo "== 4. the consumer, in a clean environment"
venv="$outdir/consumer-venv"
python -m venv "$venv"
"$venv/bin/pip" install --quiet --extra-index-url https://test.pypi.org/simple/ ahabase

echo "== 5. the first commands a consumer runs"
"$venv/bin/ahabase" --version
"$venv/bin/ahabase" doctor
"$venv/bin/python" -c "import ahabase; print('import OK', ahabase.__version__)"
echo "== dry run complete - nothing beyond TestPyPI"
