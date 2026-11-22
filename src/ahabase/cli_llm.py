"""``ahabase llm``: the model door of the CLI.

Capability: llm-paths

Implements: implementation-ahabase-llm-blueprint

Commands over the ``ahabase.llm`` package: list the access paths, discover what
the machine can use, verify a path, switch the tool to a verified path, restore
a settings backup, write a session payload, and ``key``, the command the tool
runs to obtain a path's key (the key helper). The package ships no provider
entries, so these commands see the native routes and the instance's own
variants; a method that has provider entries passes them to the library.

No command prints a credential value except ``key``, whose single job is to
write a path's key to its standard output, a pipe to the tool; every other
output is redacted.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import click

from .llm import discovery, paths, session, switch, verify


def _fail(error: Exception) -> None:
    raise click.ClickException(str(error))


#: The file names the door goes by (the console script, with the Windows executable form).
_DOOR_NAMES = ("ahabase", "ahabase.exe")


def _door() -> str:
    """The absolute path of this ``ahabase`` command: the bound helper and the safe's runner at once.

    A key the safe holds is released only to a command its owner bound, so the door names itself
    to the library (``executable`` and ``safe_executable``) and the key is obtained through the
    safe's bound run instead of an in-process resolution the consumer check would refuse. When the
    door was started through an interpreter (``python -m ahabase``, a directory, a file that merely
    starts with the name) the command next to the interpreter, else the one on PATH, stands in:
    only a regular file called exactly ``ahabase`` (or ``ahabase.exe``, in any letter case, as Windows spells it) is ever named.
    """
    first = Path(sys.argv[0]) if sys.argv and sys.argv[0] else None
    if first is not None and first.name.lower() in _DOOR_NAMES and first.is_file():
        return os.path.abspath(first)
    for name in _DOOR_NAMES:
        beside = Path(sys.executable).parent / name
        if beside.is_file():
            return str(beside)
    return shutil.which("ahabase") or str(Path(sys.executable).parent / "ahabase")


@click.group("llm")
def llm():
    """Access paths to a language model: list, discover, verify, switch, restore, pin a session."""


@llm.command("path-list")
def path_list():
    """List the known access paths and which one is in force."""
    active = paths.current_path()
    for path_id, definition in paths.known_paths().items():
        marker = "*" if path_id == active else " "
        click.echo(f"{marker} {path_id}")
        click.echo(f"    {definition.get('description', '')}")
        click.echo(f"    base_url: {definition.get('base_url') or '(none)'}")
        click.echo(f"    model:    {definition.get('model') or '(default)'}")
        click.echo(f"    auth:     {definition.get('auth', '')}")


@llm.command("discover")
@click.option("--no-registry", is_flag=True, help="Do not update the per-machine registry.")
def discover(no_registry):
    """Find which access paths this machine can use (local checks only; no network)."""
    try:
        result = discovery.discover(update_registry=not no_registry)
    except paths.AuthError as error:
        _fail(error)
    click.echo(f"active: {result['active']}")
    for row in result["availability"]:
        click.echo(f"{'available' if row['available'] else 'not available':14} {row['path']}: {row['evidence']}")
    if result["registration_candidate"]:
        click.echo(f"candidate: {result['registration_candidate']['note']}")


@llm.command("path-verify")
@click.argument("path_id")
def path_verify(path_id):
    """Verify a path with a minimal request (a few tokens)."""
    try:
        result = verify.verify_path(path_id, executable=_door(), safe_executable=_door())
    except paths.AuthError as error:
        _fail(error)
    click.echo(f"{path_id}: {'ok' if result['ok'] else 'failed'} - {result['detail']}")
    if not result["ok"]:
        cls = verify.failure_class(result)
        click.echo(f"class: {cls} - {verify.FAILURE_HINTS[cls]}")
        sys.exit(1)


@llm.command("path-switch")
@click.argument("path_id")
@click.option("--confirm", is_flag=True, help="Required: this edits the live settings.")
@click.option("--no-prove", is_flag=True, help="Skip the one-turn launch proof.")
@click.option("--force", is_flag=True, help="Proceed although live sessions are pinned elsewhere.")
@click.option("--region", default=None)
def path_switch(path_id, confirm, no_prove, force, region):
    """Point the tool at a verified path, with a backup of the previous settings."""
    try:
        result = switch.switch_path(path_id, confirm=confirm, prove=not no_prove, force=force, region=region,
                                    executable=_door(), safe_executable=_door())
    except (ValueError, FileNotFoundError, paths.AuthError) as error:
        _fail(error)
    click.echo(f"settings now point at {path_id}; backup {result['backup']}")


@llm.command("path-restore")
@click.argument("backup", required=False)
@click.option("--latest", is_flag=True)
@click.option("--confirm", is_flag=True, help="Required: this edits the live settings.")
@click.option("--no-prove", is_flag=True)
@click.option("--allow-literal", is_flag=True,
              help="Accept writing back a literal credential that an older backup holds.")
def path_restore(backup, latest, confirm, no_prove, allow_literal):
    """List the settings backups, or restore one (verify first, reversible)."""
    if not backup and not latest and not confirm:
        for row in switch.list_backups():
            click.echo(f"{row['index']:3} {row['name']}  ->  {row['base_url']}")
        return
    try:
        result = switch.restore_backup(backup, latest=latest, confirm=confirm, prove=not no_prove,
                                       allow_literal=allow_literal)
    except (ValueError, FileNotFoundError) as error:
        _fail(error)
    click.echo(f"restored {result['backup']} ({result['base_url']}); previous settings saved as "
               f"{result['pre_restore_backup']}")


@llm.command("session-env")
@click.argument("path_id")
@click.option("--out", "out_path", default=None, help="Write the payload to this file.")
@click.option("--epic", default=None, help="The epic whose data directory holds the default payload file.")
@click.option("--check", is_flag=True, help="Validate offline: presence, never values.")
def session_env(path_id, out_path, epic, check):
    """Build the per-session payload for a path (it holds no credential value)."""
    try:
        if check:
            result = session.session_env_check(path_id)
            click.echo(f"{'ok' if result['ok'] else 'failed'}: {result['detail']}")
            sys.exit(0 if result["ok"] else 1)
        if out_path or epic:
            written = session.session_env_out(path_id, out_path=out_path, epic=epic or "", executable=_door())
            click.echo(written["file"])
        else:
            click.echo(json.dumps(session.session_env(path_id, executable=_door()), indent=2))
    except (ValueError, paths.AuthError) as error:
        _fail(error)


@llm.command("key")
@click.argument("path_id")
@click.option("--emit", is_flag=True, hidden=True,
              help="The inner step: write the value the safe injected into this process.")
def key(path_id, emit):
    """Write a path's key to standard output (the key helper the tool runs)."""
    try:
        value = session.key_value(path_id, emit=emit, executable=_door(), safe_executable=_door())
    except (ValueError, paths.AuthError) as error:
        _fail(error)
    click.echo(value)


@llm.command("session-launch", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("path_id")
@click.argument("claude_args", nargs=-1, type=click.UNPROCESSED)
@click.option("--epic", default="ahabase", show_default=True,
              help="The epic whose data directory holds the payload file.")
def session_launch(path_id, claude_args, epic):
    """Launch a Claude Code session pinned to an access path - one command.

    The payload goes to an owner-only file and carries the key helper command, never a value;
    then this process is replaced by ``claude --settings FILE`` and everything after the path id
    is passed to claude unchanged. The machine's own settings are not touched.
    """
    try:
        written = session.session_env_out(path_id, epic=epic, executable=_door())
    except (ValueError, paths.AuthError) as error:
        _fail(error)
    program = shutil.which("claude")
    if program is None:
        _fail(ValueError("claude is not on PATH - install it, or launch with: claude --settings " + written["file"]))
    if written.get("context_window_warning"):
        click.echo(f"warning: {written['context_window_warning']}", err=True)
    _exec(program, [program, "--settings", written["file"], *claude_args])


def _exec(program, argv):
    """Replace this process (a seam so a test can observe the launch)."""
    os.execv(program, argv)
