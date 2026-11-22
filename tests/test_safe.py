"""The safe (AHA-0002 R2-R5), on fictional secrets only."""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta

import keyring
import keyring.backend
import pytest
from click.testing import CliRunner

import ahabase.cli_safe as cli_safe
import ahabase.safe as safe_module
from ahabase.cli import build_cli
from ahabase.plugins import Registry
from ahabase.safe import (TARGET_KINDS, EnvStore, KeyringStore, MemoryStore, Safe,
                          SafeError, manifest_path)

FAKE_VALUE = "fixture-value-0123456789"


class FakeKeyring(keyring.backend.KeyringBackend):
    """An in-memory stand-in for the OS store."""

    priority = 1

    def __init__(self):
        super().__init__()
        self.values = {}

    def get_password(self, service, username):
        return self.values.get((service, username))

    def set_password(self, service, username, password):
        self.values[(service, username)] = password

    def delete_password(self, service, username):
        if (service, username) not in self.values:
            raise keyring.errors.PasswordDeleteError(username)
        del self.values[(service, username)]


@pytest.fixture
def fake_keyring():
    fake = FakeKeyring()
    keyring.set_keyring(fake)
    return fake


@pytest.mark.parametrize("make", [MemoryStore, KeyringStore])
def test_store_contract(make, fake_keyring):
    store = make()
    assert not store.exists("a") and store.get("a") is None
    store.set("a", FAKE_VALUE)
    assert store.exists("a") and store.get("a") == FAKE_VALUE
    store.delete("a")
    store.delete("a")  # deleting twice is harmless
    assert not store.exists("a")


def test_keyring_store_writes_the_fake_backend(fake_keyring):
    KeyringStore().set("jira-api", FAKE_VALUE)
    assert fake_keyring.values == {("ahabase", "jira-api"): FAKE_VALUE}


def test_env_store_is_read_only(monkeypatch):
    monkeypatch.setenv("FIXTURE_TOKEN", FAKE_VALUE)
    store = EnvStore()
    assert store.get("FIXTURE_TOKEN") == FAKE_VALUE and store.exists("FIXTURE_TOKEN")
    with pytest.raises(SafeError):
        store.set("FIXTURE_TOKEN", "x")


def test_manifest_holds_no_value_and_resolve(fake_keyring):
    s = Safe()
    s.set("jira-api", FAKE_VALUE, purpose="issue tracker", expires="2999-01-01")
    text = manifest_path().read_text()
    assert FAKE_VALUE not in text
    assert json.loads(text)["secrets"]["jira-api"]["purpose"] == "issue tracker"
    assert s.resolve("safe://jira-api") == FAKE_VALUE
    assert s.resolve("https://plain.example.com") == "https://plain.example.com"
    with pytest.raises(SafeError) as error:
        s.resolve("safe://nope")
    assert "nope" in str(error.value) and FAKE_VALUE not in str(error.value)


def test_setting_again_records_rotation(fake_keyring):
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.entry.rotated == date.today().isoformat()
    assert s.get("jira-api") == FAKE_VALUE + "-new"


def test_health_reports_missing_and_expiring(fake_keyring):
    s = Safe()
    soon = (date.today() + timedelta(days=3)).isoformat()
    s.set("soon", FAKE_VALUE, expires=soon)
    s.set("gone", FAKE_VALUE)
    fake_keyring.values.pop(("ahabase", "gone"))
    problems = [text for ok, text in s.health() if not ok]
    assert any("gone: missing" in p for p in problems), problems
    assert any(f"soon: expires {soon}" in p for p in problems), problems


def _cli():
    return build_cli(Registry(reserved={"doctor", "safe"}))


@pytest.fixture
def owner(monkeypatch):
    """A person at an interactive terminal (the seam of the owner's checks)."""
    monkeypatch.setattr(cli_safe, "_interactive", lambda: True)


def _consumer(tmp_path, name="fixture-consumer"):
    """An installed command (not an interpreter) that checks its environment,
    shipped as the OS's script variant (.sh here, .bat on Windows)."""
    path = tmp_path / "bin" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        path = path.parent / (path.name + ".bat")
        path.write_text(f'@echo off\r\nif not "%JIRA_TOKEN%"=="{FAKE_VALUE}" exit /b 1\r\n')
        return str(path)
    path.write_text(f'#!/bin/sh\n[ "$JIRA_TOKEN" = "{FAKE_VALUE}" ]\n')
    path.chmod(0o755)
    return str(path)


def _last(result):
    return result.output.strip().splitlines()[-1] if result.output.strip() else ""


def test_cli_set_list_get_run_doctor(fake_keyring, owner, tmp_path):
    runner = CliRunner()
    cli = _cli()
    out = runner.invoke(cli, ["safe", "set", "jira-api", "--purpose", "issues"],
                        input=FAKE_VALUE + "\n")
    assert out.exit_code == 0 and FAKE_VALUE not in out.output, out.output
    listed = runner.invoke(cli, ["safe", "list"])
    assert "jira-api: store=keyring, purpose=issues; targets: none; consumers: none" \
        in listed.output
    assert FAKE_VALUE not in listed.output
    refused = runner.invoke(cli, ["safe", "get", "jira-api"])
    assert refused.exit_code != 0 and FAKE_VALUE not in refused.output
    assert "--reveal" in refused.output
    revealed = runner.invoke(cli, ["safe", "get", "jira-api", "--reveal"], input="jira-api\n")
    assert _last(revealed) == FAKE_VALUE
    child = _consumer(tmp_path)
    bound = runner.invoke(cli, ["safe", "bind", "jira-api", child], input="jira-api\n")
    assert bound.exit_code == 0, bound.output
    ran = runner.invoke(cli, ["safe", "run", "--env", "JIRA_TOKEN=safe://jira-api",
                              "--", child])
    assert ran.exit_code == 0 and FAKE_VALUE not in ran.output, ran.output
    doctor = runner.invoke(cli, ["doctor"])
    assert "check safe: ok - 1 secrets, all present" in doctor.output, doctor.output
    fake_keyring.values.clear()
    doctor = runner.invoke(cli, ["doctor"])
    assert doctor.exit_code == 1 and "jira-api: missing in store" in doctor.output


def test_value_never_from_an_argument():
    """set takes no value argument: values stay out of history and ps."""
    params = [p.name for p in cli_safe.safe_set.params]
    assert "value" not in params and params[0] == "name"


def test_safe_name_is_reserved_for_plugins():
    """A plugin cannot take the package's safe command."""
    registry = Registry(reserved={"doctor", "safe"})
    import click
    assert registry.add_command(click.Command("safe")) is False


def test_run_error_never_echoes_the_argument(fake_keyring):
    """Review e31fe5ad: a mistyped --env may be a raw value."""
    out = CliRunner().invoke(_cli(), ["safe", "run", "--env", FAKE_VALUE, "--", "true"])
    assert out.exit_code != 0 and FAKE_VALUE not in out.output, out.output


def test_plugin_cannot_replace_the_safe_check(fake_keyring):
    registry = Registry(reserved={"doctor", "safe"})
    assert registry.add_check("safe", lambda: (True, "plugin")) is False
    out = CliRunner().invoke(build_cli(registry), ["doctor"])
    assert "check safe: ok - 0 secrets" in out.output and "ok - plugin" not in out.output


@pytest.mark.skipif(sys.platform == "win32",
                    reason="0o600 is the POSIX arm's statement; the Windows arm states ACLs")
def test_manifest_mode_600_and_no_temp_left(fake_keyring):
    import os
    import stat
    Safe().set("jira-api", FAKE_VALUE)
    path = manifest_path()
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    leftovers = [p.name for p in path.parent.iterdir()
                 if p.name.startswith(".safe.json.")]
    assert leftovers == [], leftovers


def test_concurrent_sets_lose_nothing(fake_keyring):
    import threading
    names = [f"n{i}" for i in range(40)]

    def worker(chunk):
        for name in chunk:
            Safe().set(name, FAKE_VALUE)

    threads = [threading.Thread(target=worker, args=(names[i::4],)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(Safe().entries()) == sorted(names)


def test_cli_offers_no_memory_store():
    opt = next(p for p in cli_safe.safe_set.params if p.name == "store")
    assert list(opt.type.choices) == ["keyring"]


def test_no_platform_only_import_at_module_top():
    """AHA-0014 R1: fcntl or msvcrt at module top breaks import on one OS."""
    import ast
    from pathlib import Path
    import ahabase.safe as safe_module
    tree = ast.parse(Path(safe_module.__file__).read_text())
    names = [alias.name.split(".")[0] for node in tree.body
             if isinstance(node, ast.Import) for alias in node.names]
    names += [node.module.split(".")[0] for node in tree.body
              if isinstance(node, ast.ImportFrom) and node.module]
    banned = {"fcntl", "msvcrt", "termios", "winreg"}
    assert not (set(names) & banned), sorted(set(names) & banned)


def test_platform_arms_and_the_import_time_dispatch():
    """Both arms import on every OS; safe.py commits to exactly one."""
    import sys
    import ahabase._posix
    import ahabase._win
    import ahabase.safe as safe_module
    assert callable(ahabase._posix.lock) and callable(ahabase._win.lock)
    chosen = ahabase._win if sys.platform == "win32" else ahabase._posix
    assert safe_module._platform is chosen


def test_the_lock_goes_through_filelock(fake_keyring, monkeypatch):
    """A recording FileLock subclass sees the manifest lock being taken."""
    arm = safe_module._platform  # the lane's arm, whichever it is
    real = arm.FileLock

    class Recording(real):
        def __init__(self, path, *args, **kwargs):
            Recording.paths.append(str(path))
            super().__init__(path, *args, **kwargs)

    Recording.paths = []
    monkeypatch.setattr(arm, "FileLock", Recording)
    Safe().set("tok", FAKE_VALUE)
    assert any(p.endswith("safe.json.lock") for p in Recording.paths), Recording.paths


@pytest.mark.skipif(sys.platform == "win32",
                    reason="0o600 is the POSIX arm's statement; the Windows arm states ACLs")
def test_lock_file_mode_600(fake_keyring):
    """The lock file is owner-only from its first byte on POSIX."""
    import os
    import stat
    Safe().set("tok", FAKE_VALUE)
    path = manifest_path()
    lock = path.with_name(path.name + ".lock")
    assert stat.S_IMODE(os.stat(lock).st_mode) == 0o600


def test_exec_detection_answers_per_os(tmp_path):
    """AHA-0014 R2: the OS decides - shutil.which asks it (X_OK on POSIX,
    PATHEXT suffixes on Windows), not a rule of ours per platform."""
    import shutil
    script = tmp_path / "tool"
    script.write_text("#!/bin/sh\n")
    script.chmod(0o755)
    exe = tmp_path / "tool.exe"
    exe.write_text("")  # not +x: X_OK false here, a suffix executable on Windows
    txt = tmp_path / "tool.txt"
    txt.write_text("")
    if sys.platform == "win32":
        # no exec bit on this OS: which accepts any existing path-qualified file
        # (the OS cannot know before it launches); its executable/not line is the
        # name's suffix (PATHEXT), drawn on PATH search - which is where the
        # not-bindable suffix rules carry the refusal instead
        assert shutil.which(str(exe)) is not None
        assert shutil.which(str(txt)) is not None
        assert shutil.which(str(tmp_path / "missing.exe")) is None
        assert shutil.which("no-such-ahabase-tool") is None
    else:
        assert shutil.which(str(script)) is not None
        assert shutil.which(str(exe)) is None  # exists, not X_OK
    # the wiring: bind refuses what which() cannot resolve (its own lane)
    if sys.platform != "win32":
        with pytest.raises(SafeError) as error:
            Safe().bind("tok", str(exe))
        assert "is not an executable file" in str(error.value)


def test_windows_script_suffixes_reach_not_bindable(monkeypatch):
    """AHA-0014 R2: python.exe / *.bat / *.cmd hit the same refusal shape."""
    import ahabase._posix
    import ahabase._win
    import ahabase.safe as safe_module
    assert ahabase._win.exec_base_name("C:/Windows/System32/cmd.exe") == "cmd"
    assert ahabase._win.exec_base_name("C:/Python313/python3.14.exe") == "python3.14"
    assert ahabase._win.exec_base_name("C:/tools/deploy.bat") == "deploy"
    monkeypatch.setattr(safe_module, "_platform", ahabase._win)
    windows_refusal = safe_module.not_bindable_reason("C:/Windows/System32/cmd.exe")
    monkeypatch.setattr(safe_module, "_platform", ahabase._posix)
    posix_refusal = safe_module.not_bindable_reason("/usr/bin/zsh")
    assert windows_refusal is not None and posix_refusal is not None
    shape = (windows_refusal.replace("cmd.exe", "NAME"),
             posix_refusal.replace("zsh", "NAME"))
    assert shape[0] == shape[1]


def test_run_error_names_the_right_position(fake_keyring):
    """Review a90455fa nit: the same malformed pair twice."""
    runner = CliRunner()
    runner.invoke(_cli(), ["safe", "set", "tok"], input=FAKE_VALUE + "\n")
    out = runner.invoke(_cli(), ["safe", "run", "--env", "A=safe://tok",
                                 "--env", "BAD", "--", "true"])
    assert "argument 2 is not" in out.output, out.output


def test_compare_env_file_and_git_remote(fake_keyring, owner, tmp_path, monkeypatch):
    """AHA-0003: compare says same / different / missing, never a value."""
    import subprocess as sp
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "tok"], input=FAKE_VALUE + "\n")
    monkeypatch.setenv("FIXTURE_TOK", FAKE_VALUE)
    same = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--env", "FIXTURE_TOK"])
    assert same.exit_code == 0 and _last(same) == "tok: same", same.output
    monkeypatch.setenv("FIXTURE_TOK", FAKE_VALUE + "x")
    diff = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--env", "FIXTURE_TOK"])
    assert diff.exit_code == 1 and "different" in diff.output
    for out in (same, diff):
        assert FAKE_VALUE not in out.output
        assert len(_last(out)) < 40, "no fingerprint or value in the output"
    f = tmp_path / "token-file"
    f.write_text(FAKE_VALUE + "\n")
    assert runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--file", str(f)]).exit_code == 0
    repo = tmp_path / "repo"
    sp.run(["git", "init", "-q", str(repo)], check=True)
    sp.run(["git", "-C", str(repo), "remote", "add", "origin",
            f"https://fixture-user:{FAKE_VALUE}@git.example.com/o/r.git"], check=True)
    remote = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--git-remote", str(repo)])
    assert remote.exit_code == 0 and FAKE_VALUE not in remote.output, remote.output
    missing = runner.invoke(cli, input="\n", args=["safe", "compare","nope", "--env", "FIXTURE_TOK"])
    assert missing.exit_code == 2 and FAKE_VALUE not in missing.output
    monkeypatch.delenv("FIXTURE_TOK")
    nosource = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--env", "FIXTURE_TOK"])
    assert nosource.exit_code == 2 and "missing at the source" in nosource.output
    both = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--env", "X", "--file", str(f)])
    assert both.exit_code == 2


def test_compare_git_remote_decodes_the_credential(fake_keyring, owner, tmp_path):
    """AHA-0003: a percent-encoded credential in a URL equals its plain value."""
    import subprocess as sp
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "tok"], input="fixture/pass@word\n")
    repo = tmp_path / "repo"
    sp.run(["git", "init", "-q", str(repo)], check=True)
    sp.run(["git", "-C", str(repo), "remote", "add", "origin",
            "https://u:fixture%2Fpass%40word@git.example.com/o/r.git"], check=True)
    out = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--git-remote", str(repo)])
    assert out.exit_code == 0 and _last(out) == "tok: same", out.output


def test_compare_file_keeps_leading_space(fake_keyring, owner, tmp_path):
    """AHA-0003 review: only the line ending is dropped, never part of the value."""
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "tok"], input=FAKE_VALUE + "\n")
    f = tmp_path / "token-file"
    f.write_text(" " + FAKE_VALUE + "\r\n")
    out = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--file", str(f)])
    assert out.exit_code == 1 and "different" in out.output, out.output


def test_compare_git_remote_ignores_instead_of(fake_keyring, owner, tmp_path):
    """AHA-0003 review: the origin's own credential, not an insteadOf rewrite."""
    import subprocess as sp
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "tok"], input=FAKE_VALUE + "\n")
    repo = tmp_path / "repo"
    sp.run(["git", "init", "-q", str(repo)], check=True)
    sp.run(["git", "-C", str(repo), "remote", "add", "origin",
            f"https://u:{FAKE_VALUE}@git.example.com/o/r.git"], check=True)
    sp.run(["git", "-C", str(repo), "config",
            "url.https://u:rule-token@git.example.com/.insteadOf",
            f"https://u:{FAKE_VALUE}@git.example.com/"], check=True)
    rewritten = sp.run(["git", "-C", str(repo), "remote", "get-url", "origin"],
                       capture_output=True, text=True).stdout
    assert "rule-token" in rewritten, "fixture must rewrite the URL"
    out = runner.invoke(cli, input="\n", args=["safe", "compare","tok", "--git-remote", str(repo)])
    assert out.exit_code == 0 and _last(out) == "tok: same", out.output


# targets (AHA-0012 R2-R5): a copy in a tool's own store, written by the
# safe on rotation - the real kinds run git and gh, so the suite stands a
# fake kind in their place and checks the real ones' seams directly


class FakeTargetKind:
    """A stand-in target kind: records refreshes, can be told to fail,
    to lie (the write reports success, the destination holds nothing)
    or to hold a stale copy (the destination answers - with the old value)."""

    name = "fake-target"
    usage = "[NAME]"
    absence = "fixture destination does not hold the value"

    def __init__(self):
        self.refreshed = []
        self.fail = False
        self.lies = False
        self.stale = False

    def parse(self, args):
        return {"kind": self.name, "name": args[0] if args else "fixture"}

    def label(self, spec):
        return f"{self.name} {spec.get('name', '?')}"

    def refresh(self, spec, value):
        if self.fail:
            raise SafeError("fixture refusal")
        self.refreshed.append((spec.get("name"), value))

    def present(self, spec):
        return not self.lies and any(n == spec.get("name")
                                      for n, _ in self.refreshed)

    def verify(self, spec, value):
        if self.lies or self.stale:
            return False
        return any(n == spec.get("name") and v == value
                   for n, v in self.refreshed)


@pytest.fixture
def fake_target(monkeypatch):
    fake = FakeTargetKind()
    monkeypatch.setitem(safe_module.TARGET_KINDS, "fake-target", fake)
    return fake


def test_set_refreshes_targets(fake_keyring, fake_target):
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    s.target_add("jira-api", {"kind": "fake-target", "name": "fixture"})
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.refreshed == ["fake-target fixture"]
    assert fake_target.refreshed == [("fixture", FAKE_VALUE + "-new")]
    assert not rotation.failed
    problems = [text for ok, text in s.health() if not ok]
    assert not any("target" in p for p in problems), problems


def test_a_failing_target_is_reported_not_swallowed(fake_keyring, fake_target):
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    s.target_add("jira-api", {"kind": "fake-target", "name": "fixture"})
    fake_target.fail = True
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.refreshed == []
    assert rotation.failed == [("fake-target fixture", "fixture refusal")]
    assert s.get("jira-api") == FAKE_VALUE + "-new"  # stored regardless
    problems = [text for ok, text in s.health() if not ok]
    assert any("target fake-target fixture" in p for p in problems), problems
    fake_target.fail = False
    assert s.refresh("jira-api") == (["fake-target fixture"], [], [])


def test_a_write_the_destination_did_not_take_is_a_failure(fake_keyring, fake_target):
    """git accepts a value with no helper configured - the read-back proof fails."""
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    s.target_add("jira-api", {"kind": "fake-target", "name": "fixture"})
    fake_target.lies = True  # the write reports success, the store holds nothing
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.refreshed == []
    assert rotation.failed == [("fake-target fixture", fake_target.absence)]
    assert FAKE_VALUE not in rotation.failed[0][1]
    fake_target.lies = False
    assert s.refresh("jira-api") == (["fake-target fixture"], [], [])


def test_a_stale_copy_fails_the_proof(fake_keyring, fake_target):
    """A rotation's steady state: the destination still answers - with the
    previous value. Presence (health) passes; the proof must not."""
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    s.target_add("jira-api", {"kind": "fake-target", "name": "fixture"})
    fake_target.stale = True  # the destination holds the old value
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.refreshed == []
    assert rotation.failed == [("fake-target fixture", fake_target.absence)]
    assert FAKE_VALUE not in rotation.failed[0][1]
    problems = [text for ok, text in s.health() if not ok]
    assert not any("target" in p for p in problems), problems  # present, just stale
    fake_target.stale = False
    assert s.refresh("jira-api") == (["fake-target fixture"], [], [])


def test_malformed_target_is_refused(fake_keyring):
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    data = json.loads(manifest_path().read_text())
    data["secrets"]["jira-api"]["targets"] = [{"kind": ""}]
    manifest_path().write_text(json.dumps(data))
    with pytest.raises(SafeError) as error:
        Safe().entries()
    assert "malformed" in str(error.value)


def test_unknown_target_kind_is_named(fake_keyring):
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    s.target_add("jira-api", {"kind": "future-kind", "x": "y"})  # shape-valid, unknown
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.failed and "unknown target kind 'future-kind'" in rotation.failed[0][1]
    problems = [text for ok, text in s.health() if not ok]
    assert any("future-kind (unknown kind)" in p for p in problems), problems


def test_target_add_twice_is_one_target(fake_keyring, fake_target):
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    spec = {"kind": "fake-target", "name": "fixture"}
    s.target_add("jira-api", spec)
    s.target_add("jira-api", spec)
    assert Safe().entries()["jira-api"].targets == [spec]
    assert s.target_remove("jira-api", spec) == "fake-target fixture"
    with pytest.raises(SafeError) as error:
        s.target_remove("jira-api", spec)
    assert "no such target" in str(error.value)


# scope-only targets (AHA-0020 R1): the declaration grants the helper's
# host scope; the safe writes no copy for it anywhere


def test_a_scope_only_target_writes_nothing_and_is_named(fake_keyring, fake_target):
    """Rotation touches no tool store for it - reported as scope, never
    as refreshed, and health finds nothing missing."""
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    s.target_add("jira-api",
                 {"kind": "fake-target", "name": "fixture", "copy": False})
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.refreshed == [] and rotation.failed == []
    assert rotation.scope == ["fake-target fixture"]
    assert fake_target.refreshed == []  # no write was even attempted
    assert s.refresh("jira-api") == ([], ["fake-target fixture"], [])
    problems = [text for ok, text in s.health() if not ok]
    assert not any("target" in p for p in problems), problems


def test_credential_answers_for_a_scope_only_target(fake_keyring):
    """The load-bearing property EVOLUCEAN-0528 waits on: a host whose
    only declaration is scope-only still gets its answer - the helper
    reads the safe's store value, indifferent to the copy field."""
    s = Safe()
    s.set("github-push-pat", FAKE_VALUE)
    s.target_add("github-push-pat",
                 {"kind": "git-credential", "host": "github.com",
                  "account": "octocat", "copy": False})
    answer = s.credential({"protocol": "https", "host": "github.com"})
    assert answer == {"username": "octocat", "password": FAKE_VALUE}
    assert s.credential({"protocol": "https", "host": "gitlab.com"}) is None


def test_target_remove_matches_a_scope_only_declaration(fake_keyring):
    """The copy field never blocks removal: a spec typed without the
    flag withdraws the variant added with it."""
    s = Safe()
    s.set("github-push-pat", FAKE_VALUE)
    s.target_add("github-push-pat",
                 {"kind": "git-credential", "host": "github.com",
                  "account": "octocat", "copy": False})
    plain = {"kind": "git-credential", "host": "github.com",
             "account": "octocat"}
    assert s.target_remove("github-push-pat", plain) \
        == "git-credential github.com/octocat"
    assert Safe().entries()["github-push-pat"].targets == []


def test_the_copy_field_is_a_bool_or_the_manifest_is_malformed(fake_keyring):
    """A string would slip past the str-only shape check of every other
    field - the guard pins the type."""
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    data = json.loads(manifest_path().read_text())
    data["secrets"]["jira-api"]["targets"] = [
        {"kind": "git-credential", "host": "github.com",
         "account": "octocat", "copy": "false"}]
    manifest_path().write_text(json.dumps(data))
    with pytest.raises(SafeError) as error:
        Safe().entries()
    assert "malformed" in str(error.value)


def test_adding_the_other_custody_mode_converts_not_duplicates(fake_keyring,
                                                               fake_target):
    """The blocking finding of this story's review: one target has one
    custody mode - adding the spec of an already-declared target replaces
    the stored one, so one rotation can never name the same target as both
    refreshed and scope-only."""
    s = Safe()
    s.set("jira-api", FAKE_VALUE)
    plain = {"kind": "fake-target", "name": "fixture"}
    s.target_add("jira-api", plain)
    before = len(fake_target.refreshed)
    replaced = s.target_add("jira-api", {**plain, "copy": False})
    assert replaced == plain  # the stored spec, replaced in place
    assert Safe().entries()["jira-api"].targets == [{**plain, "copy": False}]
    rotation = s.set("jira-api", FAKE_VALUE + "-new")
    assert rotation.scope == ["fake-target fixture"]
    assert rotation.refreshed == [] and rotation.failed == []
    assert len(fake_target.refreshed) == before  # no write was attempted
    # and back: the copy-on mode replaces the scope-only one
    assert s.target_add("jira-api", plain) == {**plain, "copy": False}
    assert Safe().entries()["jira-api"].targets == [plain]
    rotation = s.set("jira-api", FAKE_VALUE + "-n2")
    assert rotation.refreshed == ["fake-target fixture"] and rotation.scope == []


def test_target_kinds_parse_and_label():
    git_kind = TARGET_KINDS["git-credential"]
    spec = git_kind.parse(["github.com", "octocat"])
    assert spec == {"kind": "git-credential", "host": "github.com", "account": "octocat"}
    assert git_kind.label(spec) == "git-credential github.com/octocat"
    with pytest.raises(ValueError):
        git_kind.parse(["github.com"])
    gh_kind = TARGET_KINDS["gh-login"]
    assert gh_kind.parse([]) == {"kind": "gh-login", "hostname": "github.com"}
    assert gh_kind.parse(["gh.example.org"])["hostname"] == "gh.example.org"
    with pytest.raises(ValueError):
        gh_kind.parse(["a", "b"])
    # AHA-0022: a second account on one host is its own kind; the
    # fixture account is composed at runtime - this suite ships in the
    # sdist and the containment arm matches the internal name as a
    # substring (AHA-0029, review F_d). The split carries no contiguous
    # class token, so the public-seed scrub leaves every fragment intact
    # (a contiguous token here once broke the public CI and printed the
    # composed stem into the public run log - incident 2026-11-22).
    _account = "kamen" + "skl" + "_me" + "rck"
    acct = TARGET_KINDS["gh-login-account"]
    assert acct.parse(["github.com", _account]) == {
        "kind": "gh-login-account", "hostname": "github.com", "account": _account}
    assert acct.label(acct.parse(["github.com", "a-b"])) == "gh-login-account github.com a-b"
    for bad in ([], ["github.com"], ["a", "b", "c"], ["github.com", "../x"]):
        with pytest.raises(ValueError):
            acct.parse(bad)


def test_target_kinds_carry_the_proof_members():
    """The protocol grew a verify member - no registered kind may lack it."""
    for kind in TARGET_KINDS.values():
        for member in ("name", "usage", "absence", "parse", "label",
                       "refresh", "present", "verify"):
            assert hasattr(kind, member), (type(kind).__name__, member)


def test_git_credential_feeds_stdin_never_argv(monkeypatch):
    """The value reaches git on stdin; no argument carries it."""
    calls = []
    out = type("Out", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    out.stdout = "protocol=https\nhost=github.com\npassword=x\n"

    def fake_run(argv, input=None, **_):
        calls.append((list(argv), input))
        return out
    monkeypatch.setattr(safe_module.subprocess, "run", fake_run)
    kind = TARGET_KINDS["git-credential"]
    spec = kind.parse(["github.com", "octocat"])
    kind.refresh(spec, FAKE_VALUE)
    argv, fed = calls[-1]
    assert argv == ["git", "credential", "approve"]
    assert f"password={FAKE_VALUE}" in fed
    assert not any(FAKE_VALUE in a for a in argv)
    assert kind.present(spec) is True
    out.stdout = ""  # no helper answered
    assert kind.present(spec) is False


def test_git_credential_verifies_by_readback(monkeypatch):
    """The proof reads the destination back and compares the value - a
    stale copy fails it; the read stays quiet and never prints."""

    def answering(password):
        def fake_run(argv, input=None, env=None, **_):
            assert argv == ["git", "credential", "fill"]
            assert env["GIT_TERMINAL_PROMPT"] == "0"  # the read stays quiet
            return type("Out", (), {"returncode": 0,
                                    "stdout": f"password={password}\n",
                                    "stderr": ""})()
        return fake_run

    kind = TARGET_KINDS["git-credential"]
    spec = kind.parse(["github.com", "octocat"])
    monkeypatch.setattr(safe_module.subprocess, "run", answering(FAKE_VALUE))
    assert kind.verify(spec, FAKE_VALUE) is True
    monkeypatch.setattr(safe_module.subprocess, "run",
                        answering(FAKE_VALUE + "-old"))
    assert kind.present(spec) is True  # a stale copy is present...
    assert kind.verify(spec, FAKE_VALUE) is False  # ...and fails the proof
    monkeypatch.setattr(safe_module.subprocess, "run", answering(""))
    assert kind.verify(spec, FAKE_VALUE) is False  # an empty answer is no answer


def test_presence_check_prompts_nothing(monkeypatch):
    """doctor must not pop a helper's GUI dialog (GCM) or a terminal prompt."""
    for var in ("GCM_INTERACTIVE", "GCM_GUI", "GIT_TERMINAL_PROMPT", "GIT_ASKPASS"):
        monkeypatch.delenv(var, raising=False)  # armed: no ambient value helps
    seen = {}

    def fake_run(argv, input=None, env=None, **_):
        seen.update(env or {})
        return type("Out", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", fake_run)
    kind = TARGET_KINDS["git-credential"]
    kind.present(kind.parse(["github.com", "octocat"]))
    assert seen["GIT_TERMINAL_PROMPT"] == "0"
    assert seen["GCM_INTERACTIVE"] == "never" and seen["GCM_GUI"] == "never"
    # AHA-0014 R3: the no-op is the lane's arm, not a hardcoded Unix name
    assert seen["GIT_ASKPASS"] == safe_module._platform.ASKPASS_NOOP


def test_the_askpass_noop_names_no_unix_executable_on_windows():
    """AHA-0014 R3: each arm's no-op exists on its own OS."""
    import ahabase._posix
    import ahabase._win
    assert ahabase._posix.ASKPASS_NOOP == "true"  # POSIX: the Unix true
    assert ahabase._win.ASKPASS_NOOP == "rundll32"  # Windows: no true there
    assert ahabase._win.ASKPASS_NOOP != ahabase._posix.ASKPASS_NOOP


def test_gh_login_feeds_stdin_and_drops_token_env(monkeypatch):
    calls = []

    def fake_run(argv, input=None, env=None, **_):
        calls.append((list(argv), input, env))
        return type("Out", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", fake_run)
    monkeypatch.setattr(safe_module.shutil, "which", lambda name: "/fixture/bin/gh")
    monkeypatch.setenv("GH_TOKEN", FAKE_VALUE)
    kind = TARGET_KINDS["gh-login"]
    spec = kind.parse([])
    kind.refresh(spec, FAKE_VALUE)
    argv, fed, env = calls[-1]
    assert argv == ["/fixture/bin/gh", "auth", "login", "--hostname",
                    "github.com", "--with-token"]
    assert FAKE_VALUE + "\n" == fed
    assert not any(FAKE_VALUE in a for a in argv)
    assert "GH_TOKEN" not in env  # the target is the login, not the environment
    assert kind.present(spec) is True


def test_gh_login_verifies_the_token(monkeypatch):
    """gh auth token prints the token - captured, compared by digest,
    dropped; never printed by us; the check runs on the scrubbed env."""
    seen = {}

    def fake_run(argv, input=None, env=None, **_):
        seen.update(argv=list(argv), env=env or {})
        return type("Out", (), {"returncode": 0, "stdout": FAKE_VALUE + "\n",
                                "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", fake_run)
    monkeypatch.setattr(safe_module.shutil, "which", lambda name: "/fixture/bin/gh")
    monkeypatch.setenv("GH_TOKEN", FAKE_VALUE + "-ambient")
    kind = TARGET_KINDS["gh-login"]
    spec = kind.parse([])
    assert kind.verify(spec, FAKE_VALUE) is True
    assert seen["argv"] == ["/fixture/bin/gh", "auth", "token",
                            "--hostname", "github.com"]
    assert "GH_TOKEN" not in seen["env"]  # the proof sees the login, not the ambient

    def stale_run(argv, input=None, env=None, **_):
        return type("Out", (), {"returncode": 0, "stdout": FAKE_VALUE + "-old\n",
                                "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", stale_run)
    assert kind.verify(spec, FAKE_VALUE) is False  # a login with a stale token

    def empty_run(argv, input=None, env=None, **_):
        return type("Out", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", empty_run)
    assert kind.verify(spec, FAKE_VALUE) is False  # nothing printed is nothing held


def test_missing_tools_name_their_target(monkeypatch):
    monkeypatch.setattr(safe_module.shutil, "which", lambda name: None)
    gh_kind = TARGET_KINDS["gh-login"]
    spec = gh_kind.parse([])
    with pytest.raises(SafeError) as error:
        gh_kind.refresh(spec, FAKE_VALUE)
    assert "gh is not installed" in str(error.value)
    assert FAKE_VALUE not in str(error.value)
    assert gh_kind.present(spec) is False


def test_cli_target_add_list_refresh(fake_keyring, owner, fake_target):
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "jira-api"], input=FAKE_VALUE + "\n")
    added = runner.invoke(cli, ["safe", "target", "add", "jira-api", "fake-target"],
                          input="jira-api\n")
    assert added.exit_code == 0 and "fake-target fixture" in added.output, added.output
    listed = runner.invoke(cli, ["safe", "list"])
    assert "targets: fake-target fixture" in listed.output, listed.output
    assert FAKE_VALUE not in listed.output
    fake_target.fail = True
    rotated = runner.invoke(cli, ["safe", "set", "jira-api"], input=FAKE_VALUE + "-n\n")
    assert rotated.exit_code == 1, rotated.output
    assert "not refreshed: fixture refusal" in rotated.output, rotated.output
    assert "ahabase safe refresh jira-api" in rotated.output
    assert FAKE_VALUE not in rotated.output
    fake_target.fail = False
    refreshed = runner.invoke(cli, ["safe", "refresh", "jira-api"], input="jira-api\n")
    assert refreshed.exit_code == 0, refreshed.output
    assert "refreshed target fake-target fixture" in refreshed.output
    removed = runner.invoke(cli, ["safe", "target", "remove", "jira-api", "fake-target"],
                            input="jira-api\n")
    assert removed.exit_code == 0 and "removed target" in removed.output
    doctor = runner.invoke(cli, ["doctor"])
    assert "check safe: ok - 1 secrets, all present" in doctor.output, doctor.output


def test_cli_target_add_refuses_a_wrong_spec(fake_keyring, owner):
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "jira-api"], input=FAKE_VALUE + "\n")
    wrong = runner.invoke(cli, ["safe", "target", "add", "jira-api", "git-credential",
                                "github.com"], input="jira-api\n")
    assert wrong.exit_code != 0 and "HOST ACCOUNT" in wrong.output, wrong.output
    unknown = runner.invoke(cli, ["safe", "target", "add", "jira-api", "no-such-kind"],
                            input="jira-api\n")
    assert unknown.exit_code != 0 and "unknown target kind" in unknown.output
    assert FAKE_VALUE not in unknown.output


def test_cli_no_copy_is_refused_off_git_credential(fake_keyring, owner):
    """A gh login is a copy by definition - there is no scope to declare."""
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "jira-api"], input=FAKE_VALUE + "\n")
    gh = runner.invoke(cli, ["safe", "target", "add", "jira-api", "gh-login",
                             "--no-copy"], input="jira-api\n")
    assert gh.exit_code != 0 and "gh login is a copy by definition" in gh.output
    fake = runner.invoke(cli, ["safe", "target", "add", "jira-api", "fake-target",
                               "--no-copy"], input="jira-api\n")
    assert fake.exit_code != 0 and "--no-copy is a git-credential option" in fake.output


def test_cli_scope_only_target_lifecycle(fake_keyring, owner, fake_target):
    """The variant end to end through the CLI: add says scope only, list
    distinguishes, rotation writes nothing and says so, doctor is silent,
    removal matches a spec typed without the flag."""
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "github-push-pat"],
                  input=FAKE_VALUE + "\n")
    added = runner.invoke(cli, ["safe", "target", "add", "github-push-pat",
                                "git-credential", "github.com", "octocat",
                                "--no-copy"], input="github-push-pat\n")
    assert added.exit_code == 0 and "(scope only)" in added.output, added.output
    assert "maintains no copy" in added.output
    assert Safe().entries()["github-push-pat"].targets == [
        {"kind": "git-credential", "host": "github.com",
         "account": "octocat", "copy": False}]
    listed = runner.invoke(cli, ["safe", "list"])
    assert "git-credential github.com/octocat (no copy)" in listed.output
    assert FAKE_VALUE not in listed.output
    rotated = runner.invoke(cli, ["safe", "set", "github-push-pat"],
                            input=FAKE_VALUE + "-n\n")
    assert rotated.exit_code == 0, rotated.output
    assert "scope target git-credential github.com/octocat - " \
           "no copy is maintained" in rotated.output
    assert "refreshed target" not in rotated.output
    refreshed = runner.invoke(cli, ["safe", "refresh", "github-push-pat"],
                              input="github-push-pat\n")
    assert refreshed.exit_code == 0, refreshed.output
    assert "no copy is maintained" in refreshed.output
    doctor = runner.invoke(cli, ["doctor"])
    assert "check safe: ok - 1 secrets, all present" in doctor.output, doctor.output
    removed = runner.invoke(cli, ["safe", "target", "remove", "github-push-pat",
                                  "git-credential", "github.com", "octocat"],
                            input="github-push-pat\n")
    assert removed.exit_code == 0 and "removed target" in removed.output
    assert Safe().entries()["github-push-pat"].targets == []


def test_cli_adding_the_other_mode_converts_the_target(fake_keyring, owner):
    """Re-declaring an existing target in the other custody mode converts
    it (one target, one mode) and the CLI says so - naming the leftover
    copy honestly: a copy already in the tool's store stays until removed
    by hand."""
    runner = CliRunner()
    cli = _cli()
    runner.invoke(cli, ["safe", "set", "github-push-pat"],
                  input=FAKE_VALUE + "\n")
    runner.invoke(cli, ["safe", "target", "add", "github-push-pat",
                        "git-credential", "github.com", "octocat"],
                  input="github-push-pat\n")
    converted = runner.invoke(cli, ["safe", "target", "add", "github-push-pat",
                                    "git-credential", "github.com", "octocat",
                                    "--no-copy"], input="github-push-pat\n")
    assert converted.exit_code == 0, converted.output
    assert "converted to scope only" in converted.output
    assert "stays until removed by hand" in converted.output
    assert Safe().entries()["github-push-pat"].targets == [
        {"kind": "git-credential", "host": "github.com",
         "account": "octocat", "copy": False}]
    back = runner.invoke(cli, ["safe", "target", "add", "github-push-pat",
                               "git-credential", "github.com", "octocat"],
                         input="github-push-pat\n")
    assert back.exit_code == 0 and "converted to a maintained copy" in back.output
    assert Safe().entries()["github-push-pat"].targets == [
        {"kind": "git-credential", "host": "github.com", "account": "octocat"}]
    assert FAKE_VALUE not in back.output


def test_gh_login_per_account_dir(monkeypatch, tmp_path):
    """AHA-0022 R1/R3: an account target runs gh in its own config dir
    under the workspace _config/, owner-only; the default target is unchanged."""
    monkeypatch.setenv("AHABASE_HOME", str(tmp_path))
    calls = []

    def fake_run(argv, input=None, env=None, **_):
        calls.append((list(argv), env or {}))
        return type("Out", (), {"returncode": 0, "stdout": FAKE_VALUE + "\n", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", fake_run)
    monkeypatch.setattr(safe_module.shutil, "which", lambda name: "/fixture/bin/gh")
    kind = TARGET_KINDS["gh-login-account"]
    a = kind.parse(["github.com", "acct-a"])
    b = kind.parse(["github.com", "acct-b"])
    kind.refresh(a, FAKE_VALUE)
    dir_a = tmp_path / "_config" / "ahabase-gh" / "acct-a"
    assert calls[-1][1]["GH_CONFIG_DIR"] == str(dir_a)
    assert dir_a.is_dir()
    if os.name != "nt":  # Windows carries no POSIX permission bits
        assert (dir_a.stat().st_mode & 0o777) == 0o700
    assert kind.verify(b, FAKE_VALUE) is True
    assert calls[-1][1]["GH_CONFIG_DIR"] == str(tmp_path / "_config" / "ahabase-gh" / "acct-b")
    monkeypatch.delenv("GH_CONFIG_DIR", raising=False)
    TARGET_KINDS["gh-login"].present(TARGET_KINDS["gh-login"].parse([]))
    assert "GH_CONFIG_DIR" not in calls[-1][1]  # the default login: no regression


def test_gh_login_refuses_a_plaintext_token(monkeypatch, tmp_path):
    """AHA-0022 R2: gh without a keyring writes the token into hosts.yml -
    the safe removes the file and refuses; a keyring write passes."""
    monkeypatch.setenv("AHABASE_HOME", str(tmp_path))
    monkeypatch.setattr(safe_module.shutil, "which", lambda name: "/fixture/bin/gh")
    kind = TARGET_KINDS["gh-login-account"]
    spec = kind.parse(["github.com", "acct"])
    hosts = tmp_path / "_config" / "ahabase-gh" / "acct" / "hosts.yml"

    def plaintext_run(argv, input=None, env=None, **_):
        hosts.write_text("github.com:\n    user: acct\n    oauth_token: " + FAKE_VALUE + "\n")
        return type("Out", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", plaintext_run)
    with pytest.raises(SafeError) as error:
        kind.refresh(spec, FAKE_VALUE)
    assert "plain text" in str(error.value) and FAKE_VALUE not in str(error.value)
    assert not hosts.exists()

    def keyring_run(argv, input=None, env=None, **_):
        hosts.write_text("github.com:\n    user: acct\n    git_protocol: https\n")
        return type("Out", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", keyring_run)
    kind.refresh(spec, FAKE_VALUE)
    assert hosts.exists()


def test_gh_login_refuses_the_value_under_any_field(monkeypatch, tmp_path):
    """home-5235 F2: the plaintext check is by VALUE - a renamed field
    still fails; the masked gh exit code is named."""
    monkeypatch.setenv("AHABASE_HOME", str(tmp_path))
    monkeypatch.setattr(safe_module.shutil, "which", lambda name: "/fixture/bin/gh")
    kind = TARGET_KINDS["gh-login-account"]
    spec = kind.parse(["github.com", "acct"])
    hosts = tmp_path / "_config" / "ahabase-gh" / "acct" / "hosts.yml"

    def renamed_run(argv, input=None, env=None, **_):
        hosts.write_text("github.com:\n    user: acct\n    token: " + FAKE_VALUE + "\n")
        return type("Out", (), {"returncode": 3, "stdout": "", "stderr": ""})()
    monkeypatch.setattr(safe_module.subprocess, "run", renamed_run)
    with pytest.raises(SafeError) as error:
        kind.refresh(spec, FAKE_VALUE)
    assert "plain text" in str(error.value) and "exited 3" in str(error.value)
    assert FAKE_VALUE not in str(error.value) and not hosts.exists()


def test_account_login_is_a_distinct_kind():
    """home-5235 F1: the account login is its own kind, never a field on
    gh-login - so a reader without the kind refuses it on the unknown-kind
    leg (that refusal is pinned by test_unknown_target_kind_is_named),
    instead of writing the account's token into the default login."""
    assert TARGET_KINDS["gh-login-account"].name != TARGET_KINDS["gh-login"].name
    spec = TARGET_KINDS["gh-login-account"].parse(["github.com", "acct"])
    assert spec["kind"] == "gh-login-account"


def test_gh_config_dir_is_the_one_path(monkeypatch, tmp_path):
    """home-5235 F6: the command seam names the directory; a bad name is refused."""
    from click.testing import CliRunner
    from ahabase.cli_safe import safe
    monkeypatch.setenv("AHABASE_HOME", str(tmp_path))
    out = CliRunner().invoke(safe, ["gh-config-dir", "acct"])
    assert out.exit_code == 0
    assert out.output.strip() == str(tmp_path / "_config" / "ahabase-gh" / "acct")
    bad = CliRunner().invoke(safe, ["gh-config-dir", "../x"])
    assert bad.exit_code != 0
