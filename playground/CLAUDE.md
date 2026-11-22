# CLAUDE.md

This file provides guidance to Claude Code when working in this workspace.

## What this workspace is

A **consumer playground** for standalone ahabase: this workspace exists to try
the ahabase package exactly the way an outside consumer gets it - from the
wheel, with no development checkout, no other tooling, and no inherited
knowledge. The **ahabase CLI is the primary tool**; nothing else manages the
knowledge or the stories here.

## Layout

```
ahabase.env      the entrypoint: source it before any work (see below)
CLAUDE.md        this file
scenarios.md     the request archetypes this playground walks through
.venv/           ahabase serves from here (installed from the wheel)
repos/scratch/   an empty git repository - the consumer's first touch
repos/messy/     code, its own default branch (trunk), a v0.1 tag, a CI file
```

## The one rule above all: source the entrypoint first

```sh
source ahabase.env
```

`ahabase.env` pins `AHABASE_WORKSPACE` to this workspace. ahabase resolves
that variable first and falls back to `~/ahabase` - on this machine that
default is the **development workspace, which this playground must never
write**. Without the pin, any workspace-resolved path targets the wrong tree.
Source the entrypoint in every shell (and every Claude Code session) before
running ahabase here.

## The workflow

One Epic = one git repository with a `_grid4d/` knowledge tree. An existing
repository becomes an Epic through its own identity file - there is no
parallel registry:

```sh
cd repos/scratch
../.venv/bin/ahabase init SCRATCH --root .     # registers the Epic
../.venv/bin/ahabase validate --root .        # must hold
../.venv/bin/ahabase story create "the request" --root .
# ... work in _worktrees/<STORY>/ (the story set lives there) ...
cd .. && cd -   # return to the Epic's main tree, on the declared branch
../.venv/bin/ahabase story complete SCRATCH-0001 --root .
```

- Stories live in worktrees (`_worktrees/<STORY>/`); `complete` runs from the
  Epic's main tree, on the branch the def file declares (`**Branch:**`, else
  git's default).
- `complete` tags `v<STORY>`, merges `--no-ff`, archives beyond the declared
  history window (`**StoryHistoryKeep:**`), and removes the worktree.
- Every refusal names its reason - read it, fix what it names, re-run.
  Nothing is written before a refusal is cleared.
- A conflicted merge aborts clean: resolve the conflict on the main branch,
  then re-run `complete`; it is idempotent.

## Conventions

- Story documents are written in **English** (they are shared material).
- Commit messages: `<STORY>(<type>): <description>` (`feat`, `fix`, `docs`,
  `chore`, ...).
- `scenarios.md` is the playbook - walk its archetypes with the CLI alone.
