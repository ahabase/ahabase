"""Discovery (AHA-0024 R3a): local availability and the per-machine registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from ahabase.llm import discovery, paths


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(paths, "CREDENTIALS_PATH", tmp_path / ".credentials.json")
    monkeypatch.setattr(paths, "AWS_CREDENTIALS_PATH", tmp_path / "aws" / "credentials")
    monkeypatch.setattr(paths, "AWS_SSO_CACHE_PATH", tmp_path / "aws" / "sso")
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: False)
    for name in ("CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_MODEL", "AWS_ACCESS_KEY_ID", "GW_KEY"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


LADDER = {
    "gw": {"base_url": "http://gw", "model": "m", "auth": "env:GW_KEY"},
    "vault": {"base_url": "http://v", "model": "m", "auth": "safe://MYKEY"},
    "helper": {"base_url": "http://h", "model": "m", "auth": "env:UNSET", "key_helper": "true"},
}


def rows(**kwargs):
    return {r["path"]: r for r in discovery.assess_local_availability(env={}, process_env={}, **kwargs)}


def test_native_routes_are_assessed_by_presence(home):
    found = rows()
    assert not found["claude-pro"]["available"] and not found["bedrock"]["available"]
    paths.CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
    assert rows()["claude-pro"]["available"]


def test_a_variable_token_checks_the_settings_then_the_process(home):
    assert rows(builtin=LADDER)["gw"] == {"path": "gw", "available": False, "evidence": "GW_KEY not set", "current": False}
    both = discovery.assess_local_availability(env={"GW_KEY": "x"}, process_env={}, builtin=LADDER)
    assert [r for r in both if r["path"] == "gw"][0]["evidence"] == "settings env: GW_KEY"
    proc = discovery.assess_local_availability(env={}, process_env={"GW_KEY": "x"}, builtin=LADDER)
    assert [r for r in proc if r["path"] == "gw"][0]["evidence"] == "process env: GW_KEY"


def test_a_key_helper_counts_as_declared(home):
    assert rows(builtin=LADDER)["helper"]["available"]


def test_a_safe_reference_is_available_when_the_manifest_names_it(home, monkeypatch):
    class Manifest:
        def entries(self):
            return {"MYKEY": object()}
    import ahabase.safe as safe_module
    monkeypatch.setattr(safe_module, "Safe", Manifest)
    assert rows(builtin=LADDER)["vault"]["evidence"] == "safe entry: MYKEY"
    monkeypatch.setattr(Manifest, "entries", lambda self: {})
    assert not rows(builtin=LADDER)["vault"]["available"]


def test_the_registry_round_trips_and_an_unreadable_one_reads_as_empty(home):
    target = home / "reg.yml"
    assert discovery.load_registry(registry_path=target)["machines"] == {}
    assert discovery.save_registry({"version": "v", "machines": {"m": {"x": 1}}}, registry_path=target)
    assert discovery.load_registry(registry_path=target)["machines"] == {"m": {"x": 1}}
    target.write_text(": : [", encoding="utf-8")
    assert discovery.load_registry(registry_path=target)["machines"] == {}
    assert discovery.save_registry({}, registry_path=home / "no" / "such" / "dir" / "reg.yml")


def test_discover_records_this_machine_only(home):
    target = home / "reg.yml"
    result = discovery.discover(env={}, registry_path=target, builtin=LADDER)
    assert result["registry_saved"] and result["shape_known"] and result["active"] == "claude-pro"
    entry = discovery.load_machine_availability(registry_path=target)
    assert set(entry["paths"]) >= {"claude-pro", "bedrock", "gw"}
    assert discovery.load_machine_availability(machine="another-machine", registry_path=target) is None


@pytest.mark.filterwarnings("error::DeprecationWarning")
def test_the_registry_timestamp_is_utc_and_uses_no_deprecated_clock(home):
    from datetime import datetime, timezone
    target = home / "reg.yml"
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    discovery.discover(env={}, registry_path=target)
    entry = discovery.load_machine_availability(registry_path=target)
    stamp = entry["checked_at"]
    assert stamp.endswith("Z")
    moment = datetime.fromisoformat(stamp[:-1])
    assert 0 <= (moment - before).total_seconds() < 5
    assert entry["paths"]["claude-pro"]["checked_at"] == stamp


def test_an_unrecognised_shape_is_a_candidate_never_an_edit(home):
    result = discovery.discover(env={"ANTHROPIC_BASE_URL": "http://unknown"}, update_registry=False)
    assert not result["shape_known"] and result["registration_candidate"]["base_url"] == "http://unknown"
    assert not result["registry_saved"]


def test_the_default_registry_lives_in_the_instance_config(home):
    assert discovery.get_registry_path() == home / "ws" / "_config" / discovery.REGISTRY_FILENAME
