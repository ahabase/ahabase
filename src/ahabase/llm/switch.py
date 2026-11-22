"""The settings switch: move the tool to a verified path, with a backup and a restore.

Capability: llm-paths

Implements: implementation-ahabase-llm-blueprint

The settings change only after a successful verification of the target, after a
backup of the previous content, atomically, and (by default) only if the tool
itself answers through exactly the settings about to be written. The written
settings hold a **key helper reference** for a path that authenticates with a
variable or a safe reference - never the resolved value - and a restore refuses
a legacy backup that holds a literal credential unless the caller says so.
Output is redacted before it is shown.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from . import paths as res
from .verify import (HELPER_HEADERS, TOKEN_HEADERS, _post_messages, launch_overlay, prove_launch,
                     redacted, verify_path)
from .session import helper_command

__all__ = ["switch_path", "list_backups", "restore_backup", "write_settings_atomically",
           "new_backup_path", "redacted"]


def _atomic_write(path: Path, text: str) -> None:
    """Replace ``path`` with ``text`` atomically (temp file, fsync, existing mode kept, ``os.replace``)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = os.stat(path).st_mode & 0o777 if path.exists() else None
    descriptor, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        if mode is not None:
            os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def write_settings_atomically(settings_path: Path, config: dict) -> None:
    """Replace the settings file in one step - a crash never leaves it half written.

    Capability: llm-paths

    The text is serialised first, so a dump error never reaches the disk.
    """
    _atomic_write(settings_path, json.dumps(config, indent=2))


def new_backup_path(settings_path: Path) -> Path:
    """A settings backup name no earlier backup has.

    Capability: llm-paths

    Two changes in one second share the second-resolution name; a taken name
    gets a counter, and the listing's newest-first order holds.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = settings_path.with_suffix(f".json.backup.path-{stamp}")
    count = 1
    while backup.exists():
        backup = settings_path.with_suffix(f".json.backup.path-{stamp}_{count}")
        count += 1
    return backup


def _backup_target(env: dict) -> str:
    """What a backup points at, for the listing - a cloud-native backup is not the subscription."""
    if str(env.get(res.BEDROCK_FLAG, "")).lower() in ("1", "true", "yes"):
        return f"(cloud-native {env.get('ANTHROPIC_MODEL') or 'default model'})"
    return env.get("ANTHROPIC_BASE_URL") or "(subscription)"


def list_backups(*, settings_path: Optional[Path] = None) -> list:
    """The timestamped settings backups, newest first.

    Capability: llm-paths

    Each row carries the base URL the backup would restore (``(subscription)``
    for a backup with no override), never a credential value.
    """
    settings_path = Path(settings_path) if settings_path else res.SETTINGS_PATH
    rows: list = []
    for index, backup in enumerate(sorted(settings_path.parent.glob(settings_path.name + ".backup.path-*"),
                                          reverse=True)):
        try:
            env = (json.loads(backup.read_text()) or {}).get("env", {})
        except (OSError, json.JSONDecodeError):
            env = {}
        rows.append({"index": index, "name": backup.name, "path": str(backup),
                     "timestamp": backup.name.rsplit("path-", 1)[-1], "base_url": _backup_target(env)})
    return rows


def _holds_literal(config: dict) -> bool:
    """True when the settings carry a credential value, with or without a key helper next to it.

    An older switch wrote the resolved token AND a helper together; the helper does not make the
    literal harmless - it is still on the disk, and a restore would write it back.
    """
    env = config.get("env") or {}
    return bool(env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY"))


def switch_path(target: str, base_url: Optional[str] = None, model: Optional[str] = None,
                confirm: bool = False, env: Optional[dict] = None, region: Optional[str] = None,
                force: bool = False, prove: bool = True, *, guard: Optional[Callable] = None,
                builtin: Optional[dict] = None, variants_file: Optional[Path] = None,
                tool_probe_paths=frozenset(), executable: Optional[str] = None,
                argv: Optional[list] = None, safe=None,
                safe_executable: Optional[str] = None) -> dict:
    """Point the tool at an access path - only after a verified preflight.

    Capability: llm-paths

    A path with a key helper writes the helper as the top-level ``apiKeyHelper``
    and no key at all. A path that authenticates with a variable or a safe
    reference writes the key helper command ``ahabase llm key PATH_ID`` and
    explicitly EMPTY ``ANTHROPIC_AUTH_TOKEN`` and ``ANTHROPIC_API_KEY`` - the
    resolved value is never written. The subscription route removes the
    overrides (written empty, so a shell export cannot decide); the cloud-native
    route does the same and sets its flag; any other route clears that flag.
    Model tiers resolve per tier: an explicit ``model`` wins, else the
    definition's ``tier_models`` entry, else its single ``model``.

    ``guard(target_id)`` (the id of the path switched to) returns the live sessions pinned to another path (each
    ``{session, llm_path}``); with any, the switch refuses unless ``force``.
    ``prove`` launches the tool once through exactly the settings about to be
    written and refuses when it does not answer.

    Returns ``{switched, path, backup, verify, foreign_sessions, proof}``.
    Raises :class:`ValueError` on an unverified target, an unknown path or a
    missing ``confirm``, and :class:`FileNotFoundError` without a settings file.
    """
    path_id = target  # the contract names the first parameter ``target``
    if not confirm:
        raise ValueError("switch requires confirm (it edits the live settings)")
    options = dict(builtin=builtin, variants_file=variants_file)
    verify = verify_path(path_id, base_url=base_url, model=model, env=env,
                         tool_probe_paths=tool_probe_paths, argv=argv, safe=safe,
                         executable=executable, safe_executable=safe_executable, **options)
    if not verify["ok"]:
        raise ValueError(f"preflight failed, not switching: {verify['detail']}")
    definitions = res.known_paths(builtin, variants_file)
    target_id = path_id if path_id in definitions else "custom"
    foreign = guard(target_id) if guard else []
    if foreign and not force:
        listed = ", ".join(f"{s['session']} (on {s['llm_path']})" for s in foreign)
        raise ValueError(f"live session(s) pinned to another path: {listed}. A machine switch re-pins "
                         "their next launch - re-run with force to proceed anyway, or ask them to close first")
    settings_path = res.SETTINGS_PATH
    if not settings_path.exists():
        raise FileNotFoundError(f"settings not found: {settings_path}")

    definition = definitions.get(path_id, {})
    target_base = base_url or definition.get("base_url")
    target_model = model or definition.get("model")
    helper = definition.get("key_helper")
    auth = definition.get("auth", "")
    if not helper and res.auth_form(str(auth)) in ("env", "safe") and not (auth in ("oauth", "aws-credentials")):
        helper = helper_command(path_id, executable)
    tier_models = definition.get("tier_models") or {}

    backup = new_backup_path(settings_path)
    shutil.copy(settings_path, backup)
    with open(settings_path) as handle:
        config = json.load(handle)
    original = json.loads(json.dumps(config))
    env_section = config.setdefault("env", {})
    config.pop("apiKeyHelper", None)
    if auth in ("oauth", "aws-credentials") and not base_url:
        for key in res.CONNECTION_ENV_KEYS:
            env_section[key] = ""
        if auth == "aws-credentials":
            env_section[res.BEDROCK_FLAG] = "1"
            if region:
                env_section["AWS_REGION"] = region
            if target_model:
                env_section["ANTHROPIC_MODEL"] = target_model
    else:
        env_section[res.BEDROCK_FLAG] = ""
        env_section["ANTHROPIC_MODEL"] = res.pinned_model(definition, model)
        env_section["ANTHROPIC_BASE_URL"] = target_base
        if helper:
            config["apiKeyHelper"] = helper
        env_section["ANTHROPIC_AUTH_TOKEN"] = ""
        env_section["ANTHROPIC_API_KEY"] = ""
        if target_model:
            for tier in res.TIERS:
                env_section[f"ANTHROPIC_DEFAULT_{tier}_MODEL"] = model or tier_models.get(tier) or target_model
    proof = None
    if prove:
        proof = prove_launch(launch_overlay(original, config))
        if not proof["ok"]:
            backup.unlink(missing_ok=True)  # nothing was written
            raise ValueError(f"the tool did not answer through the new settings, not switching: {proof['detail']}")
    write_settings_atomically(settings_path, config)
    return {"switched": True, "path": path_id, "backup": str(backup), "verify": verify,
            "foreign_sessions": foreign, "proof": proof}


def restore_backup(backup: Optional[str] = None, latest: bool = False, confirm: bool = False,
                   prove: bool = True, *, allow_literal: bool = False) -> dict:
    """Restore the env section from a settings backup - verify first.

    Capability: llm-paths

    - Verify first: the backup's own target must answer the minimal request
      before anything is written; a subscription backup gates on the login, a
      cloud-native one on the credential chain, one with a key helper on the
      key its helper returns. A failed verification leaves the live settings
      untouched.
    - Every mutation leaves a backup: the current settings are backed up first,
      so a restore is itself reversible.
    - Surgical: only the ``env`` section and the ``apiKeyHelper`` key are
      restored; other sections made since the backup survive.
    - A legacy backup that holds a literal credential is refused unless
      ``allow_literal`` says the Human accepts writing it back.

    Returns ``{restored, backup, pre_restore_backup, base_url, verify, proof}``.
    """
    if not confirm:
        raise ValueError("restore requires confirm (it edits the live settings)")
    rows = list_backups()
    if not rows:
        raise FileNotFoundError(f"no settings backups found ({res.SETTINGS_PATH.name}.backup.path-*)")
    if backup is None:
        if not latest:
            raise ValueError("choose a backup: latest, or a backup name from the listing")
        chosen = rows[0]
    else:
        wanted = Path(backup).name
        matches = [row for row in rows if row["name"] == wanted or row["path"] == str(backup)]
        if not matches:
            raise FileNotFoundError(f"backup not found: {backup}")
        chosen = matches[0]
    settings_path = res.SETTINGS_PATH
    if not settings_path.exists():
        raise FileNotFoundError(f"settings not found: {settings_path}")

    backup_path = Path(chosen["path"])
    try:
        backup_config = json.loads(backup_path.read_text()) or {}
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"the backup does not parse, not restoring: {error.__class__.__name__}") from None
    if _holds_literal(backup_config) and not allow_literal:
        raise ValueError("the backup holds a literal credential (an older switch wrote it) - not restoring it. "
                         "Set the value in the safe and switch to a path that uses it, or pass allow_literal "
                         "to write that literal back")
    target_env = backup_config.get("env", {})
    target_helper = backup_config.get("apiKeyHelper")
    base_url = target_env.get("ANTHROPIC_BASE_URL") or None
    token = target_env.get("ANTHROPIC_AUTH_TOKEN")
    if target_helper:
        token = res.resolve_key({"key_helper": target_helper})
    cloud = str(target_env.get(res.BEDROCK_FLAG, "")).lower() in ("1", "true", "yes")
    if cloud:
        source = res.bedrock_credentials_source()
        verify = ({"ok": True, "status": "credentials", "detail": f"cloud credentials present ({source})"} if source else
                  {"ok": False, "status": "no-credentials",
                   "detail": "the backup holds the cloud-native state but no credentials are on the chain"})
    elif base_url is None:
        source = res.subscription_login_source()
        verify = ({"ok": True, "status": "login", "detail": f"subscription login present ({source})"} if source else
                  {"ok": False, "status": "no-login",
                   "detail": "the backup holds the subscription state but no login is present"})
    else:
        model = (target_env.get("ANTHROPIC_DEFAULT_SONNET_MODEL") or target_env.get("ANTHROPIC_MODEL") or "ping")
        verify = redacted(_post_messages(base_url, model, token,
                                         headers=HELPER_HEADERS if target_helper else TOKEN_HEADERS), token)
    if not verify["ok"]:
        raise ValueError(f"backup target failed verification, not restoring: {verify['detail']}")

    pre_restore = new_backup_path(settings_path)
    shutil.copy(settings_path, pre_restore)
    with open(settings_path) as handle:
        config = json.load(handle)
    original = json.loads(json.dumps(config))
    config["env"] = target_env
    if target_helper:
        config["apiKeyHelper"] = target_helper
    else:
        config.pop("apiKeyHelper", None)
    proof = None
    if prove:
        proof = prove_launch(launch_overlay(original, config))
        if not proof["ok"]:
            pre_restore.unlink(missing_ok=True)
            raise ValueError(f"the tool did not answer through the backup's settings, not restoring: {proof['detail']}")
    write_settings_atomically(settings_path, config)
    return {"restored": True, "backup": str(backup_path), "pre_restore_backup": str(pre_restore),
            "base_url": _backup_target(target_env), "verify": verify, "proof": proof}
