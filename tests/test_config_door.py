"""The config door: the graduated config/instance-state layer (AHA-0021).

The suite holds the landing's measured properties: the surface is a
composition (name-for-name, not presence), the epic is a required
keyword (checkpoint 1's amendment), the settings precedence is the
contract's, and the holdings read is the ported allowlist.
"""

from __future__ import annotations

import json
import socket
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import yaml

import ahabase
from ahabase import config

#: The seam contract's surface - the whole of it, name for name. The six
#: the flip quotes (frozen at the door's first release) plus the AHA-0035
#: addition: the workspace folder set (the Human ruling 2026-11-22).
SURFACE = {
    "get_workspace_dir",
    "get_instance_root",
    "get_machine_id",
    "load_settings",
    "get_data_dir",
    "list_scope_holdings",
    "ensure_standard_folders",
}

#: The allowlist of list_scope_holdings - the contract the consumers
#: read against; a field added here without the write path is exactly
#: the divergence the ported lesson names.
HOLDING_KEYS = {
    "invocation_id", "bound_story", "bound_epic", "tree", "role",
    "team", "llm_path", "model", "last_access", "host_pid", "stale",
}


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A door pointed at a throwaway workspace."""
    ws = tmp_path / "ws"
    monkeypatch.setenv("AHABASE_WORKSPACE", str(ws))
    return ws


def write_settings(ws: Path, epic: str, text: str) -> None:
    cfg = ws / "_config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / f"{epic}-cli-settings.yml").write_text(text)


# ---- the surface -----------------------------------------------------------------

def test_surface_composition_name_for_name():
    """The six functions are the module's whole public function surface."""
    public = {n for n, v in vars(config).items()
              if not n.startswith("_") and callable(v)
              and getattr(v, "__module__", None) == config.__name__}
    assert public == SURFACE
    for name in SURFACE:
        assert callable(getattr(ahabase, name, None)), (
            f"{name} missing from the ahabase package seam")


def test_epic_is_a_required_keyword():
    """No ambient epic: the settings readers refuse a parameterless call."""
    for fn in (config.load_settings, config.get_data_dir,
               config.list_scope_holdings):
        with pytest.raises(TypeError):
            fn()


# ---- the workspace trio ----------------------------------------------------------

def test_workspace_trio(tmp_path, monkeypatch):
    monkeypatch.delenv("AHABASE_WORKSPACE", raising=False)
    assert config.get_workspace_dir() == Path("~/ahabase").expanduser()
    assert config.get_instance_root() == config.get_workspace_dir()
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    assert config.get_workspace_dir() == tmp_path / "ws"
    assert config.get_instance_root() == tmp_path / "ws"
    assert config.get_machine_id() == socket.gethostname()


# ---- settings --------------------------------------------------------------------

def test_missing_settings_is_normal_and_per_epic(workspace):
    assert config.load_settings(epic="evolucean") == {}
    write_settings(workspace, "epicone",
                   "data_dir: ~/somewhere\nsession_stale_seconds: 120\n")
    settings = config.load_settings(epic="epicone")
    assert settings["session_stale_seconds"] == 120
    assert settings["data_dir"] == str(Path("~/somewhere").expanduser())
    assert config.load_settings(epic="epictwo") == {}


def test_env_config_override_wins(workspace, tmp_path, monkeypatch):
    write_settings(workspace, "epicone", "data_dir: /from-file\n")
    override = tmp_path / "override.yml"
    override.write_text("data_dir: /from-env\n")
    monkeypatch.setenv("AHABASE_CONFIG", str(override))
    assert config.load_settings(epic="epicone")["data_dir"] == str(Path("/from-env"))


def test_duplicate_key_warns_once_and_last_wins(workspace, capsys):
    write_settings(workspace, "dup", "data_dir: /a\ndata_dir: /b\n")
    assert config.load_settings(epic="dup")["data_dir"] == str(Path("/b"))
    assert "duplicated key" in capsys.readouterr().err
    config.load_settings(epic="dup")
    assert capsys.readouterr().err == ""


def test_malformed_settings_is_a_loud_failure(workspace):
    # A file that exists but does not parse raises (witnessed:
    # yaml.parser.ParserError for this input) - it must never read as {}
    write_settings(workspace, "broken", "data_dir: [unclosed\n")
    with pytest.raises(yaml.YAMLError):
        config.load_settings(epic="broken")


# ---- the data dir ----------------------------------------------------------------

def test_data_dir_default_is_the_ahabase_layout(workspace):
    data = config.get_data_dir(epic="base")
    assert data == workspace / "_data" / "base"
    assert data.is_dir()


def test_data_dir_settings_override(workspace, tmp_path, monkeypatch):
    absolute = tmp_path / "abs-data"
    write_settings(workspace, "abs", f"data_dir: {absolute}\n")
    assert config.get_data_dir(epic="abs") == absolute
    write_settings(workspace, "rel", "data_dir: ./rel-data\n")
    assert config.get_data_dir(epic="rel") == (workspace / "rel-data").resolve()
    write_settings(workspace, "home", "data_dir: ~/home-data\n")
    assert config.get_data_dir(epic="home") == Path("~/home-data").expanduser()


def test_epic_is_a_name_not_a_path(workspace):
    for bad in ("../escape", "a/b", ".hidden", ""):
        with pytest.raises(ValueError):
            config.load_settings(epic=bad)


# ---- the holdings ----------------------------------------------------------------

def plant_session(ws: Path, epic: str, invocation: str, payload: dict) -> None:
    sessions = ws / "_data" / epic / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    (sessions / f"{invocation}.json").write_text(json.dumps(payload))


def test_holdings_allowlist_fresh_stale_and_malformed(workspace):
    now = datetime.now()
    plant_session(workspace, "hold", "fresh", {
        "bound_story": "STORY-0001", "bound_epic": "epicone",
        "tree": "/t/ree", "role": "author", "team": "t1",
        "llm_path": "flash/mimo", "model": "mimo",
        "last_access": (now - timedelta(minutes=1)).isoformat(),
        "host_pid": 4242,
        "secret_runtime_state": "must not ride",
    })
    plant_session(workspace, "hold", "stale", {
        "bound_story": "STORY-0002",
        "last_access": (now - timedelta(hours=2)).isoformat(),
    })
    plant_session(workspace, "hold", "broken", {"payload": "overwritten below"})
    (workspace / "_data" / "hold" / "sessions" / "broken.json").write_text("{not json")

    entries = {e["invocation_id"]: e for e in
               config.list_scope_holdings(epic="hold")}
    assert set(entries) == {"fresh", "stale"}  # malformed skipped
    assert set(entries["fresh"]) == HOLDING_KEYS  # the allowlist, exactly
    assert entries["fresh"]["stale"] is False
    assert entries["fresh"]["host_pid"] == 4242
    assert "secret_runtime_state" not in entries["fresh"]
    assert entries["stale"]["stale"] is True
    assert entries["stale"]["role"] is None  # absent field reads as None


def test_holdings_staleness_reads_the_epic_settings(workspace):
    write_settings(workspace, "hold", "session_stale_seconds: 60\n")
    plant_session(workspace, "hold", "ten-minutes", {
        "bound_story": "STORY-0003",
        "last_access": (datetime.now() - timedelta(minutes=10)).isoformat(),
    })
    (entry,) = config.list_scope_holdings(epic="hold")
    assert entry["stale"] is True  # 10 min > the 60 s override


def test_holdings_missing_sessions_dir_is_empty(workspace):
    assert config.list_scope_holdings(epic="nothing-yet") == []
