"""The session payload and the key helper (AHA-0024 R3c)."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from ahabase.llm import paths, session

CANARY = "CANARY-session-0123456789abcdef"
EXE = os.path.abspath("/opt/bin/ahabase")


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    return tmp_path


LADDER = {
    "by-env": {"base_url": "http://a", "model": "m", "auth": "env:SESSION_KEY",
               "tier_models": {"HAIKU": "small"}},
    "by-safe": {"base_url": "http://b", "model": "m", "auth": "safe://VAULT"},
    "by-helper": {"base_url": "http://c", "model": "m", "auth": "env:UNUSED", "key_helper": "my-helper"},
    "small-ctx": {"base_url": "http://d", "model": "m", "auth": "env:K", "context_window": 1000},
    "pinned": {"base_url": "http://e", "model": "pm", "auth": "env:K", "pin_model": True},
    "bad-pin": {"base_url": "", "model": "m", "auth": "env:K", "pin_model": True},
}


def spec(path_id, **kwargs):
    return session.session_env(path_id, env=kwargs.pop("env", {}), builtin=LADDER, executable=EXE, **kwargs)


def test_the_helper_command_is_absolute_and_quoted(monkeypatch):
    command = session.helper_command("a b", EXE)
    assert os.path.abspath(EXE) in command
    assert "'a b'" in command or '"a b"' in command  # one argument, quoted, not split
    relative = session.helper_command("p", "relative/ahabase")
    assert os.path.abspath("relative/ahabase") in relative
    monkeypatch.setattr(session.shutil, "which", lambda name: "/found/ahabase")
    assert os.path.abspath("/found/ahabase") in session.helper_command("p")
    monkeypatch.setattr(session.shutil, "which", lambda name: None)
    with pytest.raises(ValueError, match="not on PATH"):
        session.helper_command("p")


def test_a_variable_token_path_carries_the_helper_and_no_token():
    result = spec("by-env")
    assert result["settings"]["apiKeyHelper"] == session.helper_command("by-env", EXE)
    assert result["env"]["ANTHROPIC_AUTH_TOKEN"] == "" and result["env"]["ANTHROPIC_API_KEY"] == ""
    assert result["auth_env"] == "SESSION_KEY" and result["launchable"]
    assert result["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == "small" and result["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] == "m"
    assert result["env"][paths.BEDROCK_FLAG] == "" and result["env"]["ANTHROPIC_MODEL"] == ""


def test_a_safe_reference_path_carries_the_helper_too():
    result = spec("by-safe")
    assert result["settings"]["apiKeyHelper"].endswith("llm key by-safe") or "by-safe" in result["settings"]["apiKeyHelper"]
    assert result["auth_env"] is None


def test_a_path_with_its_own_helper_keeps_it():
    assert spec("by-helper")["settings"] == {"apiKeyHelper": "my-helper"}


def test_native_routes_unset_every_override():
    pro = spec("claude-pro")["env"]
    assert all(pro[key] == "" for key in paths.OAUTH_REMOVED_KEYS) and pro[paths.BEDROCK_FLAG] == ""
    cloud = spec("bedrock", region="eu-1", env={"AWS_PROFILE": "p"})["env"]
    assert cloud[paths.BEDROCK_FLAG] == "1" and cloud["AWS_REGION"] == "eu-1" and cloud["AWS_PROFILE"] == "p"


def test_the_pin_and_the_context_floor():
    assert spec("pinned")["env"]["ANTHROPIC_MODEL"] == "pm"
    assert "floor" in spec("small-ctx")["context_window_warning"]
    assert spec("by-env")["context_window_warning"] is None
    with pytest.raises(ValueError):
        spec("bad-pin")
    with pytest.raises(ValueError):
        spec("nope")


def test_overrides_from_the_caller_are_merged_last():
    assert spec("by-env", env_overrides={"CLAUDE_CODE_AUTO_COMPACT_WINDOW": "123", "ANTHROPIC_MODEL": "x"})["env"][
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW"] == "123"


def out(path_id, tmp_path, **kwargs):
    return session.session_env_out(path_id, env=kwargs.pop("env", {"SESSION_KEY": CANARY, "K": "x"}),
                                   epic="e", builtin=LADDER, executable=EXE, **kwargs)


def test_the_payload_file_never_holds_the_value(home):
    written = out("by-env", home)
    text = open(written["file"], encoding="utf-8").read()
    assert CANARY not in text and json.loads(text)["apiKeyHelper"]


def test_one_file_per_path_is_overwritten_not_accumulated(home):
    first = out("by-env", home)["file"]
    second = out("by-env", home)["file"]
    assert first == second
    assert len(list((home / "ws" / "_data" / "e" / "session-env").glob("*.json"))) == 1


@pytest.mark.skipif(os.name == "nt", reason="owner-only modes are POSIX")
def test_the_payload_file_is_owner_only(home):
    assert os.stat(out("by-env", home)["file"]).st_mode & 0o777 == 0o600


def test_an_unset_variable_is_refused_and_epic_is_required(home):
    with pytest.raises(ValueError, match="SESSION_KEY"):
        out("by-env", home, env={})
    with pytest.raises(TypeError):
        session.session_env_out("by-env", env={}, builtin=LADDER)  # no epic: no bare data-dir call


def test_an_explicit_out_path_is_honoured(home):
    target = home / "x" / "p.json"
    assert out("by-env", home, out_path=target)["file"] == str(target) and target.exists()


def check(path_id, env=None):
    return session.session_env_check(path_id, env=env or {}, builtin=LADDER)


def test_the_offline_check_reports_presence_only(home):
    assert not check("nope")["ok"]
    assert not check("by-env")["ok"] and check("by-env", {"SESSION_KEY": CANARY})["ok"]
    assert CANARY not in json.dumps(check("by-env", {"SESSION_KEY": CANARY}))
    assert check("by-safe")["ok"] and "bound" in check("by-safe")["detail"]
    assert check("claude-pro")["ok"]
    ok = {**LADDER, "h": {"base_url": "u", "model": "m", "key_helper": f'"{sys.executable}" -c "print(1)"'}}
    assert session.session_env_check("h", builtin=ok)["ok"]
    bad = {"h": {"base_url": "u", "model": "m", "key_helper": f'"{sys.executable}" -c "import sys; sys.exit(1)"'}}
    assert not session.session_env_check("h", builtin=bad)["ok"]


# --- the key helper -----------------------------------------------------------

def key(path_id, **kwargs):
    return session.key_value(path_id, builtin=LADDER, executable=EXE, **kwargs)


def test_an_env_path_returns_its_variable_and_refuses_when_unset():
    assert key("by-env", env={"SESSION_KEY": CANARY}) == CANARY
    with pytest.raises(ValueError):
        key("by-env", env={})


def test_the_inner_step_returns_only_what_the_safe_injected():
    assert key("by-safe", emit=True, env={session.EMIT_VARIABLE: CANARY}) == CANARY
    with pytest.raises(ValueError, match="safe run"):
        key("by-safe", emit=True, env={})


def test_a_safe_path_launches_the_safes_bound_run_never_resolve(home):
    seen = []

    def runner(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=CANARY + "\n", stderr="")
    assert key("by-safe", env={}, runner=runner) == CANARY
    command = seen[0]
    assert command[1:4] == ["safe", "run", "--env"]
    assert command[4] == f"{session.EMIT_VARIABLE}=safe://VAULT"
    assert command[5:] == ["--", command[0], "llm", "key", "by-safe", "--emit"]
    assert command[0] == os.path.abspath(EXE)


def test_a_refusal_by_the_safe_names_the_owner_step_without_a_value(home):
    runner = lambda command, **kwargs: subprocess.CompletedProcess(command, 1, stdout="", stderr="not bound")
    with pytest.raises(ValueError) as raised:
        key("by-safe", env={}, runner=runner)
    assert "safe bind VAULT" in str(raised.value) and "--prefix llm --prefix key" in str(raised.value)


def test_paths_that_need_no_key_helper_refuse_politely():
    with pytest.raises(ValueError):
        key("by-helper")
    with pytest.raises(ValueError):
        session.key_value("claude-pro", builtin=LADDER, executable=EXE)
    with pytest.raises(ValueError):
        key("nope")


# --- the runner and the bound helper are two programs (AHA-0026) --------------------------

def test_the_runner_and_the_bound_helper_are_named_separately(home):
    seen = []

    def runner(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=CANARY + "\n", stderr="")
    value = session.key_value("by-safe", env={}, builtin=LADDER, executable="/m/helper",
                              safe_executable="/a/ahabase", runner=runner)
    assert value == CANARY
    command = seen[0]
    assert command[0] == os.path.abspath("/a/ahabase")
    assert command[1:4] == ["safe", "run", "--env"]
    assert command[5:] == ["--", os.path.abspath("/m/helper"), "llm", "key", "by-safe", "--emit"]


def test_the_refusal_names_the_helper_the_owner_binds_not_the_runner(home):
    runner = lambda command, **kwargs: subprocess.CompletedProcess(command, 1, stdout="", stderr="not bound")
    with pytest.raises(ValueError) as raised:
        session.key_value("by-safe", env={}, builtin=LADDER, executable="/m/helper",
                          safe_executable="/a/ahabase", runner=runner)
    message = str(raised.value)
    assert os.path.abspath("/m/helper") in message and "safe bind VAULT" in message and CANARY not in message


def test_a_swapped_pair_is_visible_in_the_command(home):
    seen = []
    runner = lambda command, **kwargs: (seen.append(command), subprocess.CompletedProcess(command, 0, stdout=CANARY, stderr=""))[1]
    session.key_value("by-safe", env={}, builtin=LADDER, executable="/b/inner", safe_executable="/a/outer", runner=runner)
    assert seen[0][0].endswith("outer") and seen[0][6].endswith("inner")
