"""The safe's hardening (AHA-0007): threat model T2, T9-T12, on fictional values."""

from __future__ import annotations

import os
import subprocess
import sys

import keyring
import pytest
from click.testing import CliRunner

import ahabase.cli_safe as cli_safe
from ahabase.cli import build_cli
from ahabase.plugins import Registry
from ahabase.safe import Safe, SafeError, child_env, package_root

import conftest
from test_safe import FAKE_VALUE, FakeKeyring

OTHER = "other-exported-value-987"


@pytest.fixture
def fake_keyring():
    fake = FakeKeyring()
    keyring.set_keyring(fake)
    return fake


@pytest.fixture
def owner(monkeypatch):
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)


def _cli():
    return build_cli(Registry(reserved={"doctor", "safe"}))


def _exe(path, body="exit 0", win_body="exit /b 0"):
    """An installed command (not an interpreter), shipped as the OS's
    script variant (.sh here, .bat on Windows) - AHA-0014 R4."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        path = path.parent / (path.name + ".bat")
        path.write_text(f"@echo off\r\n{win_body}\r\n")
        return str(path)
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(0o755)
    return str(path)


needs_symlinks = pytest.mark.skipif(not conftest.SYMLINKS,
                                    reason="symlinks need Developer Mode or an elevated Windows runner")


def _set(runner, name="tok"):
    out = runner.invoke(_cli(), ["safe", "set", name], input=FAKE_VALUE + "\n")
    assert out.exit_code == 0, out.output


def _bind(runner, name, path, *extra):
    return runner.invoke(_cli(), ["safe", "bind", name, path, *extra], input=f"{name}\n")


# T2: what can be bound ---------------------------------------------------

@pytest.mark.parametrize("tool", ["sh", "bash", "env", "xargs", "python3.14", "node", "curl", "gh", "git"])
def test_listed_names_cannot_be_bound(
        fake_keyring, owner, tmp_path, tool):
    runner = CliRunner()
    _set(runner)
    out = _bind(runner, "tok", _exe(tmp_path / "bin" / tool))
    assert out.exit_code != 0 and "would bind nothing" in out.output, out.output
    assert "installed command" in out.output  # the way through is named


def test_bind_needs_an_absolute_path_and_an_executable(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    relative = _bind(runner, "tok", "fixture-tool")
    assert relative.exit_code != 0 and "absolute path" in relative.output
    plain = tmp_path / "not-exe"
    plain.write_text("x")
    if sys.platform == "win32":
        # no exec bit on this OS: an existing file passes the OS's check, so the
        # refusal line there is the suffix (PATHEXT) not a mode bit - stated,
        # not skipped (the portability constraint: honest per-OS statements)
        assert _bind(runner, "tok", str(plain)).exit_code == 0
    else:
        assert _bind(runner, "tok", str(plain)).exit_code != 0


def test_bind_is_the_owners_step(fake_keyring, tmp_path):
    runner = CliRunner()
    _set(runner)
    out = runner.invoke(_cli(), ["safe", "bind", "tok", _exe(tmp_path / "bin" / "tool")])
    assert out.exit_code != 0 and "interactive terminal" in out.output


# T2: run checks before resolving -------------------------------------------

def test_unbound_command_is_refused_before_any_value_is_read(fake_keyring, owner, tmp_path, monkeypatch):
    runner = CliRunner()
    _set(runner)
    reads = []
    original = Safe.get
    monkeypatch.setattr(Safe, "get", lambda self, name: reads.append(name) or original(self, name))
    tool = _exe(tmp_path / "bin" / "tool")
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert out.exit_code != 0 and "not a bound consumer" in out.output
    assert f"ahabase safe bind tok {tool}" in out.output  # the way through
    assert reads == [] and FAKE_VALUE not in out.output


def test_an_earlier_executable_on_path_does_not_match(fake_keyring, owner, tmp_path, monkeypatch):
    runner = CliRunner()
    _set(runner)
    bound = _exe(tmp_path / "good" / "tool")
    assert _bind(runner, "tok", bound).exit_code == 0
    _exe(tmp_path / "evil" / "tool")
    monkeypatch.setenv("PATH", os.pathsep.join(
        [str(tmp_path / "evil"), str(tmp_path / "good"), os.environ["PATH"]]))
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", "tool"])
    assert out.exit_code != 0 and "not a bound consumer" in out.output


@needs_symlinks
def test_binding_survives_an_upgrade_but_not_a_move_elsewhere(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    v1 = _exe(tmp_path / "Cellar" / "tool" / "1.0" / "bin" / "tool")
    # the link carries the OS's script suffix: an extensionless link to a .bat
    # is not launchable on Windows (OSError 8, measured by the first lane run)
    link = tmp_path / "bin" / ("tool.bat" if sys.platform == "win32" else "tool")
    link.parent.mkdir(parents=True)
    link.symlink_to(v1)
    assert _bind(runner, "tok", str(link)).exit_code == 0
    assert package_root(str(link)) == str(tmp_path / "Cellar" / "tool")
    # an upgrade moves the real target inside the package root - still bound
    v2 = _exe(tmp_path / "Cellar" / "tool" / "2.0" / "bin" / "tool")
    link.unlink()
    link.symlink_to(v2)
    ok = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", str(link)])
    assert ok.exit_code == 0, ok.output
    # pointing the link elsewhere is refused, with the way through
    other = _exe(tmp_path / "elsewhere" / "tool")
    link.unlink()
    link.symlink_to(other)
    moved = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", str(link)])
    assert moved.exit_code != 0 and "outside its bound package" in moved.output
    assert "ahabase safe bind tok" in moved.output


def test_prefix_and_redirecting_options(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool, "--prefix", "run").exit_code == 0
    run = lambda *args: runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool, *args])
    assert run("run", "--select", "m").exit_code == 0
    wrong = run("debug")
    assert wrong.exit_code != 0 and "only with the arguments run" in wrong.output
    redirect = run("run", "--profiles-dir=/tmp/elsewhere")
    assert redirect.exit_code != 0 and "--allow --profiles-dir" in redirect.output
    assert _bind(runner, "tok", tool, "--prefix", "run", "--allow", "--target").exit_code == 0
    assert run("run", "--target", "dev").exit_code == 0


# T2, T12: the child's environment ------------------------------------------

def test_child_gets_a_working_base_and_no_other_exported_value(fake_keyring, owner, tmp_path, monkeypatch):
    runner = CliRunner()
    _set(runner)
    monkeypatch.setenv("OTHER_TOKEN", OTHER)
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.example:8080")
    monkeypatch.setenv("KEPT_SETTING", "kept")
    check = ('[ "$T" = "%s" ] && [ -z "$OTHER_TOKEN" ] && [ -n "$PATH" ] '
             '&& [ "$HTTPS_PROXY" = "http://proxy.example:8080" ] && [ "$KEPT_SETTING" = "kept" ]'
             % FAKE_VALUE)
    check_win = ('if not "%%T%%"=="%s" exit /b 1\r\nif not "%%OTHER_TOKEN%%"=="" exit /b 1\r\n'
                 'if "%%PATH%%"=="" exit /b 1\r\n'
                 'if not "%%HTTPS_PROXY%%"=="http://proxy.example:8080" exit /b 1\r\n'
                 'if not "%%KEPT_SETTING%%"=="kept" exit /b 1' % FAKE_VALUE)
    tool = _exe(tmp_path / "bin" / "tool", check, check_win)
    assert _bind(runner, "tok", tool, "--keep", "KEPT_SETTING").exit_code == 0
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--keep", "KEPT_SETTING", "--", tool])
    assert out.exit_code == 0, out.output
    assert OTHER not in str(child_env({"T": "x"}).values())


def test_keep_is_bound_per_variable_and_run_needs_a_secret(fake_keyring, owner, tmp_path, monkeypatch):
    """Review: --keep could hand any exported value to any command."""
    runner = CliRunner()
    _set(runner)
    monkeypatch.setenv("OTHER_TOKEN", OTHER)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    kept = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--keep", "OTHER_TOKEN", "--", tool])
    assert kept.exit_code != 0 and "--keep OTHER_TOKEN" in kept.output and OTHER not in kept.output
    bare = runner.invoke(_cli(), ["safe", "run", "--keep", "OTHER_TOKEN", "--", _exe(tmp_path / "bin" / "x")])
    assert bare.exit_code != 0 and "nothing to resolve" in bare.output


# review bypasses -------------------------------------------------------------

@needs_symlinks
def test_dot_dot_through_a_directory_symlink_is_refused(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    bound = _exe(tmp_path / "bound" / "tool")
    _exe(tmp_path / "evil" / "bound" / "tool")
    (tmp_path / "evil" / "x").mkdir()
    (tmp_path / "link").symlink_to(tmp_path / "evil" / "x")
    assert _bind(runner, "tok", bound).exit_code == 0
    trick = f"{tmp_path}/link/../bound/tool"
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", trick])
    assert out.exit_code != 0 and "contains '..'" in out.output


@needs_symlinks
def test_flat_bin_swap_to_another_program_is_refused(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    other = _exe(tmp_path / "bin" / "other")
    assert _bind(runner, "tok", tool).exit_code == 0
    os.unlink(tool)
    os.symlink(other, tool)
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert out.exit_code != 0 and "not the file it was bound to" in out.output


def test_a_changed_file_needs_rebinding_and_doctor_says_so(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    _exe(tmp_path / "bin" / "tool", "echo replaced", "echo replaced")
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert out.exit_code != 0 and "changed since it was bound" in out.output
    assert f"ahabase safe bind tok {tool}" in out.output  # the way through
    doctor = runner.invoke(_cli(), ["doctor"])
    assert "changed since it was bound" in doctor.output
    assert _bind(runner, "tok", tool).exit_code == 0
    assert runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool]).exit_code == 0


@needs_symlinks
def test_a_keg_link_that_now_leads_to_a_shell_is_refused(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    real = _exe(tmp_path / "Cellar" / "tool" / "1.0" / "bin" / "tool")
    shell = _exe(tmp_path / "Cellar" / "tool" / "1.0" / "bin" / "bash")
    link = tmp_path / "bin" / "tool"
    link.parent.mkdir(parents=True)
    link.symlink_to(real)
    assert _bind(runner, "tok", str(link)).exit_code == 0
    link.unlink()
    link.symlink_to(shell)
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", str(link)])
    assert out.exit_code != 0 and "would bind nothing" in out.output


@pytest.mark.parametrize("tool", ["make", "find", "tar", "vim", "less", "busybox", "npx", "docker"])
def test_tools_with_a_shell_escape_cannot_be_bound(fake_keyring, owner, tmp_path, tool):
    runner = CliRunner()
    _set(runner)
    out = _bind(runner, "tok", _exe(tmp_path / "bin" / tool))
    assert out.exit_code != 0 and "would bind nothing" in out.output


def test_an_abbreviated_redirecting_option_is_refused(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool, "--hos", "x"])
    assert out.exit_code != 0 and "--host" in out.output


def test_a_git_ignored_manifest_is_allowed(fake_keyring, tmp_path):
    """Review: an owner whose HOME is a dotfiles repository must not be locked out."""
    repo = tmp_path / "home"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / ".gitignore").write_text("safe.json\n")
    Safe(path=repo / "ahabase" / "_config" / "safe.json").set("tok", FAKE_VALUE)


def test_run_is_shell_free(fake_keyring, owner, tmp_path, monkeypatch):
    """Pinned: the binding rests on executing an argument list, never a shell string."""
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    calls = []

    def spy(argv, **kwargs):
        calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(cli_safe.subprocess, "run", spy)
    runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool, "a b; c"])
    (argv, kwargs), = calls
    assert isinstance(argv, list) and argv == [tool, "a b; c"]
    assert not kwargs.get("shell") and "executable" not in kwargs


# T2, T11: reveal and compare are the owner's ------------------------------

def test_reveal_needs_the_owner_and_the_typed_name(fake_keyring, tmp_path, monkeypatch):
    runner = CliRunner()
    _set(runner)
    agent = runner.invoke(_cli(), ["safe", "get", "tok", "--reveal"])
    assert agent.exit_code != 0 and FAKE_VALUE not in agent.output
    assert "interactive terminal" in agent.output
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)
    wrong = runner.invoke(_cli(), ["safe", "get", "tok", "--reveal"], input="other\n")
    assert wrong.exit_code != 0 and FAKE_VALUE not in wrong.output
    right = runner.invoke(_cli(), ["safe", "get", "tok", "--reveal"], input="tok\n")
    assert right.exit_code == 0 and FAKE_VALUE in right.output


def test_compare_needs_the_owner_and_refuses_bursts(fake_keyring, tmp_path, monkeypatch):
    runner = CliRunner()
    _set(runner)
    monkeypatch.setenv("CANDIDATE", "guess")
    agent = runner.invoke(_cli(), ["safe", "compare", "tok", "--env", "CANDIDATE"])
    assert agent.exit_code == 2 and "interactive terminal" in agent.output
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)
    codes = [runner.invoke(_cli(), ["safe", "compare", "tok", "--env", "CANDIDATE"], input="\n").exit_code
             for _ in range(cli_safe.COMPARE_LIMIT)]
    assert codes == [1] * cli_safe.COMPARE_LIMIT  # a shadow run's comparisons pass
    burst = runner.invoke(_cli(), ["safe", "compare", "tok", "--env", "CANDIDATE"], input="\n")
    assert burst.exit_code == 2 and "wait a minute" in burst.output


# T9: the manifest and the override variables -------------------------------

def test_override_variables_need_the_owner_and_doctor_reports_them(fake_keyring, tmp_path, monkeypatch):
    runner = CliRunner()
    monkeypatch.setenv("AHABASE_SAFE_MANIFEST", str(tmp_path / "elsewhere" / "safe.json"))
    tool = _exe(tmp_path / "bin" / "tool")
    out = runner.invoke(_cli(), ["safe", "run", "--", tool])
    assert out.exit_code != 0 and "AHABASE_SAFE_MANIFEST" in out.output
    assert "ahabase safe trust-location" in out.output  # the way through
    doctor = runner.invoke(_cli(), ["doctor"])
    assert "AHABASE_SAFE_MANIFEST is set" in doctor.output


def test_manifest_is_refused_inside_a_git_working_tree(fake_keyring, tmp_path):
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    with pytest.raises(SafeError, match="inside the git working tree"):
        Safe(path=repo / "_config" / "safe.json").set("tok", FAKE_VALUE)


def test_doctor_reports_a_bound_consumer_that_disappeared(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    os.unlink(tool)
    doctor = runner.invoke(_cli(), ["doctor"])
    assert doctor.exit_code == 1 and "no longer exists - rebind or unbind it" in doctor.output


def test_unbind(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    assert runner.invoke(_cli(), ["safe", "unbind", "tok", tool], input="tok\n").exit_code == 0
    again = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert again.exit_code != 0 and "not a bound consumer" in again.output


def test_unbind_and_delete_are_the_owners_steps(fake_keyring, tmp_path, monkeypatch):
    """Review: an agent could strip bindings or delete entries - a loss of access (T12)."""
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)
    assert _bind(runner, "tok", tool).exit_code == 0
    monkeypatch.setattr(cli_safe, "_interactive", lambda: False)
    for args in (["safe", "unbind", "tok", tool], ["safe", "delete", "tok"]):
        out = runner.invoke(_cli(), args)
        assert out.exit_code != 0 and "interactive terminal" in out.output, out.output
    assert "consumers: " + tool in runner.invoke(_cli(), ["safe", "list"]).output
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)
    assert runner.invoke(_cli(), ["safe", "delete", "tok"], input="tok\n").exit_code == 0


def test_a_trusted_location_lets_an_unattended_run_through(fake_keyring, tmp_path, monkeypatch):
    """Coordinator review: AHABASE_HOME is a legitimate setting - no lockout for services (T12)."""
    runner = CliRunner()
    monkeypatch.setenv("AHABASE_HOME", str(tmp_path / "work"))
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    monkeypatch.setattr(cli_safe, "_interactive", lambda: False)
    refused = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert refused.exit_code != 0 and "ahabase safe trust-location" in refused.output
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)
    trusted = runner.invoke(_cli(), ["safe", "trust-location"], input="_config\n")
    assert trusted.exit_code == 0, trusted.output
    monkeypatch.setattr(cli_safe, "_interactive", lambda: False)
    ok = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert ok.exit_code == 0, ok.output
    monkeypatch.setenv("AHABASE_HOME", str(tmp_path / "attacker"))
    other = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert other.exit_code != 0 and "has not trusted" in other.output


def test_future_comparison_times_do_not_lock_the_owner_out(fake_keyring, owner, tmp_path, monkeypatch):
    """Home primary review: a clock stepped back must not refuse compare forever (T12)."""
    import json as _json
    import time as _time
    runner = CliRunner()
    _set(runner)
    monkeypatch.setenv("CANDIDATE", "guess")
    limit = Safe().path.with_name("safe-compare.json")
    limit.write_text(_json.dumps({"tok": [_time.time() + 3600] * 10}))
    out = runner.invoke(_cli(), ["safe", "compare", "tok", "--env", "CANDIDATE"], input="\n")
    assert out.exit_code == 1, out.output  # compared (different), not refused
    limit.write_text("[1, 2, 3]")  # a record of the wrong shape counts nothing
    assert runner.invoke(_cli(), ["safe", "compare", "tok", "--env", "CANDIDATE"], input="\n").exit_code == 1


def test_a_damaged_manifest_is_named_with_a_way_through(fake_keyring, owner, tmp_path):
    """Third home lane: a truncated or unknown-key manifest raised a traceback."""
    runner = CliRunner()
    _set(runner)
    path = Safe().path
    data = _json_load(path)
    data["secrets"]["tok"]["future_field"] = "x"
    path.write_text(__import__("json").dumps(data))
    assert Safe().entries()["tok"].extra == {"future_field": "x"}  # unknown keys kept aside
    path.write_text('{"secrets": {')
    listed = runner.invoke(_cli(), ["safe", "list"])
    assert listed.exit_code != 0 and "cannot be read" in listed.output and "move" in listed.output
    assert "Traceback" not in listed.output
    doctor = runner.invoke(_cli(), ["doctor"])
    assert doctor.exit_code == 1 and "cannot be read" in doctor.output


def _json_load(path):
    import json as _json
    return _json.loads(path.read_text())


def test_a_relay_script_under_another_name_is_not_recognized(fake_keyring, owner, tmp_path):
    """Third home lane: the deny-list works by name - pinned, so the docs stay honest."""
    runner = CliRunner()
    _set(runner)
    relay = _exe(tmp_path / "bin" / "deploy.sh", 'exec "$@"', "%*")
    assert _bind(runner, "tok", relay).exit_code == 0  # a stated residual (T2), not a guarantee


def test_a_full_option_that_prefixes_another_is_exact(fake_keyring, owner, tmp_path):
    """Home primary round 2: --config prefixes --config-file; allowing --config must suffice."""
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool, "--allow", "--config").exit_code == 0
    ok = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool, "--config", "p.yaml"])
    assert ok.exit_code == 0, ok.output
    other = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool, "--config-file", "p"])
    assert other.exit_code != 0 and "--allow --config-file" in other.output


@pytest.mark.parametrize("field,bad", [("extra", "not-an-object"), ("consumers", "x"), ("consumers", 0), ("consumers", None), ("consumers", [1]), ("extra", ""), ("extra", 0), ("extra", None)])
def test_a_wrong_typed_field_is_named_not_a_traceback(fake_keyring, owner, tmp_path, field, bad):
    """Home primary round 2: a wrong-typed field still raised a traceback."""
    runner = CliRunner()
    _set(runner)
    path = Safe().path
    data = _json_load(path)
    data["secrets"]["tok"][field] = bad
    path.write_text(__import__("json").dumps(data))
    listed = runner.invoke(_cli(), ["safe", "list"])
    assert listed.exit_code != 0 and "malformed" in listed.output and "Traceback" not in listed.output


def test_run_on_a_malformed_manifest_is_named_too(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    _set(runner)
    path = Safe().path
    data = _json_load(path)
    data["secrets"]["tok"]["consumers"] = 0
    path.write_text(__import__("json").dumps(data))
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", _exe(tmp_path / "bin" / "t")])
    assert out.exit_code != 0 and "malformed" in out.output and "Traceback" not in out.output


@pytest.mark.parametrize("binding", [
    {"path": 5}, {"path": "/x", "prefix": "run"}, {"path": "/x", "allow": [1]},
    {"path": "/x", "keep": None}, {"path": "/x", "root": 0}, {"path": "/x", "digest": []}, {}])
def test_every_binding_field_is_shape_checked(fake_keyring, owner, tmp_path, binding):
    """Round 3: every field the checks rely on, not only the ones a reviewer tried."""
    runner = CliRunner()
    _set(runner)
    path = Safe().path
    data = _json_load(path)
    data["secrets"]["tok"]["consumers"] = [binding]
    path.write_text(__import__("json").dumps(data))
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", "/x"])
    assert out.exit_code != 0 and "malformed" in out.output and "Traceback" not in out.output


@pytest.mark.parametrize("field,bad", [("store", 5), ("expires", 20270101), ("purpose", None)])
def test_every_entry_field_is_shape_checked(fake_keyring, owner, tmp_path, field, bad):
    runner = CliRunner()
    _set(runner)
    path = Safe().path
    data = _json_load(path)
    data["secrets"]["tok"][field] = bad
    path.write_text(__import__("json").dumps(data))
    for args in (["safe", "list"], ["doctor"]):
        out = runner.invoke(_cli(), args)
        assert out.exit_code != 0 and "malformed" in out.output and "Traceback" not in out.output, out.output


def test_no_manifest_shape_raises_anything_but_a_named_refusal(fake_keyring, owner, tmp_path):
    """Fuzz over field values: any outcome is a result or a SafeError, never a raw error."""
    import itertools
    import json as _json
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    path = Safe().path
    base = _json_load(path)
    odd = [0, 1, None, "", "x", [], [1], {}, {"a": 1}, True, 1.5]
    fields = list(base["secrets"]["tok"].keys())
    binding_fields = list(base["secrets"]["tok"]["consumers"][0].keys())
    cases = [("entry", f, v) for f, v in itertools.product(fields, odd)]
    cases += [("binding", f, v) for f, v in itertools.product(binding_fields, odd)]
    for where, field, value in cases:
        data = _json.loads(_json.dumps(base))
        target = data["secrets"]["tok"] if where == "entry" else data["secrets"]["tok"]["consumers"][0]
        target[field] = value
        path.write_text(_json.dumps(data))
        s = Safe()
        for call in (s.entries, lambda: s.health(), lambda: s.check_consumer("tok", [tool])):
            try:
                call()
            except SafeError:
                pass


def test_a_vanished_bound_consumer_is_named_at_run(fake_keyring, owner, tmp_path):
    """Home primary round 4 note: a deleted bound file raised FileNotFoundError at the check."""
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    os.unlink(tool)
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool])
    assert out.exit_code != 0 and "no longer exists" in out.output and "Traceback" not in out.output
    assert "ahabase safe unbind tok" in out.output


@pytest.mark.parametrize("abbrev", ["--h", "--u", "--c", "--t", "--p", "--e", "--s"])
def test_one_letter_abbreviations_are_refused(fake_keyring, owner, tmp_path, abbrev):
    """Third home lane (executed): argparse takes --u as --url; every prefix length counts."""
    runner = CliRunner()
    _set(runner)
    tool = _exe(tmp_path / "bin" / "tool")
    assert _bind(runner, "tok", tool).exit_code == 0
    out = runner.invoke(_cli(), ["safe", "run", "--env", "T=safe://tok", "--", tool, abbrev, "x"])
    assert out.exit_code != 0 and "elsewhere" in out.output, out.output
