"""``ahabase safe``: the secrets door of the CLI.

No command prints a value unless ``get --reveal`` is given by a person at
a terminal; values are read from a hidden prompt or stdin, never from a
command-line argument (arguments end up in shell history and process
lists). ``safe run`` hands a value only to a bound consumer, with a
minimal environment (threat model T2, T9-T12).

Implements: implementation-ahabase-safe-blueprint
Blueprint: implementation-ahabase-safe-blueprint

Capability: secrets-door
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import click

from .safe import (PREFIX, TARGET_KINDS, CREDENTIAL_VERBS, KeyringStore, Safe, SafeError,
                   child_env, overrides_set, parse_credential_request, target_label)

# a seam for tests: how the command obtains its Safe
make_safe = Safe

# comparisons of one name allowed within the window - enough for a shadow
# run, refusing bursts (T11, T12)
COMPARE_LIMIT = 5
COMPARE_WINDOW = 60.0


def _interactive() -> bool:
    """Whether a person is at a terminal (a seam for tests).

    A pseudo-terminal wrapper passes this check; against an agent the
    agent guard is the control (threat model T2).
        Capability: agent-guard

    """
    return sys.stdin.isatty() and sys.stdout.isatty()


def _owner_confirms(action: str, name: str) -> None:
    """Refuse unless a person at a terminal types NAME to confirm ACTION.

        Capability: agent-guard
    """
    if not _interactive():
        raise click.ClickException(
            f"{action} '{name}' needs its owner at an interactive terminal (it refuses "
            f"when input is not a terminal, as in an agent's shell); run it yourself")
    typed = click.prompt(f"type the name '{name}' to {action}", default="",
                         show_default=False)
    if typed != name:
        raise click.ClickException(f"not confirmed - {action} '{name}' cancelled")


def _trust_file():
    from pathlib import Path
    return Path.home() / ".config" / "ahabase" / "trusted-manifest"


def _location_trusted(manifest) -> bool:
    """Whether the owner trusted this manifest location (``safe trust-location``).

        Capability: secrets-store
    """
    try:
        return _trust_file().read_text(encoding="utf-8").strip() == str(manifest.resolve())
    except OSError:
        return False


def _read_value(name: str) -> str:
    if sys.stdin.isatty():
        return click.prompt(f"value for {name}", hide_input=True,
                            confirmation_prompt=True)
    return sys.stdin.read().rstrip("\n")


@click.group("safe")
def safe():
    """Secrets: stored in your own store, referenced as safe://NAME.

        Capability: secrets-door
    """


@safe.command("set")
@click.argument("name")
@click.option("--store", default="keyring", show_default=True,
              type=click.Choice(["keyring"]),
              help="Where the value is kept (the memory store is for tests only)")
@click.option("--purpose", default="", help="What the secret is for")
@click.option("--owner", default="", help="Who is responsible for it")
@click.option("--scope", default="", help="What it grants access to")
@click.option("--expires", default="", help="Expiry date YYYY-MM-DD")
def safe_set(name, store, purpose, owner, scope, expires):
    """Store NAME; the value is read hidden from the terminal or from stdin.

    Setting an existing name is the rotation, and the one place it
    happens: the reachable targets are refreshed in the same command,
    the ones it could not reach are named - exit 1 says the rotation is
    not finished until they are refreshed by hand (`safe refresh NAME`
    retries them).
        Capability: secrets-door

    """
    value = _read_value(name)
    try:
        rotation = make_safe().set(name, value, store=store, purpose=purpose,
                                   owner=owner, scope=scope, expires=expires)
    except SafeError as error:
        raise click.ClickException(str(error))
    click.echo(f"stored {name} in {rotation.entry.store} (reference: {PREFIX}{name})")
    for label in rotation.refreshed:
        click.echo(f"refreshed target {label}")
    for label in rotation.scope:
        click.echo(f"scope target {label} - no copy is maintained")
    for label, reason in rotation.failed:
        click.echo(f"target {label} not refreshed: {reason} - after fixing it: "
                   f"ahabase safe refresh {name}", err=True)
    if rotation.failed:
        sys.exit(1)


@safe.command("list")
def safe_list():
    """List the secrets of the manifest - names and metadata, never values.

        Capability: secrets-door
    """
    try:
        entries = make_safe().entries()
    except SafeError as error:
        raise click.ClickException(str(error))
    if not entries:
        click.echo("no secrets in the manifest")
    for name, e in sorted(entries.items()):
        meta = ", ".join(f"{k}={v}" for k, v in (
            ("store", e.store), ("purpose", e.purpose), ("owner", e.owner),
            ("scope", e.scope), ("expires", e.expires), ("rotated", e.rotated)) if v)
        consumers = ", ".join(c.get("path", "") for c in e.consumers) or "none"
        targets = ", ".join(
            target_label(t) + (" (no copy)" if t.get("copy") is False else "")
            for t in e.targets) or "none"
        click.echo(f"{name}: {meta}; targets: {targets}; consumers: {consumers}")


@safe.command("bind")
@click.argument("name")
@click.argument("command")
@click.option("--prefix", "prefix", multiple=True, metavar="ARG",
              help="An argument the command line must start with (repeatable, in order)")
@click.option("--allow", "allow", multiple=True, metavar="OPTION",
              help="A redirecting option (such as --target) this binding permits")
@click.option("--keep", "keep", multiple=True, metavar="VAR",
              help="A variable of the caller this consumer may receive through --keep")
def safe_bind(name, command, prefix, allow, keep):
    """Allow COMMAND, by its absolute path, to receive NAME through `safe run`.

    The owner's step, at a terminal. Shells, interpreters, wrappers and
    general-purpose network tools cannot be bound; bind the installed
    command that takes its destination from its own configuration.
        Capability: secrets-bind

    """
    _owner_confirms("bind", name)
    try:
        binding = make_safe().bind(name, command, tuple(prefix), tuple(allow), tuple(keep))
    except SafeError as error:
        raise click.ClickException(str(error))
    scope = ("inside its package " + binding["root"] if not binding["digest"]
             else "while the file is unchanged")
    click.echo(f"bound {binding['path']} to {name} (valid {scope})")


@safe.group("target")
def target():
    """Copies in a tool's own store, written by the safe on every `set`.

        Capability: secrets-manifest
    """


@target.command("add")
@click.argument("name")
@click.argument("kind")
@click.argument("spec", nargs=-1)
@click.option("--no-copy", is_flag=True,
              help="Declare helper scope only - the safe maintains no copy "
                   "(git-credential only)")
def target_add(name, kind, spec, no_copy):
    """Register a target on NAME - the owner's step, at a terminal.

    KIND SPEC as the kind takes it: git-credential HOST ACCOUNT (a git
    credential helper's keychain item, e.g. github.com octocat) or
    gh-login [HOSTNAME] (the host's gh CLI login) or gh-login-account
    HOSTNAME ACCOUNT (one account's gh login in its own config dir - a
    second account on the same host). `safe set NAME` and
    `safe refresh NAME` keep the copy current. A git-credential target
    added with --no-copy declares only the host scope `ahabase safe
    credential` answers for - rotation then writes no copy anywhere.
        Capability: secrets-manifest

    """
    _owner_confirms("add a target to", name)
    if no_copy and kind != "git-credential":
        raise click.ClickException(
            "--no-copy is a git-credential option - a gh login is a copy by "
            "definition, there is no scope to declare")
    parsed = _parse_target(kind, spec)
    if no_copy:
        parsed["copy"] = False
    try:
        replaced = make_safe().target_add(name, parsed)
    except SafeError as error:
        raise click.ClickException(str(error))
    label = TARGET_KINDS[kind].label(parsed)
    converted = replaced is not None and replaced != parsed
    if no_copy:
        if converted:
            click.echo(f"target {label} converted to scope only on {name} - the "
                       f"credential helper answers for the host; the safe maintains "
                       f"no copy (a copy already written in the tool's store, if "
                       f"any, stays until removed by hand)")
        else:
            click.echo(f"target {label} added to {name} (scope only) - the credential "
                       f"helper answers for the host; the safe maintains no copy")
    elif converted:
        click.echo(f"target {label} converted to a maintained copy on {name} - "
                   f"`safe set {name}` writes it, `safe refresh {name}` rewrites it")
    else:
        click.echo(f"target {label} added to {name} - `safe set {name}` writes it, "
                   f"`safe refresh {name}` rewrites it")


@target.command("remove")
@click.argument("name")
@click.argument("kind")
@click.argument("spec", nargs=-1)
def target_remove(name, kind, spec):
    """Withdraw a target from NAME (named as in `target add`) - the owner's step.

        Capability: secrets-manifest
    """
    _owner_confirms("remove a target from", name)
    parsed = _parse_target(kind, spec)
    try:
        label = make_safe().target_remove(name, parsed)
    except SafeError as error:
        raise click.ClickException(str(error))
    click.echo(f"removed target {label} from {name}")


def _parse_target(kind: str, spec: tuple[str, ...]) -> dict:
    """The kind's spec from command arguments (never a value).

    The registry is the source of truth for the kinds, read at call time
    (a static choice would freeze it at import).
        Capability: secrets-manifest

    """
    impl = TARGET_KINDS.get(kind)
    if impl is None:
        raise click.ClickException(f"unknown target kind '{kind}' - one of: "
                                   f"{', '.join(sorted(TARGET_KINDS))}")
    try:
        return impl.parse(list(spec))
    except ValueError as error:
        raise click.ClickException(str(error))


@safe.command("refresh")
@click.argument("name")
def safe_refresh(name):
    """Rewrite NAME's targets from the stored value - the owner's step.

    What `safe set` does to the targets; the remedy when a rotation
    could not reach one of them. The value is read in-process and never
    printed.
        Capability: secrets-rotate

    """
    _owner_confirms("refresh the targets of", name)
    try:
        refreshed, scope, failed = make_safe().refresh(name)
    except SafeError as error:
        raise click.ClickException(str(error))
    if not refreshed and not scope and not failed:
        click.echo(f"{name} has no targets")
    for label in refreshed:
        click.echo(f"refreshed target {label}")
    for label in scope:
        click.echo(f"scope target {label} - no copy is maintained")
    for label, reason in failed:
        click.echo(f"target {label} not refreshed: {reason}", err=True)
    if failed:
        sys.exit(1)


@safe.command("trust-location")
def safe_trust_location():
    """Trust the manifest location the override variables point to - the owner's step.

    With AHABASE_HOME or AHABASE_SAFE_MANIFEST set, `safe run` asks its
    owner each time, since the variables could redirect the whole safe;
    a location trusted here passes without a terminal, so services and
    scheduled jobs keep working. One location at a time.
        Capability: secrets-store

    """
    path = make_safe().path.resolve()
    _owner_confirms("trust the manifest location", str(path.parent.name or path))
    trust = _trust_file()
    trust.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(trust, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(str(path) + "\n")
    click.echo(f"trusted {path} for `safe run`")


@safe.command("unbind")
@click.argument("name")
@click.argument("command")
def safe_unbind(name, command):
    """Withdraw COMMAND's binding to NAME - the owner's step, at a terminal.

        Capability: secrets-bind
    """
    _owner_confirms("unbind", name)
    try:
        make_safe().unbind(name, command)
    except SafeError as error:
        raise click.ClickException(str(error))
    click.echo(f"unbound {command} from {name}")


@safe.command("gh-config-dir")
@click.argument("account")
def safe_gh_config_dir(account):
    """Print the gh config directory of ACCOUNT's login (a gh-login-account target).

    Callers select the account with ``GH_CONFIG_DIR=$(ahabase safe
    gh-config-dir ACCOUNT) gh ...``; the safe is the directory's only
    writer, and the path is formed in one place. No value is printed.
        Capability: secrets-manifest
    """
    from .safe import gh_config_dir
    try:
        click.echo(gh_config_dir(account))
    except SafeError as error:
        raise click.ClickException(str(error))


@safe.command("get")
@click.argument("name")
@click.option("--reveal", is_flag=True, help="Really print the value")
def safe_get(name, reveal):
    """Print the value of NAME - only with --reveal, by its owner at a terminal.

        Capability: secrets-door
    """
    if not reveal:
        raise click.ClickException(
            "refusing to print a secret without --reveal; to pass it to a "
            f"program use: ahabase safe run --env VAR={PREFIX}{name} -- PROGRAM")
    _owner_confirms("reveal", name)
    try:
        click.echo(make_safe().get(name))
    except SafeError as error:
        raise click.ClickException(str(error))


@safe.command("credential")
@click.argument("verb")
def safe_credential(verb):
    """git's credential helper over the safe - git asks, the safe answers.

    Wired as ``credential.<url>.helper = !ahabase safe credential``; git
    calls the helper with a verb and a key=value request on stdin. `get`
    answers the username/password of the entry whose git-credential
    target names the host; a host the safe holds nothing for answers
    nothing (exit 0 - git's contract, its next helper answers). `store`
    and `erase` never write the safe: a value enters only through `set`
    by the owner. The value crosses only the stdout pipe to git - never
    stderr, never a log.
        Capability: secrets-door (git's side)

    """
    if verb == "capability":
        return  # this helper offers none: an empty answer is the whole reply
    if verb not in CREDENTIAL_VERBS:
        raise click.ClickException(f"unknown credential verb '{verb}' - git's are "
                                   f"{', '.join(CREDENTIAL_VERBS)}")
    request = parse_credential_request(sys.stdin.read())
    if verb in ("store", "erase"):
        click.echo("the safe stores nothing from git - a value enters only through "
                   "`ahabase safe set`, the owner's step at a terminal", err=True)
        return
    try:
        answer = make_safe().credential(request)
    except SafeError as error:
        # fail soft, git's contract: answering nothing lets git's next helper
        # or its own prompt answer; the notice names the safe's remedy, never
        # a value
        click.echo(f"safe credential: {error}", err=True)
        return
    if answer is not None:
        click.echo(f"username={answer['username']}")
        click.echo(f"password={answer['password']}")
        click.echo("")


@safe.command("delete")
@click.argument("name")
def safe_delete(name):
    """Remove NAME from its store and the manifest - the owner's step, at a terminal.

    Deleting a value or a binding is a loss of access if it was not meant
    (threat model T12), so an agent cannot do it.
        Capability: secrets-door

    """
    _owner_confirms("delete", name)
    try:
        make_safe().delete(name)
    except SafeError as error:
        raise click.ClickException(str(error))
    click.echo(f"deleted {name}")


@safe.command("run", context_settings={"ignore_unknown_options": True})
@click.option("--env", "pairs", multiple=True, metavar="VAR=safe://NAME",
              help="Environment variable of the child and the secret it gets")
@click.option("--keep", "keep", multiple=True, metavar="VAR",
              help="Pass this variable of the caller to the child as well")
@click.argument("command", nargs=-1, required=True, type=click.UNPROCESSED)
def safe_run(pairs, keep, command):
    """Run COMMAND, a bound consumer, with secrets only in its environment.

    The child gets a working base environment (paths, locale, terminal,
    proxy and certificate settings), the kept variables and the named
    values - no other exported value. Executed as an argument list, never
    through a shell.
        Capability: secrets-bind

    """
    s = make_safe()
    overrides = overrides_set()
    if overrides and not _location_trusted(s.path):
        # the override variables redirect the whole safe (threat model T9); a
        # location its owner trusted once passes, so an unattended job is not
        # locked out (T12)
        if not _interactive():
            raise click.ClickException(
                f"{', '.join(overrides)} redirects the safe to {s.path}, which its owner "
                f"has not trusted; at a terminal, trust it once: ahabase safe "
                f"trust-location (or unset {', '.join(overrides)})")
        _owner_confirms(f"run with {', '.join(overrides)} set for", "run")
    refs: list[tuple[str, str]] = []
    for position, pair in enumerate(pairs, start=1):
        var, sep, ref = pair.partition("=")
        if not sep or not var or not ref.startswith(PREFIX):
            # never echo the argument: a mistyped pair may be a raw value
            raise click.ClickException(f"each --env must be VAR={PREFIX}NAME "
                                       f"(argument {position} is not)")
        refs.append((var, ref))
    if not refs:
        raise click.ClickException("nothing to resolve - give --env VAR=safe://NAME, or "
                                   "run the command directly")
    argv = list(command)
    named: dict[str, str] = {}
    try:
        checked = []
        for _, ref in refs:  # every check before any value is read
            checked.append((ref[len(PREFIX):], s.check_consumer(ref[len(PREFIX):], argv)))
        for var in keep:  # a kept variable may carry a value too: the binding names it
            for secret, binding in checked:
                if var not in (binding.get("keep") or []):
                    raise SafeError(f"--keep {var} is not part of {binding['path']}'s "
                                    f"binding to '{secret}'; if it should pass: ahabase "
                                    f"safe bind {secret} {binding['path']} --keep {var}")
        for var, ref in refs:
            named[var] = s.resolve(ref)
    except SafeError as error:
        raise click.ClickException(str(error))
    argv[0] = checked[0][1]["path"]  # execute exactly the string that was checked
    sys.exit(subprocess.run(argv, env=child_env(named, tuple(keep))).returncode)


def _within_compare_limit(name: str) -> bool:
    """Record one comparison of NAME; False when the window's limit is reached."""
    path = make_safe().path.with_name("safe-compare.json")
    now = time.time()
    try:
        recent = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        recent = {}
    if not isinstance(recent, dict) or not isinstance(recent.get(name, []), list):
        recent = {}  # an unreadable record counts nothing (T12)
    # only times inside the window and not in the future: a future time (a
    # clock stepped back, an edited file) must not lock the owner out (T12)
    times = [t for t in recent.get(name, [])
             if isinstance(t, (int, float)) and 0 <= now - t < COMPARE_WINDOW]
    if len(times) >= COMPARE_LIMIT:
        recent[name] = times  # drop what no longer counts, so waiting helps
        _write_limit(path, recent)
        return False
    recent[name] = times + [now]
    _write_limit(path, recent)
    return True


def _write_limit(path, recent) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(recent))
    except OSError:
        pass  # a limit that cannot be recorded must not block the owner (T12)


def _current_value(env_var: str | None, file: str | None, git_remote: str | None) -> str | None:
    """The value as the current source holds it (never printed)."""
    if env_var:
        return os.environ.get(env_var)
    if file:
        try:
            with open(os.path.expanduser(file), encoding="utf-8") as handle:
                # only the line ending: a leading space is part of the value
                return handle.read().rstrip("\r\n")
        except OSError:
            return None
    if git_remote:
        from urllib.parse import unquote, urlsplit
        # the raw URL: `remote get-url` applies insteadOf rewrites, which may
        # carry another token than the repository's own
        out = subprocess.run(["git", "-C", os.path.expanduser(git_remote), "config",
                              "--get", "remote.origin.url"], capture_output=True, text=True)
        if out.returncode != 0:
            return None
        password = urlsplit(out.stdout.strip()).password
        # a URL carries the credential percent-encoded; the safe holds it plain
        return unquote(password) if password else None
    return None


@safe.command("compare")
@click.argument("name")
@click.option("--env", "env_var", metavar="VAR", help="Compare with this environment variable")
@click.option("--file", "file", metavar="PATH", help="Compare with the content of this file")
@click.option("--git-remote", "git_remote", metavar="REPO",
              help="Compare with the credential in the origin URL of this repository")
def safe_compare(name, env_var, file, git_remote):
    """Tell whether NAME holds the same value as its current source.

    For the shadow run before a consumer switches to the safe: prints
    only "same", "different" or what is missing - never a value and never
    a fingerprint (a fingerprint of a short password can be guessed).
    Exit 0 same, 1 different, 2 a side is missing or no source given.
    """
    import hashlib
    import hmac

    if sum(bool(x) for x in (env_var, file, git_remote)) != 1:
        click.echo("give exactly one source: --env, --file or --git-remote")
        sys.exit(2)
    # an equality oracle for any candidate: the owner's step (threat model T11)
    if not _interactive():
        click.echo(f"compare '{name}' needs its owner at an interactive terminal; "
                   "run it yourself")
        sys.exit(2)
    if not click.confirm(f"compare '{name}' with its current source?", default=True):
        sys.exit(2)
    if not _within_compare_limit(name):
        click.echo(f"too many comparisons of '{name}' in the last "
                   f"{int(COMPARE_WINDOW)} s - wait a minute and repeat")
        sys.exit(2)
    try:
        stored = make_safe().get(name)
    except SafeError as error:
        click.echo(f"missing in the safe: {error}")
        sys.exit(2)
    current = _current_value(env_var, file, git_remote)
    if not current:
        click.echo("missing at the source")
        sys.exit(2)
    same = hmac.compare_digest(hashlib.sha256(stored.encode()).digest(),
                               hashlib.sha256(current.encode()).digest())
    click.echo(f"{name}: {'same' if same else 'different'}")
    sys.exit(0 if same else 1)


def health() -> tuple[bool, str]:
    """The doctor check of the safe: store available, entries resolvable."""
    s = make_safe()
    try:
        problems = [text for ok, text in s.health() if not ok]
        s.entries()
    except SafeError as error:
        return False, str(error)
    store = s.stores.get("keyring")
    if isinstance(store, KeyringStore) and any(
            e.store == "keyring" for e in s.entries().values()):
        available, detail = store.available()
        if not available:
            problems.append(f"OS store not usable ({detail})")
    for name in overrides_set():
        problems.append(f"{name} is set - the safe is redirected to {s.path}")
    count = len(s.entries())
    if problems:
        return False, f"{count} secrets; " + "; ".join(problems)
    return True, f"{count} secrets, all present"
