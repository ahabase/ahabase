"""The per-session payload and the key helper.

Capability: llm-paths

Implements: implementation-ahabase-llm-blueprint

A session can be pinned to an access path without touching the machine's
settings: the tool is started with ``--settings <payload>``. The payload carries
the path's environment and, for a path that authenticates with a variable or a
safe reference, a **key helper**: the command ``ahabase llm key PATH_ID``, which
the tool runs at the moment it needs the key. No credential value is ever
written to the payload file, and one file per path is overwritten, never
accumulated.

The key helper obtains the value as follows. For ``env:NAME`` it reads that
variable from its own environment. For ``safe://NAME`` it launches
``safe run --env VAR=safe://NAME -- ahabase llm key PATH_ID --emit``: the safe
releases the value only to the consumer its owner bound (the prefix
``llm key``), and the inner command writes it to its standard output, a pipe to
the tool, and nowhere else. It never calls the safe's plain ``resolve``, which
does not check the consumer.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..config import get_data_dir
from . import paths as res

# The floor a launch must clear before a path's stated context window is
# trusted: the tool's own tool schemas alone measured about 33.6K tokens at a
# failing session, plus an output reservation - a fresh session needs this much
# before a single turn of real conversation.
CONTEXT_FLOOR_ESTIMATE = 80000

# The variable the inner key helper reads; the safe sets it for that child only.
EMIT_VARIABLE = "AHABASE_LLM_KEY"


def _executable(executable: Optional[str]) -> str:
    found = executable or shutil.which("ahabase")
    if not found:
        raise ValueError("ahabase is not on PATH - pass its absolute path")
    return os.path.abspath(found)


def helper_command(path_id: str, executable: Optional[str] = None) -> str:
    """The command the tool runs to obtain the key of a path.

    Capability: llm-paths

    The executable is made absolute: the safe's binding names an absolute path
    and compares it exactly.
    """
    exe = _executable(executable)
    if os.name == "nt":
        return subprocess.list2cmdline([exe, "llm", "key", path_id])
    return " ".join(shlex.quote(part) for part in (exe, "llm", "key", path_id))


def _token_auth(definition: dict) -> bool:
    return res.auth_form(str(definition.get("auth", ""))) in ("env", "safe") \
        and not definition.get("key_helper")


def session_env(path_id: str, region: Optional[str] = None, env: Optional[dict] = None, *,
                builtin: Optional[dict] = None, variants_file: Optional[Path] = None,
                env_overrides: Optional[dict] = None, executable: Optional[str] = None) -> dict:
    """Build the per-session ``--settings`` payload for one access path.

    Capability: llm-paths

    The env map has the same shape the settings switch writes, with a key that a
    switch would remove expressed as an empty string (the tool's unset): a
    ``--settings`` payload merges per variable, so an omitted key would let the
    machine value leak through. ``env_overrides`` (for example a compact
    window the method resolved) is merged last.

    Returns ``{path, env, settings, auth_env, launchable, context_window_warning,
    model, context_window}``. Raises :class:`ValueError` for an unknown path or a
    pin the definition cannot honour.
    """
    env = env if env is not None else os.environ
    definition = res.known_paths(builtin, variants_file).get(path_id)
    if definition is None:
        raise ValueError(f"unknown access path {path_id!r}")
    pin_problem = res.pin_error(path_id, definition)
    if pin_problem:
        raise ValueError(pin_problem)
    auth = definition.get("auth", "")
    tier_models = definition.get("tier_models") or {}
    target_model = definition.get("model") or ""
    helper = definition.get("key_helper")

    payload: dict = {}
    settings: dict = {}
    auth_env: Optional[str] = None
    if auth in ("oauth", "aws-credentials") and not definition.get("base_url"):
        for key in res.OAUTH_REMOVED_KEYS:
            payload[key] = ""
        if auth == "aws-credentials":
            payload[res.BEDROCK_FLAG] = "1"
            region = region or definition.get("region") or env.get("AWS_REGION")
            profile = definition.get("aws_profile") or env.get("AWS_PROFILE")
            if region:
                payload["AWS_REGION"] = region
            if profile:
                payload["AWS_PROFILE"] = profile
            if target_model:
                payload["ANTHROPIC_MODEL"] = target_model
        else:
            payload[res.BEDROCK_FLAG] = ""
        launchable = True
    else:
        if helper:
            settings["apiKeyHelper"] = helper
        elif _token_auth(definition):
            settings["apiKeyHelper"] = helper_command(path_id, executable)
            if res.auth_form(auth) == "env":
                auth_env = auth[4:]
        payload[res.BEDROCK_FLAG] = ""
        payload["ANTHROPIC_MODEL"] = res.pinned_model(definition)
        payload["ANTHROPIC_BASE_URL"] = definition.get("base_url")
        payload["ANTHROPIC_AUTH_TOKEN"] = ""
        payload["ANTHROPIC_API_KEY"] = ""
        if target_model:
            for tier in res.TIERS:
                payload[f"ANTHROPIC_DEFAULT_{tier}_MODEL"] = tier_models.get(tier) or target_model
        launchable = True
    context_window = definition.get("context_window")
    warning = None
    if context_window is not None and context_window < CONTEXT_FLOOR_ESTIMATE:
        warning = (f"context_window {context_window} is below the ~{CONTEXT_FLOOR_ESTIMATE} floor "
                   "a fresh session needs (tool schemas and the output reservation alone) - "
                   "this path may be refused on its very first turn")
    payload.update(env_overrides or {})
    return {"path": path_id, "env": payload, "settings": settings, "auth_env": auth_env,
            "launchable": launchable, "context_window_warning": warning,
            "model": target_model, "context_window": context_window}


def _write_owner_only(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(text)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def session_env_out(path_id: str, *, epic: str, out_path: Optional[Path] = None,
                    region: Optional[str] = None, env: Optional[dict] = None,
                    builtin: Optional[dict] = None, variants_file: Optional[Path] = None,
                    env_overrides: Optional[dict] = None, executable: Optional[str] = None) -> dict:
    """Write the launchable session payload to a file.

    Capability: llm-paths

    The payload holds no credential value: a path that authenticates with a
    variable or a safe reference carries the key helper command, and a path
    whose variable is not set in this environment is refused (an empty answer
    would authenticate nothing and mask the cause). One file per path is
    overwritten under the epic's data directory, owner-only where the platform
    has the mode. ``epic`` is required, like the config door's.

    Returns ``{path, file, auth_env, context_window_warning}``.
    """
    import json

    env = env if env is not None else os.environ
    spec = session_env(path_id, region=region, env=env, builtin=builtin, variants_file=variants_file,
                       env_overrides=env_overrides, executable=executable)
    if spec["auth_env"] and not env.get(spec["auth_env"]):
        raise ValueError(f"auth variable {spec['auth_env']} is not set in this environment - export it first")
    payload = {**spec["settings"], "env": dict(spec["env"])}
    target = Path(out_path) if out_path is not None else get_data_dir(epic=epic) / "session-env" / f"{path_id}.json"
    _write_owner_only(target, json.dumps(payload, indent=2))
    return {"path": path_id, "file": str(target), "auth_env": spec["auth_env"],
            "context_window_warning": spec["context_window_warning"]}


def session_env_check(path_id: str, env: Optional[dict] = None, *,
                      builtin: Optional[dict] = None, variants_file: Optional[Path] = None) -> dict:
    """Validate a session target offline: presence, never values.

    Capability: llm-paths

    The definition is known; a variable-token path has its variable set; a
    key-helper path has a helper that returns a key; a safe reference names an
    entry the safe can serve to the helper (checked when the helper runs, so
    only the shape is checked here); a native route needs no variable.
    """
    env = env if env is not None else os.environ
    definition = res.known_paths(builtin, variants_file).get(path_id)
    if definition is None:
        return {"ok": False, "path": path_id, "detail": f"unknown access path {path_id!r}"}
    form = res.auth_form(str(definition.get("auth", "")))
    if definition.get("key_helper"):
        if not res.resolve_key(definition, env):
            return {"ok": False, "path": path_id, "detail": "the key helper returned no key"}
        return {"ok": True, "path": path_id, "detail": "path known, the key helper returns a key"}
    if form == "env":
        name = definition["auth"][4:]
        if not env.get(name):
            return {"ok": False, "path": path_id, "detail": f"auth variable {name} not set"}
        return {"ok": True, "path": path_id, "detail": f"path known, auth variable {name} present"}
    if form == "safe":
        return {"ok": True, "path": path_id,
                "detail": "path known, the key comes from the safe through the key helper "
                          "(the owner must have bound it: ahabase safe bind)"}
    return {"ok": True, "path": path_id,
            "detail": "path known, credential-native auth (no variable required)"}


def key_value(path_id: str, *, emit: bool = False, env: Optional[dict] = None,
              builtin: Optional[dict] = None, variants_file: Optional[Path] = None,
              executable: Optional[str] = None, safe_executable: Optional[str] = None,
              runner=subprocess.run) -> str:
    """The key of a path, for the key helper command; raises :class:`ValueError` without one.

    Capability: llm-paths

    ``emit`` is the inner step: it returns the value the safe placed in this
    process's environment. Without it, an ``env:NAME`` path returns that
    variable, and a ``safe://NAME`` path launches the safe's bound run around
    the inner step; the plain ``resolve`` of the safe is never used. A path with
    a ``key_helper`` has no key to emit here.

    Two programs are involved for a ``safe://`` path: the **runner**
    (``safe_executable``, the program that provides ``safe run``) and the
    **bound helper** (``executable``, the command the owner bound). They are the
    same program unless the caller names the runner (the released default); the
    command is always ``<runner> safe run ... -- <helper> llm key ... --emit``, so a
    helper without a ``safe`` group fails the run, it never runs outside the gate.
    """
    env = env if env is not None else os.environ
    if emit:
        value = env.get(EMIT_VARIABLE, "")
        if not value:
            raise ValueError("no key was injected - run this through 'ahabase safe run'")
        return value
    definition = res.known_paths(builtin, variants_file).get(path_id)
    if definition is None:
        raise ValueError(f"unknown access path {path_id!r}")
    if definition.get("key_helper"):
        raise ValueError(f"{path_id} has a key helper of its own")
    form = res.auth_form(str(definition.get("auth", "")))
    if form == "env":
        value = env.get(definition["auth"][4:], "")
        if not value:
            raise ValueError(f"auth variable {definition['auth'][4:]} is not set")
        return value
    if form == "safe":
        exe = _executable(executable)
        runner_exe = _executable(safe_executable) if safe_executable is not None else exe
        name = definition["auth"][len(res.SAFE_PREFIX):]
        command = [runner_exe, "safe", "run", "--env", f"{EMIT_VARIABLE}={res.SAFE_PREFIX}{name}", "--",
                   exe, "llm", "key", path_id, "--emit"]
        proc = runner(command, capture_output=True, text=True, check=False)
        if proc.returncode != 0 or not (proc.stdout or "").strip():
            raise ValueError(f"the safe did not release safe://{name} to this command - "
                             f"the owner binds it once: ahabase safe bind {name} {exe} --prefix llm --prefix key")
        return proc.stdout.strip()
    raise ValueError(f"{path_id} authenticates with {definition.get('auth')!r}, which needs no key helper")
