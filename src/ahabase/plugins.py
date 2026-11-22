"""The plugin contract: one registry behind every door.

A plugin is a Python distribution that declares an entry point in the
group ``ahabase.plugins``. The entry point names a module (or object)
with:

- ``API_VERSION`` - the major registry API version it was written for;
- ``register(registry)`` - adds its commands and health checks.

The package never imports a plugin by name; it only loads what the
entry points name. Loading is robust: an incompatible API version, a
name already taken or any failure of a plugin - an exception or a
``SystemExit`` - is recorded as a problem of that plugin, its partial
registrations are rolled back, and the CLI keeps working (only Ctrl-C
passes through). Installing a plugin means trusting its code - every
plugin is listed with the distribution it came from.

Implements: implementation-ahabase-architecture-blueprint
Blueprint: implementation-ahabase-architecture-blueprint

Capability: plugin-registry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import metadata
from types import MappingProxyType
from typing import Callable, Mapping

import click

API_VERSION = 1
GROUP = "ahabase.plugins"

HealthCheck = Callable[[], "tuple[bool, str]"]


@dataclass
class PluginRecord:
    """What is known about one discovered plugin."""

    name: str
    distribution: str
    version: str
    loaded: bool = False
    problem: str | None = None
    commands: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)


class Registry:
    """Commands and health checks the doors expose.

    The CLI shows the commands; ``doctor`` runs the health checks; the
    MCP server will expose the same registry as tools. ``reserved`` names
    belong to the package and are never given to a plugin. The contents
    are read through read-only views; only ``add_command`` and
    ``add_check`` change them.
    """

    def __init__(self, reserved: set[str] | frozenset[str] = frozenset()) -> None:
        self._commands: dict[str, click.Command] = {}
        self._checks: dict[str, HealthCheck] = {}
        self._reserved = frozenset(reserved)
        self.plugins: list[PluginRecord] = []
        self._current: PluginRecord | None = None

    @property
    def commands(self) -> Mapping[str, click.Command]:
        """The registered commands (read-only)."""
        return MappingProxyType(self._commands)

    @property
    def checks(self) -> Mapping[str, HealthCheck]:
        """The registered health checks (read-only)."""
        return MappingProxyType(self._checks)

    def add_command(self, command: click.Command, name: str | None = None) -> bool:
        """Add a command; a name already taken or reserved is refused and reported."""
        name = name or command.name
        if not name:
            raise ValueError("a command needs a name")
        if name in self._commands or name in self._reserved:
            self._problem(f"command '{name}' already exists - not overwritten")
            return False
        self._commands[name] = command
        if self._current is not None:
            self._current.commands.append(name)
        return True

    def add_check(self, name: str, check: HealthCheck) -> bool:
        """Add a health check run by ``doctor``; names are unique and the
        package's own names (``reserved``) are refused."""
        if name in self._checks or name in self._reserved:
            self._problem(f"health check '{name}' already exists - not overwritten")
            return False
        self._checks[name] = check
        if self._current is not None:
            self._current.checks.append(name)
        return True

    def _rollback(self, record: PluginRecord) -> None:
        """Remove what a failed plugin registered before it failed."""
        for name in record.commands:
            self._commands.pop(name, None)
        for name in record.checks:
            self._checks.pop(name, None)
        record.commands.clear()
        record.checks.clear()

    def _problem(self, text: str) -> None:
        if self._current is not None:
            self._current.problem = (f"{self._current.problem}; {text}"
                                     if self._current.problem else text)


def _entry_points():
    """The entry points of the plugin group (a seam for tests)."""
    return metadata.entry_points(group=GROUP)


def _distribution(ep) -> tuple[str, str]:
    dist = getattr(ep, "dist", None)
    if dist is None:
        return "unknown", "unknown"
    return dist.metadata.get("Name", "unknown"), dist.version or "unknown"


def _failure(error: BaseException) -> str:
    if isinstance(error, SystemExit):
        return f"SystemExit({error.code})"
    return f"{type(error).__name__}: {error}"


def load_plugins(registry: Registry) -> Registry:
    """Load every plugin of the group into ``registry``, never raising.

    Every failure but ``KeyboardInterrupt`` is caught - ``SystemExit``
    included, so a plugin cannot end the process.
    """
    for ep in sorted(_entry_points(), key=lambda e: e.name):
        dist_name, dist_version = _distribution(ep)
        record = PluginRecord(name=ep.name, distribution=dist_name, version=dist_version)
        registry.plugins.append(record)
        try:
            plugin = ep.load()
        except KeyboardInterrupt:
            raise
        except BaseException as error:  # noqa: BLE001 - a plugin never breaks the CLI
            record.problem = f"import failed: {_failure(error)}"
            continue
        wanted = getattr(plugin, "API_VERSION", None)
        if wanted != API_VERSION:
            record.problem = (f"needs registry API {wanted}, this ahabase offers "
                              f"{API_VERSION} - not loaded")
            continue
        register = getattr(plugin, "register", None)
        if not callable(register):
            record.problem = "no register(registry) - not loaded"
            continue
        registry._current = record
        try:
            register(registry)
            record.loaded = True
        except KeyboardInterrupt:
            raise
        except BaseException as error:  # noqa: BLE001
            registry._rollback(record)
            record.problem = f"register failed: {_failure(error)} - rolled back"
        finally:
            registry._current = None
    return registry
