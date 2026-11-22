"""The settings switch, backups and restore (AHA-0024 R3c)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ahabase.llm import paths, session, switch, verify

from .test_verify import MESSAGE, Gateway

CANARY = "CANARY-switch-0123456789abcdef"
EXE = os.path.abspath("/opt/bin/ahabase")


@pytest.fixture
def gateway():
    created = []

    def make(**kwargs):
        created.append(Gateway(**kwargs))
        return created[-1]

    yield make
    for item in created:
        item.close()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(paths, "CREDENTIALS_PATH", tmp_path / ".credentials.json")
    monkeypatch.setattr(paths, "AWS_CREDENTIALS_PATH", tmp_path / "aws" / "credentials")
    monkeypatch.setattr(paths, "AWS_SSO_CACHE_PATH", tmp_path / "aws" / "sso")
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: False)
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    paths.SETTINGS_PATH.write_text(json.dumps(
        {"theme": "dark", "env": {"ANTHROPIC_BASE_URL": "http://before", "KEEP": "1"}, "apiKeyHelper": "old-helper"}),
        encoding="utf-8")
    return tmp_path


def ladder(url):
    return {
        "gw": {"base_url": url, "model": "m", "auth": "env:SWITCH_KEY", "tier_models": {"HAIKU": "small"}},
        "vault": {"base_url": url, "model": "m", "auth": "safe://VAULT"},
        "own": {"base_url": url, "model": "m", "auth": "env:X", "key_helper": "own-helper"},
        "pinned": {"base_url": url, "model": "pm", "auth": "env:SWITCH_KEY", "pin_model": True},
    }


def go(path_id, url, **kwargs):
    kwargs.setdefault("prove", False)
    kwargs.setdefault("env", {"SWITCH_KEY": CANARY})
    return switch.switch_path(path_id, confirm=True, builtin=ladder(url), executable=EXE, **kwargs)


def settings():
    return json.loads(paths.SETTINGS_PATH.read_text(encoding="utf-8"))


# --- the switch ---------------------------------------------------------------

def test_a_switch_needs_confirmation(home, gateway):
    with pytest.raises(ValueError, match="confirm"):
        switch.switch_path("gw", builtin=ladder(gateway(body=MESSAGE).url), prove=False)


def test_a_failed_preflight_changes_nothing(home, gateway):
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="preflight failed"):
        go("gw", gateway(status=500, body={"error": "x"}).url)
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before
    assert switch.list_backups() == []


def test_a_variable_path_writes_the_helper_and_never_the_value(home, gateway):
    result = go("gw", gateway(body=MESSAGE).url)
    text = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    assert CANARY not in text
    written = settings()
    assert written["apiKeyHelper"] == session.helper_command("gw", EXE)
    env = written["env"]
    assert env["ANTHROPIC_AUTH_TOKEN"] == "" and env["ANTHROPIC_API_KEY"] == "" and env[paths.BEDROCK_FLAG] == ""
    assert env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "small" and env["ANTHROPIC_DEFAULT_SONNET_MODEL"] == "m"
    assert written["theme"] == "dark" and env["KEEP"] == "1"  # unrelated settings survive
    assert result["switched"] and Path(result["backup"]).exists()


def test_the_backup_holds_the_previous_content(home, gateway):
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    backup = go("gw", gateway(body=MESSAGE).url)["backup"]
    assert Path(backup).read_text(encoding="utf-8") == before


def test_a_path_with_its_own_helper_writes_that_helper(home, gateway):
    go("own", gateway(body=MESSAGE).url)
    assert settings()["apiKeyHelper"] == "own-helper"


def test_the_pin_is_written_and_a_model_override_wins_every_tier(home, gateway):
    url = gateway(body=MESSAGE).url
    go("pinned", url)
    assert settings()["env"]["ANTHROPIC_MODEL"] == "pm"
    go("gw", url, model="forced")
    env = settings()["env"]
    assert env["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "forced" and env["ANTHROPIC_MODEL"] == ""


def test_the_subscription_route_states_the_overrides_empty(home):
    paths.CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
    switch.switch_path("claude-pro", confirm=True, prove=False)
    written = settings()
    assert "apiKeyHelper" not in written
    assert all(written["env"][key] == "" for key in paths.CONNECTION_ENV_KEYS)


def test_the_cloud_native_route_sets_its_flag_region_and_model(home):
    defs = {"cloud-m": {"base_url": "", "model": "model-x", "auth": "aws-credentials"}}
    switch.switch_path("cloud-m", confirm=True, prove=False, env={"AWS_ACCESS_KEY_ID": "x"},
                       builtin=defs, region="eu-1")
    env = settings()["env"]
    assert env[paths.BEDROCK_FLAG] == "1" and env["AWS_REGION"] == "eu-1" and env["ANTHROPIC_MODEL"] == "model-x"
    assert env["ANTHROPIC_BASE_URL"] == ""


def test_live_sessions_on_another_path_stop_the_switch_unless_forced(home, gateway):
    url = gateway(body=MESSAGE).url
    seen = []

    def guard(target):
        seen.append(target)
        return [{"session": "s1", "llm_path": "other"}]
    with pytest.raises(ValueError, match="s1 \\(on other\\)"):
        go("gw", url, guard=guard)
    assert seen == ["gw"] and settings()["env"]["ANTHROPIC_BASE_URL"] == "http://before"
    result = go("gw", url, guard=guard, force=True)
    assert result["foreign_sessions"][0]["session"] == "s1"


def test_a_proof_that_fails_leaves_the_settings_and_no_backup(home, gateway, monkeypatch):
    monkeypatch.setattr(switch, "prove_launch", lambda overlay, **k: {"ok": False, "detail": "401 nope", "models": []})
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="did not answer"):
        go("gw", gateway(body=MESSAGE).url, prove=True)
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before and switch.list_backups() == []


def test_the_proof_runs_through_exactly_the_settings_about_to_be_written(home, gateway, monkeypatch):
    seen = []

    def prove(overlay, **k):
        seen.append(overlay)
        return {"ok": True, "detail": "fine", "models": []}
    monkeypatch.setattr(switch, "prove_launch", prove)
    go("gw", gateway(body=MESSAGE).url, prove=True)
    assert seen[0]["apiKeyHelper"] == settings()["apiKeyHelper"]
    assert seen[0]["env"]["ANTHROPIC_BASE_URL"] == settings()["env"]["ANTHROPIC_BASE_URL"]


def test_a_missing_settings_file_is_reported(home, gateway):
    paths.SETTINGS_PATH.unlink()
    with pytest.raises(FileNotFoundError):
        go("gw", gateway(body=MESSAGE).url)


# --- atomic write and backup names --------------------------------------------

def test_a_crash_during_the_write_keeps_the_old_content_and_leaves_no_temp_file(home, monkeypatch):
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")

    def boom(source, target):
        raise OSError("disk gone")
    monkeypatch.setattr(switch.os, "replace", boom)
    with pytest.raises(OSError):
        switch.write_settings_atomically(paths.SETTINGS_PATH, {"new": True})
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before
    assert [p.name for p in home.glob(".settings.json*")] == []


@pytest.mark.skipif(os.name == "nt", reason="modes are POSIX")
def test_the_write_keeps_the_existing_mode(home):
    paths.SETTINGS_PATH.chmod(0o640)
    switch.write_settings_atomically(paths.SETTINGS_PATH, {"a": 1})
    assert os.stat(paths.SETTINGS_PATH).st_mode & 0o777 == 0o640


def test_a_serialisation_error_never_reaches_the_disk(home):
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    with pytest.raises(TypeError):
        switch.write_settings_atomically(paths.SETTINGS_PATH, {"bad": object()})
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before


def test_backup_names_are_unique_within_a_second(home):
    first = switch.new_backup_path(paths.SETTINGS_PATH)
    first.write_text("{}")
    second = switch.new_backup_path(paths.SETTINGS_PATH)
    assert first != second and ".backup.path-" in second.name


def test_the_listing_is_newest_first_and_shows_what_each_backup_points_at(home):
    folder = paths.SETTINGS_PATH.parent
    (folder / "settings.json.backup.path-20260101_000001").write_text(json.dumps({"env": {"ANTHROPIC_BASE_URL": "http://a"}}))
    (folder / "settings.json.backup.path-20260101_000002").write_text(json.dumps({"env": {paths.BEDROCK_FLAG: "1", "ANTHROPIC_MODEL": "mx"}}))
    (folder / "settings.json.backup.path-20260101_000003").write_text("not json")
    rows = switch.list_backups()
    assert [r["timestamp"] for r in rows] == ["20260101_000003", "20260101_000002", "20260101_000001"]
    assert [r["index"] for r in rows] == [0, 1, 2]
    assert rows[0]["base_url"] == "(subscription)" and rows[1]["base_url"] == "(cloud-native mx)" and rows[2]["base_url"] == "http://a"


# --- restore --------------------------------------------------------------------

def make_backup(name, config):
    path = paths.SETTINGS_PATH.parent / f"settings.json.backup.path-{name}"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_restore_needs_confirmation_a_choice_and_a_backup(home):
    with pytest.raises(ValueError, match="confirm"):
        switch.restore_backup(latest=True)
    with pytest.raises(FileNotFoundError):
        switch.restore_backup(latest=True, confirm=True)
    make_backup("20260101_000001", {"env": {}})
    with pytest.raises(ValueError, match="choose a backup"):
        switch.restore_backup(confirm=True)
    with pytest.raises(FileNotFoundError):
        switch.restore_backup("settings.json.backup.path-missing", confirm=True)


def test_restore_verifies_the_backups_target_first_and_changes_nothing_on_failure(home, gateway):
    make_backup("20260101_000001", {"env": {"ANTHROPIC_BASE_URL": gateway(status=500, body={"e": 1}).url}})
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="failed verification"):
        switch.restore_backup(latest=True, confirm=True, prove=False)
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before
    assert len(switch.list_backups()) == 1  # no pre-restore backup was left


def test_restore_is_surgical_and_reversible(home, gateway):
    url = gateway(body=MESSAGE).url
    make_backup("20260101_000001", {"env": {"ANTHROPIC_BASE_URL": url}, "apiKeyHelper": "keep-me", "theme": "light"})
    # a backup with a helper verifies with the key the helper returns; use one that prints a value
    import sys
    helper = f'"{sys.executable}" -c "print(chr(107)*8)"'
    make_backup("20260101_000002", {"env": {"ANTHROPIC_BASE_URL": url}, "apiKeyHelper": helper, "theme": "light"})
    result = switch.restore_backup("settings.json.backup.path-20260101_000002", confirm=True, prove=False)
    now = settings()
    assert now["env"] == {"ANTHROPIC_BASE_URL": url} and now["apiKeyHelper"] == helper
    assert now["theme"] == "dark"  # sections outside env and the helper are not restored
    assert json.loads(Path(result["pre_restore_backup"]).read_text())["env"]["KEEP"] == "1"


def test_restore_drops_a_helper_the_backup_did_not_have(home, gateway):
    make_backup("20260101_000001", {"env": {"ANTHROPIC_BASE_URL": gateway(body=MESSAGE).url}})
    switch.restore_backup(latest=True, confirm=True, prove=False)
    assert "apiKeyHelper" not in settings()


def test_a_legacy_backup_with_a_literal_is_refused_unless_the_human_allows_it(home, gateway):
    make_backup("20260101_000001", {"env": {"ANTHROPIC_BASE_URL": gateway(body=MESSAGE).url, "ANTHROPIC_AUTH_TOKEN": CANARY}})
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        switch.restore_backup(latest=True, confirm=True, prove=False)
    assert "literal credential" in str(raised.value) and CANARY not in str(raised.value)
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before
    switch.restore_backup(latest=True, confirm=True, prove=False, allow_literal=True)
    assert settings()["env"]["ANTHROPIC_AUTH_TOKEN"] == CANARY


def test_a_backup_that_does_not_parse_is_refused(home):
    (paths.SETTINGS_PATH.parent / "settings.json.backup.path-20260101_000001").write_text("{broken")
    with pytest.raises(ValueError, match="does not parse"):
        switch.restore_backup(latest=True, confirm=True, prove=False)


def test_restore_gates_a_subscription_backup_on_the_login(home):
    make_backup("20260101_000001", {"env": {}})
    with pytest.raises(ValueError, match="no login"):
        switch.restore_backup(latest=True, confirm=True, prove=False)
    paths.CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
    assert switch.restore_backup(latest=True, confirm=True, prove=False)["restored"]


def test_a_failed_proof_removes_the_pre_restore_backup(home, gateway, monkeypatch):
    make_backup("20260101_000001", {"env": {"ANTHROPIC_BASE_URL": gateway(body=MESSAGE).url}})
    monkeypatch.setattr(switch, "prove_launch", lambda overlay, **k: {"ok": False, "detail": "no", "models": []})
    with pytest.raises(ValueError, match="did not answer"):
        switch.restore_backup(latest=True, confirm=True)
    assert len(switch.list_backups()) == 1


def test_the_atomic_write_flushes_to_disk(home, monkeypatch):
    calls = []
    real = os.fsync
    monkeypatch.setattr(switch.os, "fsync", lambda fd: (calls.append(fd), real(fd))[1])
    switch.write_settings_atomically(paths.SETTINGS_PATH, {"a": 1})
    assert calls


def test_a_literal_is_a_literal_with_or_without_a_helper_next_to_it(home, gateway):
    import sys
    helper = f'"{sys.executable}" -c "print(chr(107)*8)"'
    for env in ({"ANTHROPIC_AUTH_TOKEN": CANARY}, {"ANTHROPIC_API_KEY": CANARY}):
        assert switch._holds_literal({"env": env}) is True
        assert switch._holds_literal({"env": env, "apiKeyHelper": helper}) is True
    assert switch._holds_literal({"env": {}, "apiKeyHelper": helper}) is False
    assert switch._holds_literal({"env": {"ANTHROPIC_AUTH_TOKEN": "", "ANTHROPIC_API_KEY": ""}}) is False


def test_a_backup_with_a_literal_and_a_helper_is_refused_without_consent_and_restored_with_it(home, gateway):
    import sys
    helper = f'"{sys.executable}" -c "print(chr(107)*8)"'
    url = gateway(body=MESSAGE).url
    make_backup("20260101_000001", {"env": {"ANTHROPIC_BASE_URL": url, "ANTHROPIC_AUTH_TOKEN": CANARY}, "apiKeyHelper": helper})
    before = paths.SETTINGS_PATH.read_text(encoding="utf-8")
    with pytest.raises(ValueError) as raised:
        switch.restore_backup(latest=True, confirm=True, prove=False)
    assert "literal credential" in str(raised.value) and CANARY not in str(raised.value)
    assert paths.SETTINGS_PATH.read_text(encoding="utf-8") == before
    assert switch.restore_backup(latest=True, confirm=True, prove=False, allow_literal=True)["restored"]
