"""The ``ahabase`` command line: the first door over the registry.

Implements: implementation-ahabase-architecture-blueprint
Blueprint: implementation-ahabase-architecture-blueprint

Capability: cli-command
"""

from __future__ import annotations

import platform
import sys

import click

from . import __version__
from .plugins import API_VERSION, Registry, load_plugins


def _package_cli(get_registry) -> click.Group:
    """The CLI group with the package's own commands only."""

    @click.group()
    @click.version_option(__version__, prog_name="ahabase")
    def cli():
        """ahabase - the open door to your knowledge workspace."""

    @cli.command()
    def doctor():
        """Check this installation: Python, the package and its plugins.

        Capability: health-report
        """
        registry = get_registry()
        ok = True
        click.echo(f"ahabase {__version__} (registry API {API_VERSION})")
        click.echo(f"python {platform.python_version()} ({sys.executable})")
        if not registry.plugins:
            click.echo("plugins: none installed")
        for record in registry.plugins:
            state = "loaded" if record.loaded else "NOT loaded"
            click.echo(f"plugin {record.name}: {state} - from {record.distribution} "
                       f"{record.version}")
            if record.commands:
                click.echo(f"  commands: {', '.join(record.commands)}")
            if record.problem:
                ok = False
                click.echo(f"  problem: {record.problem}")
        from . import cli_safe

        # the package's own check wins: a plugin cannot replace it
        checks = {**registry.checks, "safe": cli_safe.health}
        for name, check in checks.items():
            try:
                passed, detail = check()
            except KeyboardInterrupt:
                raise
            except BaseException as error:  # noqa: BLE001 - a check never ends doctor
                passed, detail = False, f"{type(error).__name__}: {error}"
            ok = ok and passed
            click.echo(f"check {name}: {'ok' if passed else 'FAIL'} - {detail}")
        sys.exit(0 if ok else 1)

    from .cli_safe import safe
    from .cli_transparency import ontology, verify

    cli.add_command(safe)
    from .cli_grid4d import init, validate
    from .cli_llm import llm
    from .cli_story import story_group
    from .cli_workspace import workspace_group
    cli.add_command(init)
    cli.add_command(llm)
    cli.add_command(ontology)
    cli.add_command(story_group, name="story")
    cli.add_command(validate)
    cli.add_command(verify)
    cli.add_command(workspace_group, name="workspace")
    return cli


def build_cli(registry: Registry | None = None) -> click.Group:
    """The CLI: the package's commands first, then the plugins'.

    The package's command names are reserved before any plugin loads, so
    a plugin can never take or overwrite them (review c6e031a3).
    """
    holder: dict = {}
    cli = _package_cli(lambda: holder["registry"])
    if registry is None:
        registry = load_plugins(Registry(reserved=set(cli.commands)))
    holder["registry"] = registry
    for name, command in registry.commands.items():
        if name not in cli.commands:
            cli.add_command(command, name)
    return cli


def main() -> None:
    """Console-script entry point."""
    build_cli()()
