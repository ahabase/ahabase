"""Discovery: which access paths exist on this machine and are usable.

Capability: llm-discovery

Introspects what the tool actually runs, assesses every known path with cheap
local checks only (a variable set, a login or credentials present, a safe
entry named) and keeps a per-machine registry. No network is used and no
token is spent; a network check is verification's job, taken with consent.
Presence is checked, a credential value is never read or returned.

The registry belongs to one machine and lives in the instance's ``_config``
directory, outside git; another machine's record is never read as this one's.

Implements: implementation-ahabase-llm-blueprint
"""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

from ..config import get_instance_root, get_machine_id
from . import paths as res

REGISTRY_VERSION = "2026-10"
REGISTRY_FILENAME = "llm-paths-registry.yml"


def get_registry_path() -> Path:
    """The live per-machine registry (outside git).

    Capability: llm-discovery
    """
    return get_instance_root() / "_config" / REGISTRY_FILENAME


def machine_id() -> str:
    """The stable machine identifier (the config door's)."""
    return get_machine_id()


def load_registry(*, registry_path: Optional[Path] = None) -> dict:
    """Load the availability registry (an empty structure when absent).

    Capability: llm-discovery

    Shape: ``{version, machines: {machine_id: {hostname, checked_at,
    paths: {path_id: {available, evidence, checked_at}}}}}``. An unreadable
    registry reads as empty: discover again, never crash.
    """
    path = Path(registry_path) if registry_path else get_registry_path()
    data: dict = {"version": REGISTRY_VERSION, "machines": {}}
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text()) or {}
            if isinstance(loaded, dict):
                data.update(loaded)
                data.setdefault("machines", {})
        except (yaml.YAMLError, OSError):
            pass
    return data


def save_registry(registry: dict, *, registry_path: Optional[Path] = None) -> bool:
    """Save the registry atomically (temp file and rename); False when it cannot be written.

    Capability: llm-discovery
    """
    path = Path(registry_path) if registry_path else get_registry_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        with open(temp, "w") as handle:
            yaml.dump(registry, handle, default_flow_style=False, sort_keys=False)
        temp.replace(path)
        return True
    except OSError:
        return False


def _safe_entry_named(name: str) -> bool:
    """True when the safe's manifest names the entry (presence only; the value is not read)."""
    try:
        from ..safe import Safe, SafeError
        try:
            return name in Safe().entries()
        except SafeError:
            return False
    except ImportError:
        return False


def assess_local_availability(env: Optional[dict] = None,
                              process_env: Optional[dict] = None, *,
                              builtin: Optional[dict] = None,
                              variants_file: Optional[Path] = None) -> list[dict]:
    """Per-path availability on this machine - cheap local checks only.

    Capability: llm-discovery

    Native routes read their presence helpers; a variable-token path checks the
    tool's settings env first, then the process environment; a ``safe://`` path
    is available when the safe's manifest names the entry. Nothing here touches
    the network or reads a secret value.

    Returns a list of ``{path, available, evidence, current}`` per known path.
    """
    state = env if env is not None else res.settings_env()
    merged = {**(process_env if process_env is not None else os.environ), **state}
    active = res.current_path(state, builtin=builtin, variants_file=variants_file)
    rows: list[dict] = []
    for path_id, definition in res.known_paths(builtin, variants_file).items():
        auth = definition.get("auth", "")
        form = res.auth_form(auth)
        if definition.get("key_helper"):
            available, evidence = True, "key helper declared"
        elif form == "oauth":
            source = res.subscription_login_source()
            available = source is not None
            evidence = source or "no subscription login on this machine"
        elif form == "aws-credentials":
            source = res.bedrock_credentials_source()
            available = source is not None
            evidence = source or "no cloud credentials on the chain"
        elif form == "env":
            name = auth[4:]
            if name in state and state[name]:
                available, evidence = True, f"settings env: {name}"
            elif merged.get(name):
                available, evidence = True, f"process env: {name}"
            else:
                available, evidence = False, f"{name} not set"
        elif form == "safe":
            name = auth[len(res.SAFE_PREFIX):]
            available = _safe_entry_named(name)
            evidence = f"safe entry: {name}" if available else f"no safe entry named {name}"
        else:
            available, evidence = False, f"unmanaged auth spec for {path_id}"
        rows.append({"path": path_id, "available": available,
                     "evidence": evidence, "current": path_id == active})
    return rows


def discover(env: Optional[dict] = None, update_registry: bool = True,
             registry_path: Optional[Path] = None, *,
             builtin: Optional[dict] = None,
             variants_file: Optional[Path] = None) -> dict:
    """Full discovery: the active shape, candidates, availability and the registry.

    Capability: llm-discovery

    Introspects what the tool runs, reports an unrecognised shape as a
    registration candidate (it never edits definitions), assesses every known
    path offline and persists this machine's availability. The registry write
    is the only mutation and it lives outside git.
    """
    state = env if env is not None else res.settings_env()
    active = res.current_path(state, builtin=builtin, variants_file=variants_file)
    shape_known = active in res.known_paths(builtin, variants_file)
    candidate = None
    if not shape_known:
        candidate = {
            "shape": active,
            "base_url": state.get("ANTHROPIC_BASE_URL", ""),
            "note": "registration candidate - add a path definition",
        }
    rows = assess_local_availability(env=state, builtin=builtin, variants_file=variants_file)

    registry_saved = False
    if update_registry:
        registry = load_registry(registry_path=registry_path)
        checked = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
        entry = registry.setdefault("machines", {}).setdefault(
            machine_id(), {"hostname": socket.gethostname(), "paths": {}})
        entry["hostname"] = socket.gethostname()
        entry["checked_at"] = checked
        entry["paths"] = {
            row["path"]: {"available": row["available"],
                          "evidence": row["evidence"],
                          "checked_at": checked}
            for row in rows}
        registry["version"] = REGISTRY_VERSION
        registry_saved = save_registry(registry, registry_path=registry_path)
    return {
        "active": active,
        "shape_known": shape_known,
        "registration_candidate": candidate,
        "availability": rows,
        "registry_path": str(registry_path or get_registry_path()),
        "registry_saved": registry_saved,
    }


def load_machine_availability(*, machine: Optional[str] = None,
                              registry_path: Optional[Path] = None) -> Optional[dict]:
    """The stored availability entry for a machine (a projection reads this).

    Capability: llm-discovery

    Returns ``{hostname, checked_at, paths}`` or None when this machine has not
    discovered yet.
    """
    registry = load_registry(registry_path=registry_path)
    machines = registry.get("machines") or {}
    entry = machines.get(machine or machine_id())
    return entry if isinstance(entry, dict) else None
