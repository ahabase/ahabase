"""The plugin contract (AHA-0001 R3) with fictional plugins."""

from __future__ import annotations

import ast
import types
from pathlib import Path

import click
from click.testing import CliRunner

import ahabase.plugins as plugins
from ahabase.cli import build_cli


class _EntryPoint:
    """A stand-in for importlib.metadata.EntryPoint."""

    def __init__(self, name, target, dist="fixture-plugin"):
        self.name = name
        self._target = target
        self.dist = types.SimpleNamespace(metadata={"Name": dist}, version="9.9")

    def load(self):
        if isinstance(self._target, BaseException):
            raise self._target
        return self._target


def _plugin(api=plugins.API_VERSION, register=None):
    return types.SimpleNamespace(API_VERSION=api, register=register)


def _hello_register(registry):
    @click.command("hello")
    def hello():
        click.echo("hello from the fixture plugin")

    registry.add_command(hello)
    registry.add_check("fixture-store", lambda: (True, "reachable"))


def _cli(monkeypatch, *entry_points):
    monkeypatch.setattr(plugins, "_entry_points", lambda: list(entry_points))
    return build_cli()


def test_plugin_command_and_check(monkeypatch):
    cli = _cli(monkeypatch, _EntryPoint("good", _plugin(register=_hello_register)))
    runner = CliRunner()
    assert "hello" in runner.invoke(cli, ["--help"]).output
    assert runner.invoke(cli, ["hello"]).output.strip() == "hello from the fixture plugin"
    doctor = runner.invoke(cli, ["doctor"])
    assert doctor.exit_code == 0, doctor.output
    assert "plugin good: loaded - from fixture-plugin 9.9" in doctor.output
    assert "check fixture-store: ok - reachable" in doctor.output


def test_failing_incompatible_and_colliding_plugins_are_reported(monkeypatch):
    def boom(registry):
        raise RuntimeError("broken plugin")

    def collide(registry):
        registry.add_command(click.Command("doctor"))

    cli = _cli(monkeypatch,
               _EntryPoint("a-broken", _plugin(register=boom)),
               _EntryPoint("b-old", _plugin(api=0, register=_hello_register)),
               _EntryPoint("c-collides", _plugin(register=collide)),
               _EntryPoint("d-unimportable", ImportError("missing dependency")),
               _EntryPoint("e-good", _plugin(register=_hello_register)))
    runner = CliRunner()
    doctor = runner.invoke(cli, ["doctor"])
    out = doctor.output
    assert doctor.exit_code == 1
    assert "plugin a-broken: NOT loaded" in out and "register failed: RuntimeError" in out
    assert "plugin b-old: NOT loaded" in out and "needs registry API 0" in out
    assert "command 'doctor' already exists - not overwritten" in out
    assert "plugin d-unimportable: NOT loaded" in out and "import failed" in out
    assert "plugin e-good: loaded" in out
    # the CLI keeps working and the good plugin's command is there
    assert runner.invoke(cli, ["hello"]).exit_code == 0


def test_systemexit_and_overwrite_attempts_cannot_break_the_cli(monkeypatch):
    """Review c6e031a3: SystemExit, direct dict writes and partial
    registrations."""
    def exits(registry):
        raise SystemExit(3)

    def overwrites(registry):
        try:
            registry.commands["doctor"] = click.Command("doctor")
        except TypeError:
            pass
        registry.add_command(click.Command("doctor"))

    def partial(registry):
        registry.add_command(click.Command("half"))
        registry.add_check("half-check", lambda: (True, "x"))
        raise ValueError("fails after registering")

    def bad_check(registry):
        def check():
            raise SystemExit(4)
        registry.add_check("exits", check)

    cli = _cli(monkeypatch,
               _EntryPoint("a-exits", _plugin(register=exits)),
               _EntryPoint("b-exits-at-import", SystemExit(2)),
               _EntryPoint("c-overwrites", _plugin(register=overwrites)),
               _EntryPoint("d-partial", _plugin(register=partial)),
               _EntryPoint("e-bad-check", _plugin(register=bad_check)),
               _EntryPoint("f-good", _plugin(register=_hello_register)))
    runner = CliRunner()
    out = runner.invoke(cli, ["doctor"]).output
    assert "register failed: SystemExit(3) - rolled back" in out
    assert "import failed: SystemExit(2)" in out
    assert "command 'doctor' already exists - not overwritten" in out
    assert "check exits: FAIL - SystemExit" in out
    assert "check fixture-store: ok" in out, "a failing check must not skip later checks"
    help_out = runner.invoke(cli, ["--help"]).output
    assert "half" not in help_out, "a failed plugin's partial command stays registered"
    assert "Check this installation" in runner.invoke(cli, ["doctor", "--help"]).output


def test_no_plugins(monkeypatch):
    cli = _cli(monkeypatch)
    doctor = CliRunner().invoke(cli, ["doctor"])
    assert doctor.exit_code == 0 and "plugins: none installed" in doctor.output


def test_package_never_imports_the_core():
    """The dependency points from the core to this package, never back.

    Static imports, and string literals naming the core anywhere in the
    code (importlib.import_module, __import__, a subprocess call of the
    core's CLI) - a dynamic import built from pieces is beyond a parse.
    """
    forbidden = {"evolucean", "knowledge_usage_cli"}
    src = Path(__file__).resolve().parents[1] / "src" / "ahabase"
    for path in src.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert name.split(".")[0] not in forbidden, (path, name)
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for word in forbidden | {"knowledge-usage"}:
                    assert word not in node.value, (path, node.value)
