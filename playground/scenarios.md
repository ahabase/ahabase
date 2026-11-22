# The playground scenarios: five request archetypes, the ahabase CLI alone

> The consumer's playbook. Every step runs the wheel-served ahabase binary
> (`.venv/bin/ahabase`) after `source ahabase.env`. No other tooling exists
> in this workspace.

## The archetypes at a glance

| # | Archetype | Repo | Proves |
|---|-----------|------|--------|
| 1 | docs-only story | scratch | the minimal lifecycle: create, edit, complete |
| 2 | code-plus-tests story | scratch | a story that carries code and its tests |
| 3 | the archive window | scratch | StoryHistoryKeep: 1 - oldest set archived, newest stays |
| 4 | the conflicted merge | scratch | complete aborts clean, names the recovery, re-run completes |
| 5 | the refusals | scratch | the guard paths: dirty tree, wrong branch, incomplete set |

R2's own scenario (the messy repo: an existing repository with its own branch,
tag, and CI file becomes an Epic and its story lands on the **declared**
branch) runs once before the archetypes - it mints the workspace's state the
archetypes then build on.

## 0. The plug-and-play seam (the messy repo)

```sh
source ahabase.env
cd repos/messy
../../.venv/bin/ahabase init MESSY --root .
```

Shape the minted identity (the declarations this repo owns):
`_grid4d/story/MESSY.md` gains `**Branch:** trunk` and
`**CodeArtifacts:** src` under `**StoryPrefix:**` (the instruction lives in
`ahabase init --help` and the init door's own code comment). Fill the
overview placeholder, commit, then:

```sh
../../.venv/bin/ahabase validate --root .          # grid4d: holds
../../.venv/bin/ahabase story create "carry code on the declared branch" --root .
cd ../../_worktrees/messy/MESSY-0001 && edit + git add -A + git commit
cd ../../../repos/messy                            # the main tree, on trunk
../../.venv/bin/ahabase story complete MESSY-0001 --root .
```

The landing is measured three ways: the merge commit sits on `trunk`
(`git log --merges`), the tag `vMESSY-0001` resolves to the story branch tip
(`git rev-parse vMESSY-0001`), and `main` does not exist in this repo. The
pre-existing `v0.1` tag is untouched - complete skips tagging only when the
name already exists, and this fixture's tag shares no `v<STORY>` name.

## 1. A docs-only story

```sh
cd repos/scratch
../../.venv/bin/ahabase init SCRATCH --root .
```

Declare the window in `_grid4d/story/SCRATCH.md`: `**StoryHistoryKeep:** 1`
(archetype 3 measures it). Then per story:

```sh
../../.venv/bin/ahabase story create "describe the request" --root .
cd ../../_worktrees/scratch/SCRATCH-000N   # the worktree home is workspace-level
# fill {GOAL} in the story document, fill the tests definition, commit
cd ../../../repos/scratch
../../.venv/bin/ahabase story status --root .
../../.venv/bin/ahabase story complete SCRATCH-000N --root .
```

## 2. A code-plus-tests story

Same cycle as 1, but the worktree commits a source file and its test file
(the scratch repo needs no `**CodeArtifacts:**` for this - the lifecycle is
package-independent).

## 3. The archive window (StoryHistoryKeep: 1)

Complete two stories in sequence. After the second completion: the oldest
set sits in `_grid4d/story/history/` (archived, never deleted) and the newest
stays in `_grid4d/story/`.

## 4. The conflicted merge

Create a story; in its worktree edit the goal line and commit. **Also** edit
that same line on the main branch (a competing commit). Then `complete`:
the merge conflicts, complete **aborts** - the root holds no `MERGE_HEAD`,
`git status --porcelain` is clean, the worktree and the branch survive, and
the error names the recovery: resolve the conflict on the main branch, then
re-run. Resolve it (make the main branch's line hold the story's content,
commit), re-run `complete`: exactly one merge commit and one tag result.

## 5. The refusals (each names its reason and writes nothing)

- **Dirty main tree at create**: leave an uncommitted file in the main tree,
  run `story create` - refused ("uncommitted changes"); no worktree, no
  branch, no tag appears.
- **Root on another branch at complete**: create a story, check the root out
  on any other branch, run `complete` - refused, naming both branches; no
  tag, no merge, the story's Status unchanged.
- **Incomplete story set at complete**: create a story, delete its `-tests.md`
  from the worktree (committed), run `complete` - refused, naming the missing
  file; nothing written.

## The isolation contract (always true, measured by the story's tests)

This playground writes **nothing** into `~/ahabase` (the development
workspace): no `_data/`, no `_config/`, no sessions. The pin in `ahabase.env`
is what holds that - source it first, every time. The playground's own
workspace carries the seven standard folders at its root (created by the
bootstrap's `ahabase workspace ensure`); the story worktrees mint under
`_worktrees/<repo>/<STORY>/` there - never inside an Epic repository.

## The comparison lens: measuring what the consumer lacks

This playground can answer "what does the development workspace carry that I
do not get?" as a written, evidenced gap report. Nothing is inherited to do
it - the fresh-consumer property stands - because the comparison is an
explicit act over an explicit shelf.

**The reference shelf** (built by the development side, read-only, sanitized -
no machine paths, no account names; four files in `reference/`):

```sh
# from the ahabase repository checkout, on the development machine
playground/reference.sh ~/ahabase-playground
```

- `dev-doors.txt` - the door census: both CLI help trees verbatim
- `dev-claude.md` - the development workspace's CLAUDE.md
- `dev-knowledge.txt` - every registered Epic and its `_grid4d/` folder counts
- `dev-memory.txt` - the development memory index, titles only, never bodies

**The gap walk** (the playground seat's act):

1. Read your own surface first: this `CLAUDE.md`, `ahabase --help` and each
   door's `--help`, the story set a minted worktree carries.
2. Read the shelf, item by item.
3. Write `reports/consumer-gap-<date>.md` (English, a plain table). One row
   per door group in the census:

   | door (the development CLI) | the ahabase side | classification | evidence |
   |---|---|---|---|

   - The **ahabase side** names the door that carries the capability (or how
     it is folded, e.g. `status` lives as `story show`), or `absent`.
   - An absent door is classified exactly one of three ways:
     - **package gap** - the ahabase package lacks the capability; the
       open-source backlog's direct input. Mark it `near-term` when the
       first-public basics (grid4d, trust, story) need it, `deferred`
       otherwise.
     - **self-description gap** - the capability exists but the consumer
       cannot discover it: neither help, nor CLAUDE.md, nor templates say it.
     - **dev-only by design** - epic content, development practice,
       multi-instance machinery: not package material by ruling.
   - Every row names its evidence: a door, a help line, a count, a ruling.
4. The walk reads the shelf and writes only into `reports/` - nothing flows
   back to the development workspace.

**The staleness rule**: the suite row `r5-comparison.sh` enforces that a walk
names every door group the census records - **both sides**: the development
tree's doors get gap rows, the ahabase tree's doors get reverse-direction
rows (the young package moves first; its growth re-walks the report exactly
like a new development door). When either CLI grows a door, the row goes red
- that is the discipline working: re-walk, refresh the report, commit it. A
recorded walk is a claim to re-measure. The versioned example is
`reports/consumer-gap-sample.md` in the repository.
