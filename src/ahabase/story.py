"""The story lifecycle: mint, show, complete - locally, in the consumer's own repository (AHA-0030, row 8 basics).

One rule above all: **no state beside the tree**. The next number is
derived by SCAN (``story/`` including ``history/``, and the live
story worktrees) - never stored, no counters branch; the story's
state is its document's ``**Status:**`` line; the configuration is
the def file (``**Branch:**``, ``**StoryHistoryKeep:**``), and what
the def file does not declare falls back to git's own answer (the
branch) or the package default (the window). No
collab, no team log, no phases - the local lifecycle only. The
shared-tree phases (the whole mint, the completion's main-tree phase)
run under ONE inter-process lock inside the git directory - parallel
sessions work parallel stories; a lock held by a dead process is
released by the OS, a failure inside the mint rolls the half-minted
story back, and a mint killed outright (SIGKILL runs no rollback)
leaves a corpse the next create heals - the lock is keyed on the
repository's COMMON git directory, so the mutex is one per repository
whichever tree the command runs from.

- ``create`` refuses a dirty main tree, branches
  ``feature/<STORY>-<short-desc>`` from the main branch, adds the
  worktree at the workspace level (``<workspace>/_worktrees/<repo>/<STORY>``
  - outside the repository, AHA-0035: nothing to ignore in git),
  and mints the story set (story, tests, knowledge map) from the R1
  pattern templates - a whole-file fill of the provided keys, every
  other placeholder left verbatim as the visible TODO.
- ``status`` reads what is: the active story (its live worktree), the
  open stories (worktree or document), the completed count (the
  completed sets in ``story/`` within the window and the archived in
  ``history/``).
- ``complete`` refuses a dirty worktree, an incomplete set, a root not
  on the declared main branch (naming both branches), or a dirty root
  - every refusal precedes every write - then marks the story
  completed, tags ``v<STORY>`` at the head, merges ``--no-ff`` into
  the declared main branch, and archives: completed sets beyond the
  declared window move to ``story/history/`` - archived, never
  deleted, the history keeps them all - then the worktree and the
  branch go. A conflicted merge is ABORTED (nothing left mid-merge),
  the error carries git's own words, and the worktree and branch stay
  intact; complete is idempotent, so a re-run after the conflict is
  resolved on the main branch succeeds.

Fail-closed: every refusal names its reason; the engine never
guesses a merge or an archive.

Implements: implementation-story-lifecycle-blueprint
Blueprint: implementation-story-lifecycle-blueprint

Capability: story-lifecycle
"""

from __future__ import annotations

import contextlib
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from filelock import Timeout

from .config import get_workspace_dir
from .epic import Epic, header
from .grid4d import fill, pattern_template

if sys.platform == "win32":  # pragma: no cover - exercised on the CI Windows lane
    from . import _win as _platform
else:
    from . import _posix as _platform


class StoryError(Exception):
    """The lifecycle refuses: the message says why."""


def _git(cwd: Path, *args: str) -> str:
    """One git call; a failure raises with git's own words - stderr and
    stdout both, because git reports a merge conflict on stdout."""
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = " ".join(part for part in (result.stderr.strip(), result.stdout.strip())
                          if part)
        raise StoryError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def _merge_in_progress(cwd: Path) -> bool:
    """Whether a merge is underway at the root (MERGE_HEAD resolves)."""
    result = subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
                            cwd=cwd, capture_output=True, text=True)
    return result.returncode == 0


def _require_clean(cwd: Path) -> None:
    if _git(cwd, "status", "--porcelain"):
        raise StoryError(f"the tree at {cwd} has uncommitted changes - commit them first")


def main_branch(epic: Epic) -> str:
    """Where a story merges: the def file's ``**Branch:**`` declaration,
    else git's ``init.defaultBranch``, else ``main`` - and it must exist."""
    branch = header(epic.identity.read_text(encoding="utf-8", errors="replace"), "Branch")
    if not branch:
        result = subprocess.run(["git", "config", "init.defaultBranch"],
                                cwd=epic.root, capture_output=True, text=True)
        branch = result.stdout.strip() or "main"
    _git(epic.root, "rev-parse", "--verify", branch)
    return branch


def history_keep(epic: Epic) -> int:
    """The window the def file declares (``**StoryHistoryKeep:**``, default 2):
    how many completed story sets stay in ``story/`` before the older ones
    move to ``story/history/``."""
    value = header(epic.identity.read_text(encoding="utf-8", errors="replace"),
                   "StoryHistoryKeep")
    if not value or not value.isdigit():
        return 2
    return int(value)


def _worktrees_dir(epic: Epic) -> Path:
    """The worktrees home: ``<workspace>/_worktrees/<repo-directory>`` - at
    the workspace root, outside every repository (the proven topology,
    AHA-0035); the repository's directory name is its shelf, and nothing
    worktree-shaped ever lands inside the repository itself."""
    return get_workspace_dir() / "_worktrees" / epic.root.name


def _worktree_paths(epic: Epic) -> list[Path]:
    """Every live worktree of the repository, wherever it sits - git's own
    authoritative list, never a path convention: the workspace shelf, a
    legacy in-repo ``_worktrees/`` layout, a hand-made location all appear
    (AHA-0035 review round 1: a convention-only scan let the next mint
    silently reuse a live old-layout story's ID). The main tree itself is
    excluded - its story folders are read directly."""
    paths: list[Path] = []
    for line in _git(epic.root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):])
            if path != epic.root:
                paths.append(path)
    return sorted(paths)


def _story_dirs(epic: Epic) -> list[Path]:
    """Every folder the numbering scan reads: the story folders of the main
    tree (with history) and of each live worktree, wherever that worktree
    sits (the authoritative worktree list)."""
    dirs = [epic.grid / "story", epic.grid / "story" / "history"]
    for worktree in _worktree_paths(epic):
        dirs += [worktree / "_grid4d" / "story",
                 worktree / "_grid4d" / "story" / "history"]
    return [d for d in dirs if d.is_dir()]


def next_number(epic: Epic) -> int:
    """The next story number: one more than the max the tree already names
    (the scan, never a stored counter)."""
    pattern = re.compile(rf"^{re.escape(epic.story_prefix)}-(\d+)")
    highest = 0
    for folder in _story_dirs(epic):
        for path in folder.glob("*.md"):
            match = pattern.match(path.name)
            if match:
                highest = max(highest, int(match.group(1)))
    return highest + 1


def _slug(description: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", description.lower()).strip("-")
    return slug or "story"


_LOCK_TIMEOUT = 120.0  # the bound: a stuck holder refuses by name, never hangs a session


def _lock_path(root: Path) -> Path:
    """The lifecycle lock's file: inside the repository's COMMON git
    directory - one mutex per repository, whichever tree (main or linked
    worktree) the command runs from."""
    git_dir = Path(_git(root, "rev-parse", "--path-format=absolute",
                        "--git-common-dir"))
    return git_dir / "ahabase-story.lock"


@contextlib.contextmanager
def _lifecycle_lock(root: Path):
    """The one mutex over the lifecycle's shared-tree mutations (create's
    mint, complete's main-tree phase): a lock file inside the repository's
    common git directory - never in status, never in history, the same
    file from the main tree and from inside a linked worktree - exclusive
    across processes and released on process death; a bounded wait, then
    a named refusal."""
    handle = _platform.lock(_lock_path(root), timeout=_LOCK_TIMEOUT)
    try:
        with handle:
            yield
    except Timeout:
        raise StoryError(
            f"another story command holds the lifecycle lock "
            f"(waited {_LOCK_TIMEOUT:.0f}s) - retry once it finishes") from None


def _is_corpse(corpse: Path, story: str, held: str) -> bool:
    """Strictly a half-minted corpse, never a live story's tree: the
    branch's reflog holds only its creation entry (no commit ever moved
    it), and the worktree's dirt is limited to the mint's own template
    files. Anything else - a hand-merged story's worktree (main caught
    up with the branch, so no commit is beyond main either), a worktree
    with real commits, uncommitted user files - is NOT ours to delete;
    a classification failure (no readable reflog) fails closed the same
    way."""
    result = subprocess.run(["git", "reflog", "--format=%gs", held], cwd=corpse,
                            capture_output=True, text=True)
    entries = [line for line in result.stdout.splitlines() if line.strip()]
    if result.returncode != 0 or len(entries) != 1 \
            or not entries[0].startswith("branch: Created from"):
        return False
    mint = {f"_grid4d/story/{story}.md", f"_grid4d/story/{story}-tests.md",
            f"_grid4d/story/{story}-knowledge-map.md"}
    dirty: set[str] = set()
    for line in _git(corpse, "status", "--porcelain").splitlines():
        path = line[3:].strip()
        if " -> " in path:  # a rename: both sides count as dirt
            dirty.update(part.strip() for part in path.split(" -> "))
        else:
            dirty.add(path)
    return dirty <= mint


def _heal_half_minted(epic: Epic, branch: str) -> list[str]:
    """Remove every half-minted corpse (wherever its worktree sits): a
    story-named worktree whose branch holds no commit beyond the main
    branch AND whose shape is exactly a killed mint (creation-only
    reflog, dirt limited to the mint's own files - the aftermath of a
    create killed between the worktree add and the story-set commit,
    SIGKILL runs no rollback, whichever side of the template writes the
    kill landed on). Everything else is left untouched - a hand-merged
    story's worktree survives with its uncommitted files (measured by
    review, round 2). Safe only inside the lifecycle lock: a live
    mint's worktree passes through the same state, but never outside
    the lock. Returns the healed names."""
    pattern = re.compile(rf"^{re.escape(epic.story_prefix)}-\d+$")
    healed: list[str] = []
    for candidate in _worktree_paths(epic):
        if not (candidate.is_dir() and pattern.match(candidate.name)
                and (candidate / ".git").exists()):
            continue
        if int(_git(candidate, "rev-list", "--count", f"{branch}..HEAD")) > 0:
            continue  # the story set is committed: a live story, not a corpse
        held = _git(candidate, "branch", "--show-current")
        if not held or not _is_corpse(candidate, candidate.name, held):
            continue  # not ours to delete - left untouched, never forced away
        _git(epic.root, "worktree", "remove", "--force", str(candidate))
        _git(epic.root, "branch", "-D", held)
        healed.append(candidate.name)
    return healed


def create(epic: Epic, description: str) -> Path:
    """Mint a story: the next number by scan, the worktree + branch, the
    story set from the pattern templates - the whole mint under the
    lifecycle lock, so concurrent sessions mint serially with distinct
    numbers. Half-minted corpses (a create killed outright) heal first,
    their numbers return to the scan. A failure after the worktree add
    removes the worktree and the branch (never a half-minted orphan) and
    refuses by name. Returns the worktree."""
    root = epic.root
    templates = {doc_type: pattern_template(epic, doc_type)
                 for doc_type in ("story", "tests", "knowledge-map")}
    missing = [doc_type for doc_type, template in templates.items() if template is None]
    if missing:
        raise StoryError(f"no pattern template resolved for {', '.join(missing)}")
    with _lifecycle_lock(root):
        _require_clean(root)
        branch = main_branch(epic)
        _heal_half_minted(epic, branch)
        story = f"{epic.story_prefix}-{next_number(epic):04d}"
        worktree = _worktrees_dir(epic) / story
        if worktree.exists():
            raise StoryError(
                f"{worktree} already exists and is not a half-minted corpse "
                "- the mint refuses to overwrite it")
        worktree.parent.mkdir(parents=True, exist_ok=True)
        feature = f"feature/{story}-{_slug(description)}"
        _git(root, "worktree", "add", "-b", feature, str(worktree), branch)
        try:
            values = {"STORY": story, "TITLE": description, "EPIC": epic.name,
                      "TYPE": "default", "STATUS": "in_progress",
                      "DATE": date.today().isoformat()}
            story_dir = worktree / "_grid4d" / "story"
            for doc_type in ("story", "tests", "knowledge-map"):
                suffix = "" if doc_type == "story" else f"-{doc_type}"
                (story_dir / f"{story}{suffix}.md").write_text(
                    fill(templates[doc_type], values), encoding="utf-8")
            _git(worktree, "add", "-A")
            _git(worktree, "commit", "-m", f"{story}(feat): mint the story set")
        except BaseException as failure:  # the interrupt family too (SIGINT)
            _rollback_mint(root, worktree, feature, story, failure)
    return worktree


def _rollback_mint(root: Path, worktree: Path, feature: str, story: str,
                   failure: BaseException) -> None:
    """Never leave a half-minted story behind: the worktree and the branch
    the mint created go, then the refusal names the failure and the
    cleanup - or names the manual removal when the cleanup itself fails.
    An interrupt (KeyboardInterrupt, SystemExit - not Exception) keeps
    its class: the cleanup ran, the interrupt stands."""
    try:
        _git(root, "worktree", "remove", "--force", str(worktree))
        _git(root, "branch", "-D", feature)
    except StoryError as cleanup:
        raise StoryError(
            f"minting {story} failed ({failure}) and the rollback failed too "
            f"({cleanup}) - remove {worktree} and the branch {feature} by hand, "
            "then retry the create") from failure
    if not isinstance(failure, Exception):
        raise failure
    named = str(failure) or type(failure).__name__
    raise StoryError(
        f"minting the {story} set failed ({named}) - the worktree and the "
        "branch were removed; retry the create") from failure


def _status_of(path: Path) -> str:
    return header(path.read_text(encoding="utf-8", errors="replace"), "Status") or ""


def status(epic: Epic) -> list[str]:
    """What is: the active story, the open stories, the completed count."""
    worktree_stories: list[tuple[str, str]] = []
    open_stories: list[str] = []

    def _where(worktree: Path) -> str:
        """The worktree's readable location: workspace-relative when it sits
        in the shelf, repo-relative when it sits inside the repository (the
        legacy layout shows itself as in-repo), the absolute path only when
        it sits outside both."""
        for base in (get_workspace_dir(), epic.root):
            try:
                return str(worktree.relative_to(base))
            except ValueError:
                continue
        return str(worktree)

    for worktree in _worktree_paths(epic):
        doc = worktree / "_grid4d" / "story" / f"{worktree.name}.md"
        if doc.is_file() and _status_of(doc) != "completed":
            worktree_stories.append((worktree.name, _where(worktree)))
            open_stories.append(f"{worktree.name} (worktree, {_status_of(doc) or 'no Status line'})")
    story_doc = re.compile(rf"^{re.escape(epic.story_prefix)}-(\d+)\.md$")
    completed: set[str] = set()
    for doc in sorted((epic.grid / "story").iterdir()):
        if not (doc.is_file() and story_doc.match(doc.name)):
            continue
        if _status_of(doc) == "completed":
            completed.add(story_doc.match(doc.name).group(1))
        else:
            open_stories.append(f"{doc.stem} (no worktree, {_status_of(doc) or 'no Status line'})")
    history = epic.grid / "story" / "history"
    if history.is_dir():
        archived = re.compile(rf"^{re.escape(epic.story_prefix)}-(\d+)")
        completed |= {archived.match(p.name).group(1) for p in history.glob("*.md")
                      if archived.match(p.name)}
    active = (f"active: {worktree_stories[0][0]} "
              f"(worktree {worktree_stories[0][1]})") \
        if worktree_stories else "active: none"
    return [active, f"open: {', '.join(open_stories) if open_stories else 'none'}",
            f"completed: {len(completed)}"]


def complete(epic: Epic, story: str) -> None:
    """Complete a story: verify the set and the root (on the declared main
    branch, clean - every refusal precedes every write), mark completed,
    tag ``v<STORY>``, merge into the main branch (a conflict aborts, the
    story stays recoverable, a re-run is idempotent), archive beyond the
    history window, remove the worktree and the branch - the whole
    completion under the lifecycle lock, so concurrent sessions complete
    serially, each landing its own merge."""
    root = epic.root
    worktree = _worktrees_dir(epic) / story
    with _lifecycle_lock(root):
        if not worktree.is_dir():
            raise StoryError(f"no worktree for {story} under {worktree.parent}")
        _require_clean(worktree)
        story_dir = worktree / "_grid4d" / "story"
        for suffix in ("", "-tests", "-knowledge-map"):
            if not (story_dir / f"{story}{suffix}.md").is_file():
                raise StoryError(f"the story set is incomplete: {story}{suffix}.md is missing")
        main = main_branch(epic)
        checked = _git(root, "branch", "--show-current")
        if checked != main:
            on = checked or "(detached head)"
            raise StoryError(
                f"the root is on '{on}', not the main branch '{main}' - "
                f"checkout {main} before completing {story}")
        _require_clean(root)

        doc = story_dir / f"{story}.md"
        if _status_of(doc) != "completed":
            doc.write_text(re.sub(r"^(\*\*Status:\*\*).*$", r"\1 completed",
                                  doc.read_text(encoding="utf-8"), count=1, flags=re.MULTILINE),
                           encoding="utf-8")
            _git(worktree, "add", "-A")
            _git(worktree, "commit", "-m", f"{story}(chore): mark completed")
        if not _git(worktree, "tag", "-l", f"v{story}"):
            _git(worktree, "tag", f"v{story}")

        branch = _git(worktree, "branch", "--show-current")
        try:
            _git(root, "merge", "--no-ff", branch, "-m", f"merge {story} (story complete)")
        except StoryError as failure:
            if not _merge_in_progress(root):
                raise
            _git(root, "merge", "--abort")
            raise StoryError(
                f"{failure} - the merge was aborted, the worktree and the branch are "
                f"intact: resolve the conflict on {main}, then re-run complete {story}"
            ) from failure

        _archive_window(epic)
        if _git(root, "status", "--porcelain"):
            _git(root, "add", "-A")
            _git(root, "commit", "-m", f"{story}(chore): archive beyond the history window")

        _git(root, "worktree", "remove", str(worktree))
        _git(root, "branch", "-d", branch)


def _archive_window(epic: Epic) -> None:
    """Completed sets beyond the window move to ``story/history/`` - archived,
    never deleted: the window decides which completed sets stay reachable in
    ``story/`` (the newest), the history keeps them all."""
    story_dir = epic.grid / "story"
    grammar = re.compile(rf"^{re.escape(epic.story_prefix)}-(\d+)\.md$")
    completed = [int(grammar.match(p.name).group(1))
                 for p in sorted(story_dir.iterdir())
                 if p.is_file() and grammar.match(p.name) and _status_of(p) == "completed"]
    beyond = sorted(completed)[:max(len(completed) - history_keep(epic), 0)]
    if not beyond:
        return
    history = story_dir / "history"
    history.mkdir(exist_ok=True)
    for number in beyond:
        for path in sorted(story_dir.glob(f"{epic.story_prefix}-{number:04d}*.md")):
            path.rename(history / path.name)
