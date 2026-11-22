"""The door ``ahabase llm`` (AHA-0024 R3c)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from ahabase.cli import build_cli
from ahabase.llm import paths

CANARY = "CANARY-door-0123456789abcdef"


@pytest.fixture
def run(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(paths, "CREDENTIALS_PATH", tmp_path / ".credentials.json")
    monkeypatch.setattr(paths, "AWS_CREDENTIALS_PATH", tmp_path / "aws" / "credentials")
    monkeypatch.setattr(paths, "AWS_SSO_CACHE_PATH", tmp_path / "aws" / "sso")
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: False)
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    cli = build_cli()
    return lambda *args, **kw: CliRunner().invoke(cli, ["llm", *args], **kw)


def test_the_door_is_registered_with_its_commands(run):
    result = run("--help")
    assert result.exit_code == 0
    for name in ("path-list", "discover", "path-verify", "path-switch", "path-restore", "session-env", "key"):
        assert name in result.output


def test_path_list_shows_native_routes_and_the_one_in_force(run):
    result = run("path-list")
    assert "claude-pro" in result.output and "bedrock" in result.output and result.output.count("*") >= 1


def test_discover_reports_local_availability_and_writes_the_registry(run, tmp_path):
    result = run("discover")
    assert result.exit_code == 0 and "claude-pro" in result.output
    assert (tmp_path / "ws" / "_config" / "llm-paths-registry.yml").exists()
    assert run("discover", "--no-registry").exit_code == 0


def test_path_verify_reports_a_failure_with_its_class_and_hint(run):
    result = run("path-verify", "claude-pro")
    assert result.exit_code == 1 and "failed" in result.output and "class:" in result.output
    (paths.CREDENTIALS_PATH).write_text("{}")
    assert run("path-verify", "claude-pro").exit_code == 0
    assert run("path-verify", "no-such-path").exit_code == 1


def test_a_switch_without_confirm_is_refused(run):
    result = run("path-switch", "claude-pro")
    assert result.exit_code != 0 and "confirm" in result.output


def test_restore_lists_backups_when_given_no_choice(run, tmp_path):
    (tmp_path / "settings.json").write_text("{}")
    (tmp_path / "settings.json.backup.path-20260101_000001").write_text(json.dumps({"env": {}}))
    result = run("path-restore")
    assert result.exit_code == 0 and "settings.json.backup.path-20260101_000001" in result.output


def test_session_env_prints_a_payload_without_a_value_and_checks_offline(run, monkeypatch):
    shown = run("session-env", "claude-pro")
    assert shown.exit_code == 0 and json.loads(shown.output)["path"] == "claude-pro"
    assert run("session-env", "claude-pro", "--check").exit_code == 0
    assert run("session-env", "nope", "--check").exit_code == 1
    assert run("session-env", "nope").exit_code != 0


def test_key_takes_one_path_id_and_one_hidden_flag_and_nothing_else(run):
    from ahabase.cli_llm import key
    assert [p.name for p in key.params] == ["path_id", "emit"]
    emit = [p for p in key.params if p.name == "emit"][0]
    assert emit.hidden and emit.is_flag
    assert run("key", "a", "b").exit_code != 0  # a second argument is refused
    assert run("key", "--reveal-all", "a").exit_code != 0  # no other option exists


def test_key_emits_only_what_was_injected_and_refuses_otherwise(run):
    assert run("key", "claude-pro", "--emit").exit_code != 0
    injected = run("key", "p", "--emit", env={"AHABASE_LLM_KEY": CANARY})
    assert injected.exit_code == 0 and injected.output.strip() == CANARY


def test_the_door_reports_a_refused_credential_with_the_same_class_as_the_search(run, tmp_path):
    variants = tmp_path / "ws" / "_config" / "llm-paths-variants.yaml"
    variants.parent.mkdir(parents=True)
    variants.write_text("paths:\n  vault: {status: available, base_url: 'http://127.0.0.1:1', model: m, auth: 'safe://NOENTRY'}\n",
                        encoding="utf-8")
    result = run("path-verify", "vault")
    assert result.exit_code == 1 and "class: config" in result.output


# --- direct use: the door is its own bound helper and runner; session-launch (AHA-0027) ----------

def test_session_launch_is_registered(run):
    assert "session-launch" in run("--help").output


def test_the_door_names_itself_to_the_library_for_verify_switch_and_key(run, monkeypatch):
    from ahabase import cli_llm
    from ahabase.llm import session, switch, verify
    seen = {}

    def record(name, result):
        def fake(*args, **kwargs):
            seen[name] = kwargs
            return result
        return fake
    monkeypatch.setattr(verify, "verify_path", record("verify", {"ok": True, "status": 200, "detail": "stub"}))
    monkeypatch.setattr(switch, "switch_path", record("switch", {"backup": "b"}))
    monkeypatch.setattr(session, "key_value", record("key", "k"))
    run("path-verify", "claude-pro")
    run("path-switch", "claude-pro", "--confirm")
    run("key", "claude-pro")
    door = cli_llm._door()
    for name in ("verify", "switch", "key"):
        assert seen[name]["executable"] == door and seen[name]["safe_executable"] == door, name


def test_the_payload_helper_command_is_the_door(run, monkeypatch, tmp_path):
    from ahabase import cli_llm
    monkeypatch.setenv("CANARY_KEY", CANARY)
    variants = tmp_path / "ws" / "_config" / "llm-paths-variants.yaml"
    variants.parent.mkdir(parents=True)
    variants.write_text("paths:\n  gw:\n    status: available\n    base_url: https://gw.example\n    model: m\n    auth: env:CANARY_KEY\n")
    out = tmp_path / "pin.json"
    result = run("session-env", "gw", "--out", str(out))
    assert result.exit_code == 0, result.output
    payload = json.loads(out.read_text())
    assert payload["apiKeyHelper"].startswith(cli_llm._door()) and payload["apiKeyHelper"].endswith("llm key gw")
    assert CANARY not in out.read_text() and CANARY not in result.output


def test_session_launch_hands_the_payload_to_claude_and_passes_the_arguments(run, monkeypatch, tmp_path):
    from ahabase import cli_llm
    monkeypatch.setattr(cli_llm.shutil, "which", lambda name: "/fixture/bin/claude" if name == "claude" else None)
    launched = []
    monkeypatch.setattr(cli_llm, "_exec", lambda program, argv: launched.append((program, argv)))
    monkeypatch.setenv("AHABASE_DATA_DIR", str(tmp_path / "data"))
    result = run("session-launch", "claude-pro", "--model", "m1", "--continue")
    assert result.exit_code == 0, result.output
    program, argv = launched[0]
    assert program == "/fixture/bin/claude" and argv[:2] == ["/fixture/bin/claude", "--settings"]
    assert argv[3:] == ["--model", "m1", "--continue"]
    assert Path(argv[2]).exists() and CANARY not in Path(argv[2]).read_text()


def test_session_launch_refuses_an_unknown_path_and_a_missing_claude(run, monkeypatch, tmp_path):
    from ahabase import cli_llm
    monkeypatch.setattr(cli_llm, "_exec", lambda program, argv: pytest.fail("must not launch"))
    monkeypatch.setenv("AHABASE_DATA_DIR", str(tmp_path / "data"))
    assert run("session-launch", "no-such-path").exit_code != 0
    monkeypatch.setattr(cli_llm.shutil, "which", lambda name: None)
    missing = run("session-launch", "claude-pro")
    assert missing.exit_code != 0 and "claude is not on PATH" in missing.output and "--settings" in missing.output


def test_the_door_never_names_a_directory_or_a_program_that_merely_starts_with_its_name(monkeypatch, tmp_path):
    from ahabase import cli_llm
    directory = tmp_path / "ahabase"
    directory.mkdir()
    impostor = tmp_path / "ahabase-evil"
    impostor.write_text("#!/bin/sh\n")
    real = tmp_path / "bin" / "ahabase"
    real.parent.mkdir()
    real.write_text("#!/bin/sh\n")
    beside = tmp_path / "venv" / "bin"
    beside.mkdir(parents=True)
    (beside / "ahabase").write_text("#!/bin/sh\n")
    monkeypatch.setattr(cli_llm.sys, "executable", str(beside / "python"))
    for argv0, expected in ((str(directory), beside / "ahabase"), (str(impostor), beside / "ahabase"),
                            (str(real), real), ("", beside / "ahabase")):
        monkeypatch.setattr(cli_llm.sys, "argv", [argv0])
        named = Path(cli_llm._door())
        assert named == expected and named.is_file() and named.name.lower() in ("ahabase", "ahabase.exe"), argv0


def test_the_resolved_door_in_the_real_environment_is_a_file_called_ahabase(run):
    from ahabase import cli_llm
    named = Path(cli_llm._door())
    assert named.name.lower() in ("ahabase", "ahabase.exe")
