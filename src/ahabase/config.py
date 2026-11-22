"""The config door: workspace/instance resolution and epic settings.

Graduated from the method CLI's config layer (pilot graduation 1,
AHA-0021; the dossier and the seam contract live in the method
repository). This is the layer every other capability stands on: where
the workspace is, what an epic's settings say, where its data lives,
which machine this is, and which collaboration scopes hold bindings.

The door is workspace-level and epic-explicit. A function whose result
depends on which epic the caller "currently is" would be ambient state,
so the epic is a required keyword on the settings-reading functions and
the workspace trio takes no argument at all. The settings filename
convention ``_config/<epic>-cli-settings.yml`` is this door's own: one
settings file per tenant epic under the workspace's ``_config/``.

The collaboration store stays where the serving epic's data dir puts it
(the journal, board, inbox and sessions of a running instance do not
move). Whether a future serving epic roots its collaboration store
per-epic or workspace-wide is the collab capability's own landing to
decide; this seam records that and does not decide it.

Implements: implementation-ahabase-config-door-blueprint
Blueprint: implementation-ahabase-config-door-blueprint

Capability: config-management
"""

from __future__ import annotations

import json
import os
import re
import socket
from datetime import datetime
from pathlib import Path

from ._yaml_unique import load as _load_unique

#: Direct settings-file override: wins when the file it names exists.
ENV_CONFIG = "AHABASE_CONFIG"

#: Workspace-root override for the whole door.
ENV_WORKSPACE = "AHABASE_WORKSPACE"

#: The workspace root default.
DEFAULT_INSTANCE_ROOT = "~/ahabase"

#: An epic is a name, not a path segment: this is the whole shape one
#: may take as a settings/data tenant (a slash would leave the layout).
_EPIC_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

#: Settings keys that hold one path each (~ expanded after load).
_PATH_KEYS = ("wikis_dir", "workspace_dir", "config_dir", "data_dir")

#: TTL after which an untouched collaboration binding is stale, unless
#: the epic's settings override it.
SESSION_STALE_SECONDS = 3600


def _check_epic(epic: str) -> str:
    if not _EPIC_NAME.match(epic):
        raise ValueError(
            f"epic must be a name ([A-Za-z0-9][A-Za-z0-9_-]*), got {epic!r}")
    return epic


def _expand_path(path: str) -> Path:
    """Expand ~ and return Path."""
    return Path(path).expanduser()


def get_workspace_dir() -> Path:
    """The workspace root: ``AHABASE_WORKSPACE`` env, default ``~/ahabase``.

    Never ``None`` - callers that used to fall back on a missing root get
    the root directly (the landing decision of AHA-0021 checkpoint 1: a
    ``None`` contract would let absence propagate past path operations
    and be silently tolerated, a fail-open shape for the foundation
    layer).
    """
    env = os.environ.get(ENV_WORKSPACE)
    if env:
        return _expand_path(env)
    return _expand_path(DEFAULT_INSTANCE_ROOT)


def get_instance_root() -> Path:
    """The instance root - the ported name for the workspace resolution.

    Same resolution as :func:`get_workspace_dir` (the workspace when
    configured, ``~/ahabase`` default); the two names exist because the
    graduated consumers import both.
    """
    return get_workspace_dir()


def get_machine_id() -> str:
    """A stable machine identifier: the hostname.

    Ported behavior: the hostname is the id instances stamp into their
    collaboration rows.
    """
    return socket.gethostname()


def _settings_path(epic: str) -> Path:
    """The epic's settings file, in order of precedence.

    1. ``AHABASE_CONFIG`` env var (a settings-file path, any epic)
    2. ``<workspace>/_config/<epic>-cli-settings.yml``
    3. nothing (a missing settings file is normal: an epic without a
       file has no overrides; :func:`load_settings` returns ``{}``)
    """
    env_config = os.environ.get(ENV_CONFIG)
    if env_config:
        path = Path(env_config).expanduser()
        if path.exists():
            return path
    return get_workspace_dir() / "_config" / f"{epic}-cli-settings.yml"


def load_settings(*, epic: str) -> dict:
    """The epic's settings dict (the file at :func:`_settings_path`).

    A missing file is normal and returns ``{}``. A duplicated key warns
    once and keeps YAML's last-wins value - strict would stop every
    command on an instance until its file is repaired. The four path
    keys (``wikis_dir``, ``workspace_dir``, ``config_dir``, ``data_dir``)
    get ``~`` expanded, ported behavior.
    """
    _check_epic(epic)
    config_path = _settings_path(epic)
    if not config_path.exists():
        return {}
    settings = _load_unique(config_path.read_text(), str(config_path),
                            strict=False) or {}
    for key in _PATH_KEYS:
        if key in settings:
            settings[key] = str(_expand_path(settings[key]))
    return settings


def get_data_dir(*, epic: str) -> Path:
    """The epic's data directory, created on demand.

    The epic's settings ``data_dir`` (expanded) when set, else
    ``<workspace>/_data/<epic>`` - the ahabase layout (the ported
    default was the method product's own home directory, which could
    not ride). A relative ``data_dir`` resolves from the workspace
    root: a wheel has no project root to resolve from. (Ported-behavior
    correction, AHA-0021: the settings load expands the value first, so
    a ``./``-prefixed path arrives here collapsed to a bare relative
    name - the ported prefix test never fired and such a value silently
    landed relative to the process cwd; the door anchors every
    non-absolute value at the workspace instead.)
    """
    _check_epic(epic)
    settings = load_settings(epic=epic)
    value = settings.get("data_dir", str(get_workspace_dir() / "_data" / epic))
    path = _expand_path(value)
    if not path.is_absolute():
        path = (get_workspace_dir() / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _stale_seconds(epic: str) -> int:
    """TTL after which an untouched collaboration binding is stale.

    The epic's settings ``session_stale_seconds`` overrides; a value
    that is not an int falls back to the default rather than breaking
    the read.
    """
    settings = load_settings(epic=epic)
    try:
        return int(settings.get("session_stale_seconds", SESSION_STALE_SECONDS))
    except (TypeError, ValueError):
        return SESSION_STALE_SECONDS


def _scopes_dir(epic: str) -> Path:
    """The collaboration scopes dir: the epic's data dir under ``sessions``.

    Ported composition. The collaboration store stays where the serving
    epic's data dir puts it; see the module docstring for the recorded
    boundary.
    """
    return get_data_dir(epic=epic) / "sessions"


def list_scope_holdings(*, epic: str) -> list[dict]:
    """All collaboration scopes of the epic's sessions dir, with staleness.

    Capability: scope-holdings

    The returned dict is an explicit allowlist, not the whole scope
    file: a scope entry is raw runtime state, and a blanket passthrough
    would let anything that ever lands there reach the projections that
    render it. Every field a consumer reads must therefore be named
    here. The lesson is measured, not ceremonial: the origin story of
    this contract shipped ``host_pid`` in the write path while this read
    path silently dropped it, so the liveness check always saw ``None``
    and every live session rendered as the anonymous placeholder - a
    hand-built entry dict in the suite carried the field the real
    producer did not, and the divergence went unseen (guarded there by
    a test that runs the real producer; the guard rides the collab
    landing, not this door).
    """
    _check_epic(epic)
    ttl = _stale_seconds(epic)
    scopes_dir = _scopes_dir(epic)
    entries: list[dict] = []
    if not scopes_dir.exists():
        return entries
    now = datetime.now()
    for path in sorted(scopes_dir.glob("*.json")):
        try:
            scope = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        last = scope.get("last_access")
        stale = True
        if last:
            try:
                age = (now - datetime.fromisoformat(last)).total_seconds()
                stale = age > ttl
            except ValueError:
                pass
        entries.append({
            "invocation_id": path.stem,
            "bound_story": scope.get("bound_story"),
            "bound_epic": scope.get("bound_epic"),
            "tree": scope.get("tree"),
            "role": scope.get("role"),
            # mirrors "role" exactly - a session-level claim projected
            # for the team layer
            "team": scope.get("team"),
            # model identity stamped by the heartbeat, projected for
            # the team layer
            "llm_path": scope.get("llm_path"),
            "model": scope.get("model"),
            "last_access": last,
            # the liveness signal the write path stamps; without it
            # here, no session is ever verified
            "host_pid": scope.get("host_pid"),
            "stale": stale,
        })
    return entries
