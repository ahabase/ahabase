"""The publish door suite (AHA-0036, R2).

The end-to-end row against a throwaway local bare ``*.wiki.git`` remote
- no live GitHub anywhere in the suite: the identity probe is pinned at
its seam (``account_of_safe_login``), so the gate runs measured while
the credential chain stays offline. Success (clone/init, delta commit,
push; the pushed tree equals the mirror), the delta-only second run,
the nothing-to-publish idempotence, and every refusal polarity
(wrong account, unreachable remote, push-pending plus dirty) with the
remedy printed. Git config is isolated from the host (``/dev/null``
globals) and the commit identity comes from the environment, so the
rows measure the door, not the machine.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from click.testing import CliRunner

import ahabase.wiki.publish as publish_module
from ahabase.cli_wiki import wiki_group

ACCOUNT = "fixture-acct"

# The real probe, captured at import - before any fixture pins it at the
# seam (round-1 finding 1 held green because every end-to-end row pinned
# the probe; these rows drive the real one).
_REAL_PROBE = publish_module.account_of_safe_login


def _stub_gh(tmp_path: Path, body: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Put a stub gh on PATH ahead of everything - the probe's which()
    finds it, the door runs unmeasured by the machine's gh."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    gh = bin_dir / "gh"
    gh.write_text(body)
    gh.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")


def _git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


@dataclass
class PublishFixture:
    workspace: Path
    epic: Path
    mirror: Path
    bare: Path


@pytest.fixture
def fx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PublishFixture:
    workspace = tmp_path / "ws"
    epic = workspace / "fixepic"
    grid = epic / "_grid4d"
    (grid / "ontology").mkdir(parents=True)
    (grid / "story").mkdir(parents=True)
    (workspace / "_config").mkdir(parents=True)
    (grid / "story/FIXEPIC.md").write_text(
        "# FIXEPIC\n\n**Type:** Epic\n**StoryPrefix:** FIXEPIC-\n"
        f"**GitHubAccount:** {ACCOUNT}\n")
    (grid / "ontology/concept-a.md").write_text("# Concept A\n\nv1\n")

    bare = tmp_path / "remotes" / "fixepic.wiki.git"
    bare.parent.mkdir(parents=True)
    _git(["init", "--bare", str(bare)])

    (workspace / "_config/fixepic.wiki.yaml").write_text(
        "documents:\n  concept-a: ontology/concept-a.md\n"
        f"publish:\n  remote: {bare}\n")

    monkeypatch.setenv("AHABASE_WORKSPACE", str(workspace))
    # git isolated from the host: no global/system config, no signing,
    # the commit identity from the environment
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    for key, value in (("GIT_AUTHOR_NAME", "fixture"), ("GIT_AUTHOR_EMAIL", "f@x"),
                       ("GIT_COMMITTER_NAME", "fixture"),
                       ("GIT_COMMITTER_EMAIL", "f@x")):
        monkeypatch.setenv(key, value)
    # the identity probe pinned at its seam: the gate runs, offline
    monkeypatch.setattr(publish_module, "account_of_safe_login",
                        lambda timeout=30: ACCOUNT)
    return PublishFixture(workspace=workspace, epic=epic,
                          mirror=workspace / "_wikis" / "fixepic.wiki",
                          bare=bare)


def _commits(bare: Path) -> int:
    result = _git(["rev-list", "--count", "refs/heads/master"], cwd=bare)
    return int(result.stdout.strip()) if result.returncode == 0 else 0


def _run(*args: str):
    return CliRunner().invoke(wiki_group, list(args))


def test_publish_end_to_end_and_delta_only(fx: PublishFixture) -> None:
    """Success end to end: sync, publish - the mirror becomes a clone,
    the delta commits, the push lands and the pushed tree equals the
    mirror; a second run after a source change pushes only the delta."""
    assert _run("sync", "--epic", "fixepic").exit_code == 0
    first = _run("publish", "--epic", "fixepic")
    assert first.exit_code == 0, first.output
    assert (fx.mirror / ".git").exists()  # a clone now
    assert (fx.mirror / "concept-a.md").exists()

    mirror_head = _git(["rev-parse", "HEAD"], cwd=fx.mirror).stdout.strip()
    bare_head = _git(["rev-parse", "refs/heads/master"], cwd=fx.bare).stdout.strip()
    assert mirror_head == bare_head  # the pushed tree equals the mirror
    assert _commits(fx.bare) == 1
    mirror_status = _run("status", "--epic", "fixepic")
    assert "clean: True" in mirror_status.output

    # the source changes; sync re-copies; publish pushes only the delta
    (fx.epic / "_grid4d/ontology/concept-a.md").write_text("# Concept A\n\nv2\n")
    assert _run("sync", "--epic", "fixepic").exit_code == 0
    second = _run("publish", "--epic", "fixepic")
    assert second.exit_code == 0, second.output
    assert _commits(fx.bare) == 2  # one new commit - the delta, nothing else
    blob = _git(["cat-file", "-p", "refs/heads/master:concept-a.md"],
                cwd=fx.bare).stdout
    assert "v2" in blob  # the pushed bytes are the synced bytes

    # idempotence: nothing changed, nothing to publish
    again = _run("publish", "--epic", "fixepic")
    assert again.exit_code == 0 and "Nothing to publish" in again.output
    assert _commits(fx.bare) == 2


def test_publish_refuses_the_wrong_account(fx: PublishFixture,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
    """The identity gate: a probe naming another account refuses with
    both names and the remedy, before anything is committed or pushed."""
    assert _run("sync", "--epic", "fixepic").exit_code == 0
    monkeypatch.setattr(publish_module, "account_of_safe_login",
                        lambda timeout=30: "someone-else")
    refused = _run("publish", "--epic", "fixepic")
    assert refused.exit_code == 1
    assert "someone-else" in refused.output and ACCOUNT in refused.output
    assert "GitHubAccount" in refused.output  # the remedy names the declaration
    assert _commits(fx.bare) == 0
    assert not (fx.mirror / ".git").exists()  # not even a clone was made


def test_publish_refuses_an_unreachable_remote(fx: PublishFixture) -> None:
    """No wiki remote reachable: the fetch failure refuses with the
    remedy naming publish.remote - never a silent skip."""
    gone = fx.bare.parent / "gone.wiki.git"
    (fx.workspace / "_config/fixepic.wiki.yaml").write_text(
        f"publish:\n  remote: {gone}\n")
    assert _run("sync", "--epic", "fixepic").exit_code == 0
    refused = _run("publish", "--epic", "fixepic")
    assert refused.exit_code == 1
    assert "cannot reach the wiki remote" in refused.output
    assert "publish.remote" in refused.output
    assert _commits(fx.bare) == 0


def test_publish_refuses_pending_plus_dirty(fx: PublishFixture) -> None:
    """The ambiguous mirror: a push-pending commit from a failed run
    plus new uncommitted changes refuses with the remedy - the pending
    state is pushed by hand or reset, then the door runs again."""
    assert _run("sync", "--epic", "fixepic").exit_code == 0
    # a failed push leaves the commit in the mirror: fake it - publish
    # with a dead remote at push time is costly to stage; the state it
    # leaves is a local commit ahead of a fetched remote
    assert _run("publish", "--epic", "fixepic").exit_code == 0
    # sever the link the cheap way: a second local commit (pending) and
    # an unsynced hand edit (dirty) - the state the guard exists for
    (fx.mirror / "hand.md").write_text("hand edit\n")
    _git(["add", "-A"], cwd=fx.mirror)
    _git(["commit", "-m", "hand: local"], cwd=fx.mirror)
    (fx.mirror / "more.md").write_text("dirty\n")

    refused = _run("publish", "--epic", "fixepic")
    assert refused.exit_code == 1
    assert "push-pending" in refused.output
    assert "git -C" in refused.output  # the remedy names the manual push
    assert _commits(fx.bare) == 1  # nothing new landed on the remote


def test_account_probe_fails_closed_without_gh(
        monkeypatch: pytest.MonkeyPatch) -> None:
    """The probe itself: no gh on PATH refuses with the remedy - never
    a fallback that skips the identity gate. (No fx here: the fixture
    pins the probe at its seam; this row measures the real one.)"""
    import shutil
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.raises(publish_module.WikiRefusal, match="gh is not on PATH"):
        publish_module.account_of_safe_login()


def test_probe_returns_the_login_both_polarities(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Round-1 finding 1 (seats c020eeb4 and b39ec132, independently):
    the real probe's success polarity - a gh on PATH that prints the
    login must RETURN it (the function fell off the end and returned
    None, so the gate refused every real run); the failure polarity: a
    non-zero gh refuses with the remedy. No fx: the real function."""
    _stub_gh(tmp_path, "#!/bin/sh\nprintf 'acct-one\\n'\n", monkeypatch)
    monkeypatch.setenv("GH_TOKEN", "ambient-token")  # scrubbed, never a fallback
    assert _REAL_PROBE() == "acct-one"

    _stub_gh(tmp_path, "#!/bin/sh\necho 'bad credentials' >&2\nexit 1\n",
             monkeypatch)
    with pytest.raises(publish_module.WikiRefusal, match="gh api user failed"):
        _REAL_PROBE()


def test_publish_end_to_end_with_the_real_probe(
        fx: PublishFixture, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Round-1 finding 1's coverage gap: every end-to-end row pinned the
    probe at its seam, so the dead probe stayed green. This row releases
    the pin - a stub gh on PATH answers the identity gate for real, the
    gate compares it with the declaration, and the door publishes end
    to end. Only the remote is fixture-local; the probe is the real one."""
    _stub_gh(tmp_path, f"#!/bin/sh\nprintf '{ACCOUNT}\\n'\n", monkeypatch)
    monkeypatch.setattr(publish_module, "account_of_safe_login", _REAL_PROBE)
    assert _run("sync", "--epic", "fixepic").exit_code == 0
    published = _run("publish", "--epic", "fixepic")
    assert published.exit_code == 0, published.output
    assert _commits(fx.bare) == 1


def test_push_child_never_sees_ambient_tokens(
        fx: PublishFixture, tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch) -> None:
    """Round-1 finding 2 (seats c020eeb4 and b39ec132, independently):
    the gate scrubs the ambient token variables from the probe's child,
    but the push-path git children inherited them - a credential helper
    preferring GH_TOKEN could push as the ambient token's account while
    the gate had verified the safe's. Witness: a pre-push hook installed
    through GIT_TEMPLATE_DIR at the mirror's init dumps its environment;
    the ambient token variable must not be in it."""
    template = tmp_path / "tpl"
    (template / "hooks").mkdir(parents=True)
    witness = tmp_path / "hook-env.txt"
    hook = template / "hooks" / "pre-push"
    hook.write_text(f"#!/bin/sh\nenv > {witness}\nexit 0\n")
    hook.chmod(0o755)
    monkeypatch.setenv("GIT_TEMPLATE_DIR", str(template))
    monkeypatch.setenv("GH_TOKEN", "ambient-token")

    assert _run("sync", "--epic", "fixepic").exit_code == 0
    published = _run("publish", "--epic", "fixepic")
    assert published.exit_code == 0, published.output
    assert _commits(fx.bare) == 1  # the push happened - through the hook
    env_seen = witness.read_text()
    assert "GH_TOKEN" not in env_seen  # the child never saw the variable
    assert "ambient-token" not in env_seen  # nor its value
