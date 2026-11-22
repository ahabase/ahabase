"""The safe: one interface for secrets, pluggable stores, references instead of values.

Configuration holds a reference (``safe://NAME``); the manifest says in
which store the value of NAME lives and carries its metadata - never the
value. A value is resolved only where it is needed, ideally into the
environment of one child process (``ahabase safe run``), and is never
printed unless the user asks for it explicitly.

Stores:

- ``keyring`` - the operating system's store (macOS Keychain, Secret
  Service, Windows Credential Manager) through the ``keyring`` library;
  the default;
- ``env`` - read-only, from an environment variable (CI);
- ``memory`` - in-process, for tests.

Known limit of the OS store on macOS: any program run by the same
interpreter can read the items it created without a prompt; per-item
access control in Keychain Access narrows it.

Implements: implementation-ahabase-safe-blueprint
Blueprint: implementation-ahabase-safe-blueprint
Blueprint: implementation-ahabase-safe-integration-blueprint

Capability: secrets-store
"""

from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field, fields
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple, Protocol

if sys.platform == "win32":  # pragma: no cover - exercised on the CI Windows lane
    from . import _win as _platform
else:
    from . import _posix as _platform

PREFIX = "safe://"
SERVICE = "ahabase"


class SafeError(Exception):
    """A secret could not be resolved or stored (the message names no value)."""


class Store(Protocol):
    """What every store offers."""

    name: str

    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...
    def exists(self, key: str) -> bool: ...


class MemoryStore:
    """Values in this process only (tests)."""

    name = "memory"

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._values.get(key)

    def set(self, key: str, value: str) -> None:
        self._values[key] = value

    def delete(self, key: str) -> None:
        self._values.pop(key, None)

    def exists(self, key: str) -> bool:
        return key in self._values


class EnvStore:
    """Read-only values from environment variables (the key is the variable)."""

    name = "env"

    def get(self, key: str) -> str | None:
        return os.environ.get(key)

    def set(self, key: str, value: str) -> None:
        raise SafeError("the env store is read-only")

    def delete(self, key: str) -> None:
        raise SafeError("the env store is read-only")

    def exists(self, key: str) -> bool:
        return key in os.environ


class KeyringStore:
    """The operating system's store through the ``keyring`` library."""

    name = "keyring"

    def __init__(self, service: str = SERVICE) -> None:
        self.service = service

    def _keyring(self):
        try:
            import keyring
        except ImportError as error:  # pragma: no cover - dependency present
            raise SafeError("the keyring library is not installed") from error
        return keyring

    def get(self, key: str) -> str | None:
        return self._keyring().get_password(self.service, key)

    def set(self, key: str, value: str) -> None:
        self._keyring().set_password(self.service, key, value)

    def delete(self, key: str) -> None:
        kr = self._keyring()
        try:
            kr.delete_password(self.service, key)
        except kr.errors.PasswordDeleteError:
            pass

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def available(self) -> tuple[bool, str]:
        """Whether a usable OS backend is configured (never reads a value)."""
        try:
            backend = self._keyring().get_keyring()
        except Exception as error:  # noqa: BLE001
            return False, f"{type(error).__name__}: {error}"
        priority = getattr(backend, "priority", 0)
        return priority > 0, f"{type(backend).__module__}.{type(backend).__name__}"


@dataclass
class Entry:
    """One secret of the manifest - metadata only, never the value.

    Capability: secrets-manifest
    """

    store: str = "keyring"
    key: str = ""
    purpose: str = ""
    owner: str = ""
    scope: str = ""
    created: str = ""
    expires: str = ""
    rotated: str = ""
    consumers: list = field(default_factory=list)
    targets: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)


# Executables known by name to run whatever they are given - binding one
# binds nothing (shells, interpreters, known wrappers) - or whose
# destination comes from their arguments (general-purpose network tools).
# Matched by NAME only - the base name (with the OS exec suffix stripped on
# Windows: python.exe -> python) and the name without a version suffix
# (python3.14 -> python), on the bound path and its real target. A
# script of any other name that relays its arguments (`exec "$@"`) is not
# recognized: bind the real program, never a relay (threat model T2).
NOT_BINDABLE = frozenset({
    "sh", "bash", "zsh", "fish", "dash", "ksh", "tcsh", "csh", "pwsh", "powershell", "cmd",
    "env", "xargs", "nohup", "sudo", "doas", "time", "nice", "timeout", "exec",
    "script", "expect", "unbuffer", "watch", "parallel",
    "python", "python2", "python3", "pypy", "pypy3", "node", "nodejs", "deno", "bun",
    "perl", "ruby", "php", "lua", "tclsh", "osascript", "awk", "gawk",
    "curl", "wget", "gh", "git", "ssh", "scp", "sftp", "rsync", "nc", "ncat",
    "socat", "telnet", "ftp", "http", "https", "aws", "gcloud", "az", "kubectl",
    # tools that run commands they are given or offer a shell escape
    "make", "gmake", "find", "tar", "vi", "vim", "nvim", "less", "more", "man",
    "busybox", "toybox", "npm", "npx", "pnpm", "yarn", "pip", "pip3", "uv", "uvx",
    "pipx", "poetry", "docker", "podman", "sqlite3", "screen", "tmux", "emacs",
})

# Options that point a consumer at another configuration or destination;
# refused on a bound command line unless the binding allows them.
REDIRECT_OPTIONS = ("--profiles-dir", "--project-dir", "--config", "--config-file",
                    "--host", "--url", "--endpoint", "--server", "--target")

# What a child of ``safe run`` receives besides the named variables: enough
# to work (locale, terminal, a corporate network's proxy and certificates),
# no other exported value.
BASE_ENV = ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "TMPDIR", "TZ", "LANG",
            "TERM", "COLORTERM", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
            "http_proxy", "https_proxy", "no_proxy", "ALL_PROXY", "all_proxy",
            "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
            "NODE_EXTRA_CA_CERTS", "PIP_CERT")

OVERRIDES = ("AHABASE_SAFE_MANIFEST", "AHABASE_HOME")


def _plain_name(path: str) -> str:
    """The executable's name without a version suffix (python3.14 -> python3)."""
    name = Path(path).name.lower()
    stripped = name.rstrip("0123456789.")
    return stripped or name


def not_bindable_reason(path: str) -> str | None:
    """Why an executable cannot be a consumer, or None.

    Capability: secrets-bind
    """
    for candidate in (path, os.path.realpath(path)):
        base = _platform.exec_base_name(candidate)
        if base in NOT_BINDABLE or _plain_name(base) in NOT_BINDABLE:
            return (f"'{Path(candidate).name}' runs whatever it is given or takes its "
                    "destination from its arguments, so binding it would bind nothing")
    return None


def package_root(path: str) -> str:
    """Where a bound executable's real target must stay.

    A package manager's keg (``.../Cellar/<tool>/<version>/bin/<tool>``)
    moves on every upgrade; inside a keg the root is the tool's directory
    above the version, so the binding survives upgrades. Anywhere else the
    root is the real file itself - a shared ``bin`` directory as root
    would let the bound path be pointed at any other program in it.
    """
    real = Path(os.path.realpath(path))
    parts = real.parts
    if "Cellar" in parts:
        i = parts.index("Cellar")
        if len(parts) > i + 1:
            return str(Path(*parts[: i + 2]))
    return str(real)


def in_keg(root: str) -> bool:
    return "Cellar" in Path(root).parts and not os.path.isfile(root)


def file_digest(path: str) -> str:
    """sha256 of an executable's real file (never of a value)."""
    import hashlib
    digest = hashlib.sha256()
    with open(os.path.realpath(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_tracks_possible(path: Path, tree: Path) -> bool:
    """Whether a file at PATH could be committed in TREE (not git-ignored)."""
    try:
        out = subprocess.run(["git", "-C", str(tree), "check-ignore", "-q", str(path)],
                             capture_output=True)
    except OSError:
        return True  # cannot tell: treat as committable
    return out.returncode != 0


def _valid_binding(binding) -> bool:
    """Whether a stored binding has the shape the checks rely on."""
    if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
        return False
    if any(k in binding and not isinstance(binding[k], str) for k in ("root", "digest")):
        return False
    return all(k not in binding or (isinstance(binding[k], list) and
                                    all(isinstance(v, str) for v in binding[k]))
               for k in ("prefix", "allow", "keep"))


def _valid_target(target) -> bool:
    """Whether a stored target has the shape the checks rely on.

    The shape only: a kind the registry does not know still reads (a
    newer version's manifest must not break this one) - it is named as
    unknown at use, in health and in every refresh. ``copy`` is the one
    structured field: false declares helper scope with no tool copy
    (AHA-0020); every other field is a string.
    """
    if not (isinstance(target, dict) and isinstance(target.get("kind"), str)
            and bool(target["kind"])):
        return False
    if "copy" in target and not isinstance(target["copy"], bool):
        return False
    return all(isinstance(v, str) for k, v in target.items() if k != "copy")


def _same(a: str, b: str) -> bool:
    """Whether two values are equal, compared as digests in constant time
    (rule 8's discipline: no fingerprint of a value leaves the process).

    Capability: secrets-rotate
    """
    return hmac.compare_digest(hashlib.sha256(a.encode()).digest(),
                               hashlib.sha256(b.encode()).digest())


class TargetKind(Protocol):
    """What every target kind offers: a copy of the value in a tool's own
    store - named for messages, parsed from command arguments, written by
    the safe on rotation, read back for presence (health) and for the
    refresh proof (the value), without ever printing."""

    name: str
    usage: str
    # what a failed proof means - the message a refresh reports when the
    # destination does not hold the value (a stale copy passes presence
    # but fails the proof; git accepts a value with no helper configured
    # and writes nothing)
    absence: str

    def parse(self, args: list[str]) -> dict: ...
    def label(self, spec: dict) -> str: ...
    def refresh(self, spec: dict, value: str) -> None: ...
    def present(self, spec: dict) -> bool: ...
    def verify(self, spec: dict, value: str) -> bool: ...


class GitCredentialTarget:
    """A git credential helper's keychain item, written through git itself.

    ``git credential approve`` hands the value to every helper the user
    has configured (osxkeychain, GCM) and updates its item; the value
    travels on stdin, never in an argument list. The destination is read
    back the same way - ``git credential fill``, stdout captured, the
    value read into the checking process and never printed: presence for
    health, the value compared by digest for the refresh proof.
    """

    name = "git-credential"
    usage = "HOST ACCOUNT"
    absence = ("git accepted the value but no stored item answers - either "
               "no credential helper is configured (`git config --get-all "
               "credential.helper`, resolved from the directory the safe "
               "ran in) or a helper is configured whose store holds no item "
               "for this host and account (a locked keychain, an item never "
               "written)")

    def parse(self, args: list[str]) -> dict:
        if len(args) != 2 or not all(a.strip() for a in args):
            raise ValueError(f"{self.name} takes {self.usage} - the host and the "
                             "account of the credential helper's item "
                             "(e.g. github.com octocat)")
        return {"kind": self.name, "host": args[0], "account": args[1]}

    def label(self, spec: dict) -> str:
        return f"{self.name} {spec.get('host', '?')}/{spec.get('account', '?')}"

    def _input(self, spec: dict, value: str | None) -> str:
        lines = ["protocol=https", f"host={spec['host']}", f"username={spec['account']}"]
        if value is not None:
            lines.append(f"password={value}")
        return "\n".join(lines) + "\n"

    def refresh(self, spec: dict, value: str) -> None:
        try:
            out = subprocess.run(["git", "credential", "approve"],
                                 input=self._input(spec, value),
                                 capture_output=True, text=True)
        except OSError as error:
            raise SafeError(f"git could not be run ({type(error).__name__})") from None
        if out.returncode != 0:
            # git's output is dropped, as with compare (rule 8): an error
            # text can carry a credential
            raise SafeError(f"git credential approve failed (exit {out.returncode}) - "
                            "see `git config --get-all credential.helper` for the "
                            "helpers it feeds")

    def _quiet_env(self) -> dict[str, str]:
        # every prompt is disabled: git's own (terminal, askpass - the no-op
        # comes from the platform arm, ``true`` on POSIX, rundll32 on Windows)
        # and GCM's (a GUI dialog during `ahabase doctor` when the item is
        # missing)
        return dict(os.environ, GIT_TERMINAL_PROMPT="0",
                    GIT_ASKPASS=_platform.ASKPASS_NOOP,
                    GCM_INTERACTIVE="never", GCM_GUI="never")

    def _read(self, spec: dict) -> str | None:
        """The value the helper chain holds for the item, read into this
        process - None when no stored item answers (never printed)."""
        try:
            out = subprocess.run(["git", "credential", "fill"],
                                 input=self._input(spec, None),
                                 capture_output=True, text=True,
                                 env=self._quiet_env())
        except OSError:
            return None
        if out.returncode != 0:
            return None
        for line in out.stdout.splitlines():
            if line.startswith("password=") and line != "password=":
                return line[len("password="):]
        return None

    def present(self, spec: dict) -> bool:
        return self._read(spec) is not None

    def verify(self, spec: dict, value: str) -> bool:
        read = self._read(spec)
        return read is not None and _same(read, value)


class GhLoginTarget:
    """A gh CLI login, fed on stdin (``gh auth login --with-token``).

    gh keeps the token in its own store; the safe only writes it there,
    asks ``gh auth status`` whether a login exists (health) and reads
    ``gh auth token`` back for the refresh proof. gh reads the
    environment first (GH_TOKEN and its kin), so the write and the
    checks run without those variables - the target is the login, not
    whatever the environment happens to carry.

    The host's default login; a second account on the same host is the
    distinct kind ``gh-login-account`` (AHA-0022).
    """

    name = "gh-login"
    usage = "[HOSTNAME]"
    absence = ("gh accepted the login but its store does not hold the value - "
               "a login can exist with a different or stale token; run "
               "`gh auth status` by hand")

    _drops = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN",
              "GITHUB_ENTERPRISE_TOKEN")

    def parse(self, args: list[str]) -> dict:
        if len(args) > 1 or (args and not args[0].strip()):
            raise ValueError(f"{self.name} takes {self.usage} - the GitHub hostname, "
                             "github.com when not given")
        return {"kind": self.name, "hostname": args[0] if args else "github.com"}

    def label(self, spec: dict) -> str:
        return f"{self.name} {spec.get('hostname', '?')}"

    def config_dir(self, spec: dict) -> Path | None:
        """The login's own gh config directory; None = gh's default one."""
        return None

    def _gh(self) -> str:
        gh = shutil.which("gh")
        if gh is None:
            raise SafeError("gh is not installed (no gh on PATH)")
        return gh

    def _env(self, spec: dict | None = None) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if k not in self._drops}
        directory = self.config_dir(spec) if spec else None
        if directory is not None:
            env["GH_CONFIG_DIR"] = str(directory)
        return env

    @staticmethod
    def _refuse_plaintext(directory: Path, value: str) -> None:
        """No token may rest in the directory: remove a plaintext one and refuse.

        Primary check by VALUE (the secret's own bytes in any file - a gh
        release renaming the field is still caught); the field-shape check
        stays second, for a foreign or stale token from another source.
        """
        for path in directory.glob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(errors="replace")
            except OSError:
                continue
            if value in text or re.search(r"^\s*oauth_token:\s*\S", text, re.MULTILINE):
                path.unlink()
                raise SafeError(
                    f"gh stored the token in plain text in {path} (no keyring "
                    "available) - the file was removed; make the keyring "
                    "available and refresh the target again")

    def refresh(self, spec: dict, value: str) -> None:
        directory = self.config_dir(spec)
        if directory is not None:
            directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            directory.chmod(0o700)
        out = subprocess.run([self._gh(), "auth", "login", "--hostname",
                              spec["hostname"], "--with-token"],
                             input=value + "\n", capture_output=True, text=True,
                             env=self._env(spec))
        if directory is not None:
            try:
                self._refuse_plaintext(directory, value)
            except SafeError as exc:
                if out.returncode != 0:
                    raise SafeError(f"{exc} (gh auth login itself exited "
                                    f"{out.returncode})") from None
                raise
        if out.returncode != 0:
            raise SafeError(f"gh auth login failed (exit {out.returncode})")

    def present(self, spec: dict) -> bool:
        gh = shutil.which("gh")
        if gh is None:
            return False
        try:
            out = subprocess.run([gh, "auth", "status", "--hostname", spec["hostname"]],
                                 capture_output=True, text=True, env=self._env(spec))
        except OSError:
            return False
        return out.returncode == 0

    def verify(self, spec: dict, value: str) -> bool:
        """``gh auth token`` prints the token - captured, compared by
        digest, dropped; never printed by us."""
        gh = shutil.which("gh")
        if gh is None:
            return False
        try:
            out = subprocess.run([gh, "auth", "token", "--hostname", spec["hostname"]],
                                 capture_output=True, text=True, env=self._env(spec))
        except OSError:
            return False
        if out.returncode != 0:
            return False
        read = out.stdout.strip()
        return bool(read) and _same(read, value)


class GhLoginAccountTarget(GhLoginTarget):
    """AHA-0022: a gh login of one ACCOUNT, in its own gh config directory.

    One instance can hold two accounts on one host; gh keeps one login
    per host in one config directory, so each account's login lives in
    ``<workspace>/_config/ahabase-gh/<ACCOUNT>`` (owner-only), and every
    gh call of the target runs with ``GH_CONFIG_DIR`` set to it - a
    caller selects the account the same way (``ahabase safe
    gh-config-dir ACCOUNT`` names the directory). A distinct kind, not a
    field on ``gh-login``: an older reader of the manifest refuses an
    unknown kind, where it would ignore an extra field and write the
    account's token into the host's DEFAULT login (home-5235 F1). The
    token stays in the keyring; a plaintext copy gh wrote is removed and
    refused.
    """

    name = "gh-login-account"
    usage = "HOSTNAME ACCOUNT"

    _account_re = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_-]{0,38})")

    def parse(self, args: list[str]) -> dict:
        if len(args) != 2 or any(not a.strip() for a in args):
            raise ValueError(f"{self.name} takes {self.usage} - the GitHub hostname "
                             "and the account whose login this is")
        if not self._account_re.fullmatch(args[1]):
            raise ValueError(f"{args[1]!r} is no GitHub account name")
        return {"kind": self.name, "hostname": args[0], "account": args[1]}

    def label(self, spec: dict) -> str:
        return f"{self.name} {spec.get('hostname', '?')} {spec.get('account', '?')}"

    def config_dir(self, spec: dict) -> Path | None:
        return gh_config_dir(spec["account"])


def gh_config_dir(account: str) -> Path:
    """The gh config directory of an account's login (AHA-0022) - the one
    place the path is formed; callers ask ``ahabase safe gh-config-dir``."""
    if not GhLoginAccountTarget._account_re.fullmatch(account):
        raise SafeError(f"{account!r} is no GitHub account name")
    return workspace() / "_config" / "ahabase-gh" / account


# the kinds the CLI offers; a seam for tests (a test registers a fake kind)
TARGET_KINDS: dict[str, TargetKind] = {
    "git-credential": GitCredentialTarget(),
    "gh-login": GhLoginTarget(),
    "gh-login-account": GhLoginAccountTarget(),
}


def target_label(spec: dict) -> str:
    """A target's name for messages; an unknown kind is still named."""
    impl = TARGET_KINDS.get(spec.get("kind", ""))
    return impl.label(spec) if impl else f"{spec.get('kind', '?')} (unknown kind)"


def _same_target(stored: dict, spec: dict) -> bool:
    """Whether two target specs name the same target: equality on every
    field but ``copy`` - the custody mode never blocks removal (a spec
    typed without the flag still withdraws the variant added with it)."""
    return {k: v for k, v in stored.items() if k != "copy"} \
        == {k: v for k, v in spec.items() if k != "copy"}


class Rotation(NamedTuple):
    """What one ``set`` did: the entry, the targets refreshed, the
    scope-only ones (nothing was written for them), and the ones it could
    not reach - (label, reason), never a value."""

    entry: Entry
    refreshed: list
    scope: list
    failed: list


def overrides_set() -> list[str]:
    """The safe's override variables present in the environment."""
    return [name for name in OVERRIDES if os.environ.get(name)]


def inside_git_tree(path: Path) -> Path | None:
    """The git working tree a path lies in, or None."""
    for parent in [path.parent, *path.parent.parents]:
        if (parent / ".git").exists():
            return parent
    return None


def child_env(named: dict[str, str], keep: tuple[str, ...] = ()) -> dict[str, str]:
    """The environment of a ``safe run`` child: the base, kept names, the named values."""
    env = {k: v for k, v in os.environ.items() if k in BASE_ENV or k.startswith("LC_")}
    for name in keep:
        if name in os.environ:
            env[name] = os.environ[name]
    env.update(named)
    return env


def workspace() -> Path:
    """The workspace root: ``AHABASE_HOME``, else ``~/ahabase``."""
    return Path(os.environ.get("AHABASE_HOME", Path.home() / "ahabase"))


def manifest_path() -> Path:
    """Where the manifest lives (``AHABASE_SAFE_MANIFEST`` overrides)."""
    override = os.environ.get("AHABASE_SAFE_MANIFEST")
    return Path(override) if override else workspace() / "_config" / "safe.json"


# git's credential-helper verbs; `capability` (git 2.46+) is answered
# empty - this helper offers none
CREDENTIAL_VERBS = ("get", "store", "erase", "capability")


def parse_credential_request(text: str) -> dict:
    """git's credential-helper request (key=value lines) as a dict.

    Split on the first ``=`` of each line (a value may contain ``=``);
    a repeated key keeps its first value (git sends none twice). A
    ``url`` line carries the parts when git did not split them itself;
    the host is lowercased - targets match on the lowercase form.

    Capability: secrets-door (git's side)
    """
    out: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        key = key.strip()
        if sep and key and key not in out:
            out[key] = value
    if out.get("url") and "host" not in out:
        from urllib.parse import urlsplit
        parts = urlsplit(out["url"])
        if parts.scheme:
            out.setdefault("protocol", parts.scheme)
        if parts.hostname:
            out.setdefault("host", parts.hostname.lower())
        if parts.username:
            out.setdefault("username", parts.username)
    if "host" in out:
        out["host"] = out["host"].lower()
    return out


class Safe:
    """The service: a manifest plus the stores it names."""

    def __init__(self, path: Path | None = None,
                 stores: dict[str, Store] | None = None) -> None:
        self.path = path or manifest_path()
        self.stores: dict[str, Store] = stores or {
            "keyring": KeyringStore(), "env": EnvStore(), "memory": MemoryStore()}

    # manifest ---------------------------------------------------------
    def entries(self) -> dict[str, Entry]:
        """The manifest's entries (empty when no manifest exists)."""
        if not self.path.exists():
            return {}
        way = (f"move {self.path} aside and set the entries again, or repair it "
               f"(its entries are names and metadata only)")
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            secrets = raw.get("secrets", {})
            if not isinstance(secrets, dict):
                raise ValueError("'secrets' is not an object")
        except (OSError, ValueError, AttributeError) as error:
            raise SafeError(f"the manifest {self.path} cannot be read "
                            f"({type(error).__name__}) - {way}") from None
        known = {f.name for f in fields(Entry)} - {"extra"}
        entries: dict[str, Entry] = {}
        for name, data in secrets.items():
            # the stored value is checked, not a default: a falsy wrong type
            # (0, null, "") is as malformed as any other
            if not isinstance(data, dict) \
                    or ("extra" in data and not isinstance(data["extra"], dict)) \
                    or ("consumers" in data and not (isinstance(data["consumers"], list)
                                                     and all(_valid_binding(c)
                                                             for c in data["consumers"]))) \
                    or ("targets" in data and not (isinstance(data["targets"], list)
                                                   and all(_valid_target(t)
                                                           for t in data["targets"]))) \
                    or any(k in data and not isinstance(data[k], str) for k in
                           ("store", "key", "purpose", "owner", "scope", "created",
                            "expires", "rotated")):
                raise SafeError(f"the manifest entry '{name}' is malformed - {way}")
            extra = dict(data.get("extra") or {})
            extra.update({k: v for k, v in data.items() if k not in known and k != "extra"})
            entries[name] = Entry(**{k: v for k, v in data.items() if k in known}, extra=extra)
        return entries

    @contextlib.contextmanager
    def _locked(self):
        """An exclusive lock around a read-modify-write of the manifest.

        Concurrent ``set``/``delete`` calls (several sessions, several
        processes) serialize here, so none loses another's entry and no
        store item is left without its manifest entry (review e31fe5ad).
        The lock itself is ``filelock``'s (flock on POSIX, msvcrt on
        Windows), so it holds on every OS and dies with the process.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(self.path.name + ".lock")
        with _platform.lock(lock_path):
            yield

    def _save(self, entries: dict[str, Entry]) -> None:
        """Write the manifest atomically, mode 600 from the first byte.

        A unique temporary file in the same directory (``mkstemp`` creates
        it 0600), flushed to disk, then renamed over the manifest. Never
        inside a git working tree: the manifest is the target map.
        """
        tree = inside_git_tree(self.path)
        if tree is not None and git_tracks_possible(self.path, tree):
            raise SafeError(f"refusing to write the manifest inside the git working tree "
                            f"{tree}, where it is not ignored - it would be one commit "
                            f"away from leaving the instance; ignore it there "
                            f"(add '{self.path.name}' to that tree's .gitignore) or keep "
                            f"the workspace outside the tree")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"secrets": {n: asdict(e) for n, e in sorted(entries.items())}}
        fd, tmp = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(data, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.path)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(tmp)
            raise

    def _store(self, entry: Entry) -> Store:
        try:
            return self.stores[entry.store]
        except KeyError:
            raise SafeError(f"unknown store '{entry.store}'") from None

    # operations -------------------------------------------------------
    def set(self, name: str, value: str, store: str = "keyring", **meta: str) -> Rotation:
        """Store a value and record (or update) its manifest entry.

        Setting an existing name records the day as its last rotation and
        refreshes the entry's targets - the one place a rotation happens
        (rule 7). A target that could not be refreshed is named in the
        result, never silently skipped; the value is stored regardless,
        so it is never lost to a target's failure.
        """
        if not value:
            raise SafeError(f"empty value for '{name}' - nothing stored")
        with self._locked():
            entries = self.entries()
            today = date.today().isoformat()
            entry = entries.get(name) or Entry(store=store, key=name, created=today)
            if name in entries:
                entry.rotated = today
            for k, v in meta.items():
                if v and hasattr(entry, k):
                    setattr(entry, k, v)
            self._store(entry).set(entry.key or name, value)
            entries[name] = entry
            self._save(entries)
        # outside the lock: a target's helper (gh) may take seconds, and no
        # manifest write waits on it
        refreshed, scope, failed = self._refresh_targets(entry, value)
        return Rotation(entry, refreshed, scope, failed)

    def get(self, name: str) -> str:
        """The value of a secret; an error names the secret, never a value."""
        entry = self.entries().get(name)
        if entry is None:
            raise SafeError(f"no secret '{name}' in the manifest {self.path}")
        value = self._store(entry).get(entry.key or name)
        if value is None:
            raise SafeError(f"secret '{name}' is in the manifest but not in its "
                            f"store '{entry.store}'")
        return value

    def delete(self, name: str) -> None:
        """Remove a secret from its store and from the manifest."""
        with self._locked():
            entries = self.entries()
            entry = entries.pop(name, None)
            if entry is None:
                raise SafeError(f"no secret '{name}' in the manifest {self.path}")
            self._store(entry).delete(entry.key or name)
            self._save(entries)

    # git's credential helper --------------------------------------------
    def credential(self, request: dict) -> dict | None:
        """The credential-helper answer for a request: the value of the
        entry whose ``git-credential`` target names the request's host
        (and its account, when the request carries a username) - None
        when the safe holds nothing for the host, the helper's contract
        to answer nothing.

        The helper is a read surface: the value crosses only the
        helper's stdout pipe to git, and it enters the safe only through
        ``set`` by the owner (``store``/``erase`` never reach this
        method - the CLI fails them soft). One entry per host: entries
        are visited in name order and the first matching target answers
        (a second github.com account is a second secret with its own
        target - selected by the request's username, never overloading
        the first).

        Capability: secrets-door (git's side)
        """
        host = request.get("host", "")
        username = request.get("username")
        for name, entry in sorted(self.entries().items()):
            for spec in entry.targets:
                if spec.get("kind") != "git-credential" \
                        or spec.get("host", "").lower() != host:
                    continue
                if username is not None and spec.get("account", "") != username:
                    continue
                value = self._store(entry).get(entry.key or name)
                if value is None:
                    raise SafeError(f"secret '{name}' is in the manifest but not in "
                                    f"its store '{entry.store}' - the helper answers "
                                    f"nothing until its owner stores it: ahabase "
                                    f"safe set {name}")
                return {"username": spec.get("account", ""), "password": value}
        return None

    # consumer binding -------------------------------------------------
    def bind(self, name: str, command: str, prefix: tuple[str, ...] = (),
             allow: tuple[str, ...] = (), keep: tuple[str, ...] = ()) -> dict:
        """Allow an executable, by its absolute path, to receive NAME."""
        if not os.path.isabs(command) or ".." in Path(command).parts:
            raise SafeError(f"bind '{name}' by an absolute path without '..' (e.g. the "
                            f"output of `command -v {Path(command).name}`)")
        if shutil.which(command) is None:
            raise SafeError(f"'{command}' is not an executable file")
        reason = not_bindable_reason(command)
        if reason:
            raise SafeError(f"cannot bind '{name}' to {command}: {reason}; bind the "
                            f"installed command that takes its destination from its "
                            f"own configuration")
        root = package_root(command)
        binding = {"path": os.path.normpath(command), "root": root, "prefix": list(prefix),
                   "allow": list(allow), "keep": list(keep),
                   # outside a keg the real file is pinned by its digest
                   "digest": "" if in_keg(root) else file_digest(command)}
        with self._locked():
            entries = self.entries()
            entry = entries.get(name)
            if entry is None:
                raise SafeError(f"no secret '{name}' in the manifest {self.path}")
            entry.consumers = [c for c in entry.consumers if c.get("path") != binding["path"]]
            entry.consumers.append(binding)
            self._save(entries)
        return binding

    def unbind(self, name: str, command: str) -> None:
        """Withdraw an executable's binding to NAME."""
        with self._locked():
            entries = self.entries()
            entry = entries.get(name)
            if entry is None:
                raise SafeError(f"no secret '{name}' in the manifest {self.path}")
            path = os.path.normpath(command)
            before = len(entry.consumers)
            entry.consumers = [c for c in entry.consumers if c.get("path") != path]
            if len(entry.consumers) == before:
                raise SafeError(f"'{path}' is not bound to '{name}'")
            self._save(entries)

    # targets -----------------------------------------------------------
    def target_add(self, name: str, spec: dict) -> dict | None:
        """Record a target on NAME - the safe refreshes it on every set.

        One target has one custody mode: adding a spec that names an
        already-declared target (same kind and fields, whatever their
        ``copy``) replaces the stored one - the modes never coexist, so
        one rotation never names the same target as both refreshed and
        scope-only. Returns the replaced spec, or None when the target
        is new (an identical spec changes nothing)."""
        if not _valid_target(spec):
            raise SafeError(f"the target of '{name}' is malformed")
        with self._locked():
            entries = self.entries()
            entry = entries.get(name)
            if entry is None:
                raise SafeError(f"no secret '{name}' in the manifest {self.path}")
            replaced = next((t for t in entry.targets if _same_target(t, spec)), None)
            if replaced is not None and replaced == spec:
                return replaced  # adding twice is one target - nothing changed
            entry.targets = [spec if _same_target(t, spec) else t
                             for t in entry.targets]
            if replaced is None:
                entry.targets.append(spec)
            self._save(entries)
        return replaced

    def target_remove(self, name: str, spec: dict) -> str:
        """Withdraw a target from NAME; returns the removed target's label."""
        with self._locked():
            entries = self.entries()
            entry = entries.get(name)
            if entry is None:
                raise SafeError(f"no secret '{name}' in the manifest {self.path}")
            before = len(entry.targets)
            entry.targets = [t for t in entry.targets if not _same_target(t, spec)]
            if len(entry.targets) == before:
                have = ", ".join(target_label(t) for t in entry.targets) or "none"
                raise SafeError(f"'{name}' has no such target - its targets: {have}")
            self._save(entries)
        return target_label(spec)

    def refresh(self, name: str) -> tuple[list[str], list[str], list[tuple[str, str]]]:
        """Rewrite every target of NAME from the stored value.

        What ``set`` does to the targets - the remedy after a rotation
        could not reach one of them. Scope-only targets are named as such
        (nothing is written for them). The value is read in-process and
        never printed; a failing target is named in the result, not
        raised past, so one broken target blocks none of the others.
        """
        entries = self.entries()
        entry = entries.get(name)
        if entry is None:
            raise SafeError(f"no secret '{name}' in the manifest {self.path}")
        return self._refresh_targets(entry, self.get(name))

    def _refresh_targets(self, entry: Entry, value: str) -> tuple[list, list, list]:
        refreshed: list[str] = []
        scope: list[str] = []
        failed: list[tuple[str, str]] = []
        for spec in entry.targets:
            if spec.get("copy") is False:
                # scope-only: the declaration grants the helper's host
                # scope and nothing else - there is no copy to write
                scope.append(target_label(spec))
                continue
            impl = TARGET_KINDS.get(spec.get("kind", ""))
            if impl is None:
                failed.append((target_label(spec),
                               f"unknown target kind '{spec.get('kind', '')}' - "
                               "remove it: ahabase safe target remove"))
                continue
            try:
                impl.refresh(spec, value)
                proven = impl.verify(spec, value)
            except Exception as error:  # noqa: BLE001 - reported, never swallowed
                failed.append((impl.label(spec),
                               str(error) or type(error).__name__))
            else:
                if proven:
                    refreshed.append(impl.label(spec))
                else:
                    # a write is proven by reading the destination back -
                    # presence alone can be a stale copy
                    failed.append((impl.label(spec), impl.absence))
        return refreshed, scope, failed

    def check_consumer(self, name: str, argv: list[str]) -> dict:
        """Refuse, before any value is read, a command not bound to NAME.

        The command must be one of the entry's bound paths exactly as
        bound - no '..', an earlier executable on PATH does not match -
        and the returned binding's ``path`` is what is executed, so the
        checked string and the executed one are the same. Its real target
        must stay inside the recorded root: a package manager's keg (it may
        move with an upgrade) or, anywhere else, the very file, unchanged
        since binding (digest). The real target is checked again for being
        a shell, an interpreter or a wrapper. Its arguments must start with
        the bound prefix, and no option - nor an abbreviation of one - may
        redirect it unless allowed. Every refusal names the command that
        proceeds.
        """
        entry = self.entries().get(name)
        if entry is None:
            raise SafeError(f"no secret '{name}' in the manifest {self.path}")
        if not argv:
            raise SafeError("no command to run")
        command = argv[0]
        if ".." in Path(command).parts:
            raise SafeError(f"'{command}' contains '..' - call the bound consumer by "
                            f"the path it was bound with")
        if not os.path.isabs(command):
            found = shutil.which(command)
            if found is None:
                raise SafeError(f"'{command}' is not found on PATH")
            command = found
        command = os.path.normpath(command)
        binding = next((c for c in entry.consumers if c.get("path") == command), None)
        if binding is None:
            hint = f"ahabase safe bind {name} {command}"
            raise SafeError(f"'{command}' is not a bound consumer of '{name}' - nothing "
                            f"resolved; if it should receive it, its owner runs: {hint}")
        rebind = f"ahabase safe bind {name} {command}"
        if shutil.which(command) is None:
            raise SafeError(f"bound consumer '{command}' no longer exists or is not "
                            f"executable - reinstall it, or rebind ({rebind}) or unbind "
                            f"(ahabase safe unbind {name} {command}) it")
        real = os.path.realpath(command)
        root = binding.get("root", "")
        if in_keg(root):
            if not real.startswith(root.rstrip(os.sep) + os.sep):
                raise SafeError(f"'{command}' now leads to {real}, outside its bound "
                                f"package {root} - if this is intended: {rebind}")
        else:
            if real != root:
                raise SafeError(f"'{command}' now leads to {real}, not the file it was "
                                f"bound to ({root}) - if this is intended: {rebind}")
            if binding.get("digest") and file_digest(command) != binding["digest"]:
                raise SafeError(f"'{command}' changed since it was bound (an update, or "
                                f"a replacement) - if the change is yours: {rebind}")
        reason = not_bindable_reason(real)
        if reason:
            raise SafeError(f"'{command}' now leads to {real}: {reason}")
        prefix = binding.get("prefix") or []
        if argv[1:1 + len(prefix)] != prefix:
            raise SafeError(f"'{command}' is bound to '{name}' only with the arguments "
                            f"{' '.join(prefix)} first")
        allow = set(binding.get("allow") or [])
        for arg in argv[1:]:
            option = arg.split("=", 1)[0]
            if not option.startswith("--") or option == "--":
                continue
            if option in REDIRECT_OPTIONS:  # a full option is itself, not a prefix
                hits = [option]
            else:
                # argparse accepts any unique prefix, one letter included (--u)
                hits = [r for r in REDIRECT_OPTIONS if len(option) > 2 and r.startswith(option)]
            for hit in hits:
                if hit not in allow:
                    raise SafeError(f"'{option}' would point '{command}' elsewhere "
                                    f"({hit}); it is refused unless the binding allows "
                                    f"it: {rebind} --allow {hit}")
        return {**binding, "path": command}

    def resolve(self, value: str) -> str:
        """A reference becomes its value; any other value passes unchanged.

        The pass-through lets a consumer switch to references one setting
        at a time.
        """
        if isinstance(value, str) and value.startswith(PREFIX):
            return self.get(value[len(PREFIX):])
        return value

    def health(self, warn_days: int = 14) -> list[tuple[bool, str]]:
        """Problems of the manifest: missing values, expiry (no value shown)."""
        out: list[tuple[bool, str]] = []
        today = date.today()
        soon = today + timedelta(days=warn_days)
        for name, entry in sorted(self.entries().items()):
            try:
                present = self._store(entry).exists(entry.key or name)
            except Exception as error:  # noqa: BLE001
                out.append((False, f"{name}: store '{entry.store}' failed: "
                                   f"{type(error).__name__}"))
                continue
            if not present:
                out.append((False, f"{name}: missing in store '{entry.store}'"))
            for spec in entry.targets:
                if spec.get("copy") is False:
                    continue  # scope-only: no copy exists to be missing
                label = target_label(spec)
                impl = TARGET_KINDS.get(spec.get("kind", ""))
                if impl is None:
                    out.append((False, f"{name}: target {label} - remove it: ahabase "
                                       "safe target remove"))
                    continue
                try:
                    there = impl.present(spec)
                except Exception:  # noqa: BLE001 - presence, not the reason
                    there = False
                if not there:
                    out.append((False, f"{name}: target {label} is not there - refresh "
                                       f"it: ahabase safe refresh {name}"))
            for binding in entry.consumers:
                path = binding.get("path", "")
                if shutil.which(path) is None:
                    out.append((False, f"{name}: bound consumer {path} no longer exists - "
                                       f"rebind or unbind it"))
                elif binding.get("digest") and file_digest(path) != binding["digest"]:
                    out.append((False, f"{name}: bound consumer {path} changed since it "
                                       f"was bound - if the change is yours, rebind it: "
                                       f"ahabase safe bind {name} {path}"))
            if entry.expires:
                try:
                    expires = date.fromisoformat(entry.expires)
                except ValueError:
                    out.append((False, f"{name}: unreadable expiry '{entry.expires}'"))
                    continue
                if expires < today:
                    out.append((False, f"{name}: expired {entry.expires}"))
                elif expires <= soon:
                    out.append((False, f"{name}: expires {entry.expires} "
                                       f"(within {warn_days} days)"))
        return out
