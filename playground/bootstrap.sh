#!/bin/sh
# The AHA-0031 consumer playground bootstrap: a standalone ahabase workspace.
#
# Creates the live workspace (default ~/ahabase-playground) from this
# repository's versioned material - the workspace CLAUDE.md template, the
# scenarios document, the entrypoint pin - and installs ahabase into the
# workspace's own venv from the BUILT WHEEL (never the checkout, the leg's
# isolation lesson), witnessed by pip show. The two sample repositories of
# R2 mint here as plain git fixtures: a scratch repo (empty - no commits,
# no files; the consumer's first touch) and a messy one (code, its own
# default branch trunk, a pre-existing v0.1 tag sharing no v<STORY> name,
# an existing CI file). Registration through 'ahabase init' is the
# consumer's own act (the scenarios document), not the bootstrap's.
#
# Fail-closed: the bootstrap never touches an existing non-empty workspace
# (init's own words), writes nothing outside the workspace and its build
# sandbox, and seeds no memory - the playground proves ahabase
# self-describes a fresh agent (CLAUDE.md, CLI help, story documents).
#
# Usage: playground/bootstrap.sh [WORKSPACE]   (AHABASE_PYTHON overrides
# the Python that builds the wheel and hosts the venv; needs >= 3.11)

set -eu
PIP_DISABLE_PIP_VERSION_CHECK=1; export PIP_DISABLE_PIP_VERSION_CHECK

HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SRC="$(CDPATH= cd -- "$HERE/.." && pwd)"
WORKSPACE="${1:-$HOME/ahabase-playground}"

fail() { echo "BOOTSTRAP RED: $*" >&2; exit 1; }
note() { echo "== $*"; }

PYTHON="${AHABASE_PYTHON:-python3.13}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then PYTHON=python3; fi
"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
    || fail "$PYTHON is older than 3.11 (the package needs >=3.11) - set AHABASE_PYTHON"

# --- fail-closed on an existing workspace ---------------------------------
if [ -e "$WORKSPACE" ] && [ -n "$(ls -A "$WORKSPACE" 2>/dev/null)" ]; then
    fail "the workspace already exists at $WORKSPACE - the bootstrap never touches an existing tree"
fi

# --- the wheel, not the checkout ------------------------------------------
SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/ahabase-bootstrap.XXXXXX")"
trap 'rm -rf "$SANDBOX"' EXIT
note "building the wheel from $SRC"
"$PYTHON" -m pip wheel --quiet --no-deps --wheel-dir "$SANDBOX/dist" "$SRC" \
    || fail "the wheel did not build"
WHEEL="$(ls "$SANDBOX/dist"/ahabase-*.whl)" || fail "no wheel in dist/"

# --- the workspace net ------------------------------------------------------
note "creating the workspace at $WORKSPACE"
mkdir -p "$WORKSPACE"
WORKSPACE="$(CDPATH= cd -- "$WORKSPACE" && pwd)"

"$PYTHON" -m venv "$WORKSPACE/.venv" || fail "the venv did not create"
"$WORKSPACE/.venv/bin/pip" install --quiet "$WHEEL" || fail "the wheel did not install"
AHABASE="$WORKSPACE/.venv/bin/ahabase"
[ -x "$AHABASE" ] || fail "no ahabase console script in the venv"

note "witness: which distribution serves the workspace"
"$WORKSPACE/.venv/bin/pip" show ahabase | sed -n '1,3p'
"$AHABASE" --version

cp "$HERE/CLAUDE.md" "$WORKSPACE/CLAUDE.md"
cp "$HERE/scenarios.md" "$WORKSPACE/scenarios.md"

# the entrypoint: the named environment file pinning the single workspace
# seam (config.py resolves AHABASE_WORKSPACE first, default ~/ahabase - a
# forgotten pin targets the development workspace, so the pin is load-bearing)
cat > "$WORKSPACE/ahabase.env" <<EOF
# source this before any ahabase (or Claude Code) session in this workspace
export AHABASE_WORKSPACE="$WORKSPACE"
EOF

# the permissions allowlist: the wheel-installed binary runs without
# per-command permission prompts
mkdir -p "$WORKSPACE/.claude"
cat > "$WORKSPACE/.claude/settings.json" <<EOF
{
  "permissions": {
    "allow": [
      "Bash($WORKSPACE/.venv/bin/ahabase:*)",
      "Bash($WORKSPACE/.venv/bin/python:*)",
      "Bash(git:*)"
    ]
  }
}
EOF

# --- the R2 fixtures: plain git repositories, not yet Epics -----------------
note "minting the sample repositories"

# both fixtures pin init.defaultBranch repo-locally: story.main_branch()
# falls back to it when a def file declares no **Branch:**, and a machine's
# global default (master, trunk, ...) must not decide where the consumer's
# stories land - the fixture is deterministic on any machine (F1, the
# checkpoint-1 fold)

# scratch: an empty git repository - no commits, no files
git init -q --initial-branch=main "$WORKSPACE/repos/scratch" \
    || fail "the scratch repo did not init"
git -C "$WORKSPACE/repos/scratch" config user.name "Playground Consumer"
git -C "$WORKSPACE/repos/scratch" config user.email "consumer@playground.test"
git -C "$WORKSPACE/repos/scratch" config init.defaultBranch main

# messy: code, its own default branch (trunk, not main), a pre-existing
# v0.1 tag (sharing no v<STORY> name), an existing CI file
git init -q --initial-branch=trunk "$WORKSPACE/repos/messy" \
    || fail "the messy repo did not init"
(
    cd "$WORKSPACE/repos/messy"
    git config user.name "Playground Consumer"
    git config user.email "consumer@playground.test"
    git config init.defaultBranch trunk
    mkdir -p src .github/workflows
    echo 'def tool():' > src/lib.py
    echo '    return "the messy repo carries code"' >> src/lib.py
    echo '# the messy consumer repository' > README.md
    printf 'name: ci\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n' \
        > .github/workflows/ci.yml
    git add -A
    git commit -q -m "chore: the messy repository's own history"
    git tag v0.1
) || fail "the messy fixture did not mint"

note "the workspace net (nothing outside it was touched):"
find "$WORKSPACE" -name .venv -prune -o -name .git -prune -o -print | sed "s|^$WORKSPACE|.|"
note "BOOTSTRAP GREEN: $WORKSPACE serves ahabase from the wheel"
note "next: cd $WORKSPACE && source ahabase.env, then read scenarios.md"
