"""Access paths: definitions, authentication, the ladder and the identity in force.

Capability: llm-paths

An access path is a named route to a language model: an endpoint, the model
it serves (optionally one per tier) and how it authenticates. This module
holds what a path IS, how its authentication resolves, in which order paths
are tried when one fails (the ladder) and which path the tool currently
points at. Verification, the settings switch and the session payload live in
their own modules.

Authentication is never a literal value. A path's ``auth`` is one of:

- ``safe://NAME`` - a reference to a value in the safe; resolved only after
  the running command proves to be the consumer its owner bound;
- ``env:NAME`` - a variable the safe (or the owner's shell) injects into the
  consumer process;
- ``oauth`` - the tool's subscription login (presence is checked, never read);
- ``aws-credentials`` - the cloud provider's own credential chain (presence
  is checked, never read);
- a ``key_helper`` command - what the tool runs to obtain the key.

Anything else is a literal credential and is refused by name of the path,
never echoed.

Implements: implementation-ahabase-llm-blueprint
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml

from ..config import get_workspace_dir

SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
CREDENTIALS_PATH = Path.home() / ".claude" / ".credentials.json"
KEYCHAIN_SERVICE = "Claude Code-credentials"
AWS_CREDENTIALS_PATH = Path.home() / ".aws" / "credentials"
AWS_SSO_CACHE_PATH = Path.home() / ".aws" / "sso" / "cache"
BEDROCK_FLAG = "CLAUDE_CODE_USE_BEDROCK"
VARIANTS_FILENAME = "llm-paths-variants.yaml"
SAFE_PREFIX = "safe://"
HELPER_TIMEOUT = 15  # seconds for a key helper command

# Model tiers the tool names in its settings (ANTHROPIC_DEFAULT_<TIER>_MODEL).
TIERS = ("SONNET", "OPUS", "HAIKU", "FABLE")

# Env keys the subscription route REMOVES when the tool is switched to it: a
# set override of any of these makes the tool skip its subscription login.
OAUTH_REMOVED_KEYS = (
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_MODEL",
) + tuple(f"ANTHROPIC_DEFAULT_{tier}_MODEL" for tier in TIERS)

# Every env key that decides the connection; a launch proof states them all so
# that neither the machine settings nor the shell's exports decide for it.
CONNECTION_ENV_KEYS = (BEDROCK_FLAG,) + OAUTH_REMOVED_KEYS

# Authentication markers that carry no token: the credential is the tool's own
# login or the provider's chain, and only its presence is checked.
NON_TOKEN_AUTH = ("oauth", "aws-credentials")


class AuthError(ValueError):
    """An authentication spec that cannot be used; the message never holds a value."""


def auth_form(spec: str) -> str:
    """The kind of an auth spec: safe, env, oauth, aws-credentials, none or literal.

    Capability: llm-paths
    """
    if not spec:
        return "none"
    if spec in NON_TOKEN_AUTH:
        return spec
    if spec.startswith(SAFE_PREFIX):
        return "safe"
    if spec.startswith("env:"):
        return "env"
    return "literal"


def check_definition(path_id: str, definition: dict) -> None:
    """Refuse a definition whose auth is a literal credential.

    Capability: llm-paths

    The message names the path and the fix; it never contains the value.
    """
    if auth_form(str(definition.get("auth", ""))) == "literal":
        raise AuthError(
            f"{path_id}: the auth is a literal credential - use 'safe://NAME', "
            f"'env:NAME', 'oauth', 'aws-credentials' or a key_helper")


def variants_path(variants_file: Optional[Path] = None) -> Path:
    """Where the instance's own path variants live (outside git)."""
    if variants_file is not None:
        return Path(variants_file)
    return get_workspace_dir() / "_config" / VARIANTS_FILENAME


def load_variants(variants_file: Optional[Path] = None) -> dict:
    """Load the instance's path variants (empty when the file is missing or unreadable).

    Capability: llm-paths

    An entry marked ``status: available`` becomes a definition; it may carry
    ``tier_models``, a ``key_helper``, a ``provider``, a ``pin_model``, a
    ``context_window`` (the model's window, used for the launch warning), and for the cloud route a
    ``region`` and an ``aws_profile``. A
    definition with a literal credential raises :class:`AuthError`.
    """
    path = variants_path(variants_file)
    if not path.exists():
        return {}
    try:
        with open(path) as handle:
            config = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return {}
    result: dict = {}
    for path_id, definition in (config.get("paths") or {}).items():
        if (definition or {}).get("status") != "available":
            continue
        entry = {
            "base_url": definition.get("base_url", ""),
            "model": definition.get("model", ""),
            "auth": definition.get("auth", "aws-credentials"),
            "description": definition.get("description", f"Config path {path_id}"),
        }
        for optional in ("tier_models", "key_helper", "provider", "pin_model", "context_window",
                         "region", "aws_profile"):
            if definition.get(optional):
                entry[optional] = definition[optional]
        check_definition(path_id, entry)
        result[path_id] = entry
    return result


def native_paths() -> dict:
    """The routes the tool itself provides: the subscription login and the cloud provider's route."""
    return {
        "claude-pro": {
            "base_url": "",
            "model": "",
            "auth": "oauth",
            "description": "Subscription plan through the tool's own login "
                           "(environment overrides cleared)",
        },
        "bedrock": {
            "base_url": "",
            "model": "",
            "auth": "aws-credentials",
            "description": "Cloud provider's native route (managed model defaults)",
        },
    }


def known_paths(builtin: Optional[dict] = None,
                variants_file: Optional[Path] = None) -> dict:
    """The access path definitions: native routes, then the caller's own, then the instance's variants.

    Capability: llm-paths

    ``builtin`` is the caller's provider entries (path id -> definition); the
    package ships none, so the choice of providers stays with the method. A
    later source overrides an earlier one with the same id. A definition with
    a literal credential raises :class:`AuthError`.
    """
    definitions = dict(native_paths())
    for path_id, definition in (builtin or {}).items():
        check_definition(path_id, definition)
        definitions[path_id] = definition
    definitions.update(load_variants(variants_file))
    return definitions


def rescue_order(variants_file: Optional[Path] = None) -> list[str]:
    """The order in which a failed connection tries the paths.

    Capability: llm-paths

    ``meta.rescue_order`` of the instance's variants names it; with none, the
    instance's own available variants in file order. Unknown or unavailable
    ids are dropped by the caller's verification.
    """
    try:
        config = yaml.safe_load(variants_path(variants_file).read_text()) or {}
    except (OSError, yaml.YAMLError):
        return []
    named = (config.get("meta") or {}).get("rescue_order") or []
    if named:
        return [str(p) for p in named]
    return [pid for pid, d in (config.get("paths") or {}).items()
            if (d or {}).get("status") == "available"]


def pin_error(path_id: str, definition: Optional[dict]) -> Optional[str]:
    """Why a path's ``pin_model`` cannot be honoured, or None when it can (or is not set).

    Capability: llm-paths

    A pin needs an endpoint (a route native to the tool has no start model to
    pin) and a ``model`` to pin. The message names the fix: the definition.
    """
    definition = definition or {}
    if not definition.get("pin_model"):
        return None
    if not definition.get("base_url"):
        return (f"{path_id}: pin_model applies to endpoint paths only - "
                f"remove 'pin_model' for {path_id} in its definition")
    if not definition.get("model"):
        return (f"{path_id}: pin_model needs a model - add 'model:' or "
                f"remove 'pin_model' for {path_id} in its definition")
    return None


def pinned_model(definition: Optional[dict], model: Optional[str] = None) -> str:
    """The model a path starts a session on: its own when pinned, else empty.

    Capability: llm-paths

    Empty stays the default: a pinned path states its own model so the session
    starts on it, and the tier models are written as before so the model can
    still be switched in the session. An explicit ``model`` wins.
    """
    definition = definition or {}
    if not definition.get("pin_model"):
        return ""
    return model or definition.get("model") or ""


def resolve_auth(spec: str, env: Optional[dict] = None, *,
                 argv: Optional[list] = None, safe=None) -> Optional[str]:
    """Resolve an auth spec to a token, or None when the credential is the tool's own login.

    Capability: llm-paths

    ``env:NAME`` reads the variable from ``env`` (the process environment by
    default). ``safe://NAME`` is resolved only after the safe confirms that
    the running command is the consumer bound to NAME (``argv`` defaults to
    this command line); a refusal raises :class:`AuthError` with the owner
    step. ``oauth`` and ``aws-credentials`` carry no token (None). A literal
    raises :class:`AuthError`; the value is never echoed.
    """
    form = auth_form(spec)
    if form in ("none", "oauth", "aws-credentials"):
        return None
    if form == "env":
        env = env if env is not None else os.environ
        return env.get(spec[4:]) or None
    if form == "safe":
        name = spec[len(SAFE_PREFIX):]
        from ..safe import Safe, SafeError  # imported late: the safe is optional here
        service = safe if safe is not None else Safe()
        command = [os.path.abspath(sys.argv[0]), *sys.argv[1:]] if argv is None else list(argv)
        try:
            service.check_consumer(name, command)
            return service.get(name)
        except SafeError as error:
            raise AuthError(f"safe://{name} is not available to this command: {error}") from None
    raise AuthError("the auth is a literal credential - refused")


def resolve_key(definition: dict, env: Optional[dict] = None, *,
                argv: Optional[list] = None, safe=None) -> Optional[str]:
    """The key a path authenticates with, obtained the way the tool will.

    Capability: llm-paths

    A path with a ``key_helper`` gets its key from that command (the tool's
    ``apiKeyHelper``), so the check runs the same command; any other path
    resolves its ``auth`` spec. The value is returned to the caller only -
    never printed or logged here.
    """
    helper = definition.get("key_helper")
    if not helper:
        return resolve_auth(definition.get("auth", ""), env, argv=argv, safe=safe)
    try:
        proc = subprocess.run(helper, shell=True, capture_output=True, text=True,
                              timeout=HELPER_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    key = proc.stdout.strip() if proc.returncode == 0 else ""
    return key or None


def _keychain_login_present(service: Optional[str] = None) -> bool:
    """True when the macOS login keychain carries the credentials entry (presence only)."""
    try:
        proc = subprocess.run(
            ["security", "find-generic-password", "-s", service or KEYCHAIN_SERVICE],
            capture_output=True, timeout=5, check=False)
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def subscription_login_source() -> Optional[str]:
    """Which place holds the subscription login, if any (a human-readable source or None).

    Capability: llm-paths

    Two homes, either satisfies: the credentials file and, on macOS, the login
    keychain entry. Presence only - the secret value is never read.
    """
    if CREDENTIALS_PATH.exists():
        return f"file: {CREDENTIALS_PATH}"
    if sys.platform == "darwin" and _keychain_login_present():
        return f"macOS keychain: {KEYCHAIN_SERVICE}"
    return None


def subscription_login_present() -> bool:
    """True when the subscription login is discoverable.

    Capability: llm-paths
    """
    return subscription_login_source() is not None


def bedrock_credentials_source(env: Optional[dict] = None) -> Optional[str]:
    """Which place holds cloud-provider credentials for the native route, if any.

    Capability: llm-paths

    Presence only, in the order the provider's own chain resolves them: the
    environment, the shared credentials file (its text is read to test that it
    is non-empty and discarded), then the single-sign-on cache. The value is
    never returned, logged or persisted.
    """
    env = env if env is not None else os.environ
    if env.get("AWS_ACCESS_KEY_ID"):
        return "env: AWS_ACCESS_KEY_ID"
    try:
        if AWS_CREDENTIALS_PATH.is_file() and AWS_CREDENTIALS_PATH.read_text().strip():
            return f"file: {AWS_CREDENTIALS_PATH}"
    except OSError:
        pass
    try:
        if AWS_SSO_CACHE_PATH.is_dir() and any(AWS_SSO_CACHE_PATH.glob("*.json")):
            return f"sso cache: {AWS_SSO_CACHE_PATH}"
    except OSError:
        pass
    return None


def bedrock_credentials_present() -> bool:
    """True when the cloud provider's credential chain has any leg.

    Capability: llm-paths
    """
    return bedrock_credentials_source() is not None


def settings_env() -> dict:
    """The env section of the tool's settings (empty when absent)."""
    try:
        with open(SETTINGS_PATH) as handle:
            return json.load(handle).get("env", {})
    except (OSError, json.JSONDecodeError):
        return {}


def current_path(env: Optional[dict] = None, *, builtin: Optional[dict] = None,
                 variants_file: Optional[Path] = None) -> str:
    """Identify which access path the tool's environment currently points to.

    Capability: llm-paths

    The cloud-native flag (``CLAUDE_CODE_USE_BEDROCK`` truthy) wins first; with
    a model set it resolves a variant whose auth is ``aws-credentials``. An
    empty ``ANTHROPIC_BASE_URL`` is the subscription route. Several paths may
    share one base address, so a multi-candidate match is disambiguated by the
    model the switch wrote for the SONNET tier; no match falls back to the
    first candidate. ``custom`` and ``none`` are the non-listed fallbacks.
    """
    state = env if env is not None else settings_env()
    bedrock_val = (state[BEDROCK_FLAG] if BEDROCK_FLAG in state
                   else os.environ.get(BEDROCK_FLAG, ""))
    if str(bedrock_val).lower() in ("1", "true", "yes"):
        model = (state["ANTHROPIC_MODEL"] if "ANTHROPIC_MODEL" in state
                 else os.environ.get("ANTHROPIC_MODEL", ""))
        if model:
            for path_id, definition in known_paths(builtin, variants_file).items():
                if definition.get("auth") == "aws-credentials" and definition.get("model") == model:
                    return path_id
        return "bedrock"
    base_url = state.get("ANTHROPIC_BASE_URL", "")
    paths = known_paths(builtin, variants_file)
    candidates = [path_id for path_id, definition in paths.items()
                  if base_url == definition["base_url"]]
    if not candidates:
        return "custom" if base_url else "none"
    if len(candidates) == 1:
        return candidates[0]
    current_model = state.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "")
    for path_id in candidates:
        written = (paths[path_id].get("tier_models") or {}).get("SONNET") \
            or paths[path_id].get("model")
        if current_model and written == current_model:
            return path_id
    return candidates[0]
