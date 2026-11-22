"""The publish door: the mirror becomes the repository's wiki, pushed.

The tail the method side never had: the mirror at
``<workspace>/_wikis/<epic>.wiki`` is made a clone of the repository's
wiki remote (``<repo>.wiki.git`` - the config's ``publish.remote``
overrides the derivation from the origin remote, ``publish.branch``
overrides the default ``master``), the synced delta commits under the
``wiki:`` convention, and the push rides the git credential chain under
the Epic's declared GitHub account - the same fail-closed identity gate
as the release path: the account the safe's login opens must equal the
identity's ``**GitHubAccount:**`` declaration, and every refusal names
its remedy.

Refusal classes, each exit 1 at the door: no wiki remote reachable
(fetch or push transport failure), account mismatch (declaration or
login), ambiguous mirror (a push pending from a failed run plus new
uncommitted changes - pushed by hand or reset, then re-run).

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-publishing
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import click

from ..epic import EpicError, header, load
from .context import WikiRefusal

#: Ambient env vars gh prefers over its stored login - an inherited
#: value would silently replace the safe's login, so the child never
#: sees them (the safe's own scrub set).
_ENV_TOKEN_KEYS = ("GH_TOKEN", "GITHUB_TOKEN",
                   "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN")

_GIT_TIMEOUT = 60


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Run git in the mirror; a missing git is a refusal, never a crash."""
    if shutil.which("git") is None:
        raise WikiRefusal("git is not on PATH - install git first")
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, timeout=_GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise WikiRefusal(f"git {args[0]} timed out after {_GIT_TIMEOUT}s "
                          "in the mirror") from None


def account_of_safe_login(timeout: int = 30) -> str:
    """The login name the safe's gh login opens (the identity probe).

    ``gh api user`` on the safe-owned login; ambient token variables are
    scrubbed from the child (gh prefers them over its stored login), the
    value read is the account name only, and any failure refuses with
    the owner's remedy - never a fallback to another token source.
    """
    gh = shutil.which("gh")
    if gh is None:
        raise WikiRefusal("gh is not on PATH - install the GitHub CLI "
                          "first (the publish door probes the account "
                          "through the safe's gh login)")
    env = {k: v for k, v in os.environ.items() if k not in _ENV_TOKEN_KEYS}
    try:
        result = subprocess.run([gh, "api", "user", "--jq", ".login"],
                                capture_output=True, text=True,
                                timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise WikiRefusal(f"gh api user timed out after {timeout}s - the "
                          "account probe cannot confirm the login") from None
    value = result.stdout.strip()
    if result.returncode != 0 or not value:
        detail = (result.stderr.strip().splitlines()[-1]
                  if result.stderr.strip() else f"exit {result.returncode}")
        raise WikiRefusal(f"gh api user failed: {detail} - the login is the "
                          "safe's gh-login target; its owner refreshes it "
                          "(ahabase safe refresh <name>)")


def declared_account(epic_root: Path) -> str:
    """The Epic identity's ``**GitHubAccount:**`` declaration - the
    account the wiki push runs under; its absence refuses (the publish
    identity is declared, never ambient)."""
    try:
        epic = load(epic_root)
    except EpicError as error:
        raise WikiRefusal(f"cannot read the Epic at {epic_root}: {error} - "
                          "the publish door needs the identity's "
                          "GitHubAccount declaration") from None
    text = epic.identity.read_text(encoding="utf-8", errors="replace")
    account = header(text, "GitHubAccount")
    if not account or account.startswith("<"):
        raise WikiRefusal(f"{epic.identity.name} declares no "
                          "**GitHubAccount:** - fill the declaration; the "
                          "publish push runs under the declared account")
    return account


def _wiki_remote_url(origin: str) -> str:
    """Derive the wiki remote from an origin URL: ``.wiki.git`` on the
    repository path, an ssh github origin normalized to https (the push
    rides the credential chain); an origin already naming a wiki remote
    passes through."""
    if origin.endswith(".wiki") or origin.endswith(".wiki.git"):
        return origin if origin.endswith(".git") else origin + ".git"
    ssh = re.match(r"^git@([^:]+):(.+)$", origin)
    if ssh:
        repo = ssh.group(2)
        return f"https://{ssh.group(1)}/{repo.removesuffix('.git')}.wiki.git"
    https = re.match(r"^(https?://[^/]+/.+)$", origin)
    if https:
        return f"{https.group(1).removesuffix('.git')}.wiki.git"
    raise WikiRefusal(f"cannot derive the wiki remote from origin {origin!r} "
                      "- set publish.remote in the epic's wiki yaml")


def wiki_remote(epic_root: Path, config: dict) -> tuple[str, str]:
    """The wiki remote and branch: the config's ``publish.remote`` /
    ``publish.branch`` override, else derived from the epic repository's
    origin remote (branch defaults to ``master``, the GitHub wiki's)."""
    publish_config = config.get("publish", {})
    remote = publish_config.get("remote")
    if not remote:
        origin = _git(["remote", "get-url", "origin"], cwd=epic_root)
        if origin.returncode != 0 or not origin.stdout.strip():
            raise WikiRefusal(f"the epic repository at {epic_root} has no "
                              "origin remote - set publish.remote in the "
                              "epic's wiki yaml")
        remote = _wiki_remote_url(origin.stdout.strip())
    branch = publish_config.get("branch", "master")
    return remote, branch


def mirror_status(wiki_path: Path, timeout: int = 5) -> dict:
    """Git status of the mirror: ``clean``, ``uncommitted_count`` and the
    first ``files`` - the graduated status read the hooks consume. A git
    that cannot run or times out reports clean (a status read never
    blocks its caller)."""
    try:
        result = subprocess.run(["git", "status", "--porcelain"],
                                cwd=wiki_path, capture_output=True,
                                text=True, timeout=timeout)
        lines = [line for line in result.stdout.strip().split("\n") if line]
        return {"clean": len(lines) == 0, "uncommitted_count": len(lines),
                "files": lines[:5]}
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return {"clean": True, "uncommitted_count": 0, "files": []}


def _head(git) -> str | None:
    """The mirror's HEAD sha; None on an unborn branch."""
    result = git(["rev-parse", "--verify", "-q", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else None


def _on_branch(git, branch: str) -> None:
    """Put the mirror on ``branch`` (created when absent); a failure
    refuses - a silent one would surface three steps later as a
    confusing commit error."""
    result = git(["checkout", "-B", branch])
    if result.returncode != 0:
        raise WikiRefusal(f"git checkout -B {branch} failed in the mirror "
                          f"({result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'no detail'}) "
                          "- resolve the mirror's working tree and re-run")


def publish(epic: str, epic_root: Path, wiki_path: Path, config: dict,
            dry_run: bool = False) -> bool:
    """Make the mirror the repository's wiki: identity gate, clone or
    fetch, delta commit, push. True when a push happened; False when
    there was nothing to publish. Every refusal raises
    :class:`WikiRefusal` with the remedy in the message."""
    account = declared_account(epic_root)
    login = account_of_safe_login()
    if login != account:
        raise WikiRefusal(
            f"the safe's login opens {login!r} but Epic {epic!r} declares "
            f"GitHubAccount {account!r} - fix the identity's declaration or "
            "refresh the safe's gh-login target (the wiki push runs under "
            "the declared account, never silently another)")
    remote, branch = wiki_remote(epic_root, config)

    if not (wiki_path / ".git").exists():
        wiki_path.mkdir(parents=True, exist_ok=True)
        git_state = _git(["init"], cwd=wiki_path)
        if git_state.returncode != 0:
            raise WikiRefusal(f"git init failed in the mirror ({git_state.stderr.strip()})")
        _git(["remote", "add", "origin", remote], cwd=wiki_path)
        click.echo(f"Initialized the mirror as a clone of {remote}")
    else:
        _git(["remote", "set-url", "origin", remote], cwd=wiki_path)

    def git(args: list[str]) -> subprocess.CompletedProcess:
        return _git(args, cwd=wiki_path)

    _on_branch(git, branch)

    fetch = git(["fetch", "origin"])
    if fetch.returncode != 0:
        raise WikiRefusal(
            f"cannot reach the wiki remote {remote} ({fetch.stderr.strip().splitlines()[-1] if fetch.stderr.strip() else 'no detail'}) "
            "- check publish.remote in the epic's wiki yaml and that the "
            "repository's wiki is enabled (its Wiki tab, first page edit)")

    remote_ref = f"origin/{branch}"
    has_remote_state = git(["rev-parse", "--verify", "-q",
                            f"refs/remotes/{remote_ref}"]).returncode == 0
    if has_remote_state:
        pending = git(["rev-list", "--count", f"{remote_ref}..HEAD"])
        pending_count = int(pending.stdout.strip() or 0)
        status = mirror_status(wiki_path)
        if pending_count > 0 and not status["clean"]:
            raise WikiRefusal(
                f"the mirror holds {pending_count} push-pending commit(s) "
                f"from a failed run and new uncommitted changes - push the "
                f"pending commit by hand (git -C '{wiki_path}' push) or "
                "reset it, then re-run")
        git(["reset", "--mixed", remote_ref])
        click.echo(f"Fetched {remote} (head {git(['rev-parse', remote_ref]).stdout.strip()[:7]})")

    git(["add", "-A"])
    staged_empty = git(["diff", "--cached", "--quiet"]).returncode == 0
    head = _head(git)
    remote_head = (git(["rev-parse", remote_ref]).stdout.strip()
                   if has_remote_state else None)

    if dry_run:
        stat = git(["diff", "--cached", "--stat"])
        click.echo(stat.stdout.strip() or "(no changes)")
        click.echo("(Dry run - no commit, no push)")
        return False

    if staged_empty and (head is None or head == remote_head):
        click.echo(f"Nothing to publish - the mirror equals {remote_ref}")
        return False

    if not staged_empty:
        commit = git(["commit", "-m", f"wiki: publish {epic} mirror"])
        if commit.returncode != 0:
            raise WikiRefusal(
                f"git commit failed ({commit.stderr.strip().splitlines()[-1] if commit.stderr.strip() else 'no detail'}) "
                "- configure the git identity (user.name, user.email) and re-run")
        click.echo(f"Committed the delta: {commit.stdout.strip().splitlines()[0] if commit.stdout.strip() else 'ok'}")

    push = git(["push", "-u", "origin", branch])
    if push.returncode != 0:
        detail = (push.stderr.strip().splitlines()[-1]
                  if push.stderr.strip() else "no detail")
        raise WikiRefusal(
            f"git push to {remote} failed: {detail} - the commit stays in "
            "the mirror; fix the cause and re-run (this run pushes it)")
    click.echo(f"Pushed {branch} to {remote}")
    return True
