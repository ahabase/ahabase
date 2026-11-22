"""The module door: ``python -m ahabase`` runs the CLI door.

The same registry, the same commands as the ``ahabase`` entry point - for
the invocations that carry their own interpreter (a venv's python with
the package on ``PYTHONPATH``, a clean clone without an installed
console script).

Implements: implementation-ahabase-architecture-blueprint
Blueprint: implementation-ahabase-architecture-blueprint

Capability: cli-command
"""

from .cli import build_cli
from .plugins import Registry

if __name__ == "__main__":
    build_cli(Registry())()
