"""ahabase - the open door to the ahabase system.

The package owns the grid4d format, the services every door needs and the
doors themselves (the ``ahabase`` CLI now; the MCP server and the Claude
Code plugin next) over one registry that plugins fill. It never imports a
plugin: plugins build on it (see ``ahabase.plugins``).

Implements: implementation-ahabase-architecture-blueprint
Blueprint: implementation-ahabase-architecture-blueprint

Capability: cli-command
"""

__version__ = "0.0.1"

# The config door (AHA-0021): the graduated config/instance-state layer -
# the library seam every other capability stands on. Epic-explicit by
# design: the settings-reading functions take the epic as a required
# keyword, the workspace trio needs no argument.
from ahabase.config import (  # noqa: E402 - after the version, the door follows
    ensure_standard_folders,
    get_data_dir,
    get_instance_root,
    get_machine_id,
    get_workspace_dir,
    list_scope_holdings,
    load_settings,
)
# The AHA-0035 addition to the door's surface: the seven standard folders
# at the workspace root (the Human ruling 2026-11-22) - additive to the
# frozen six the method's flip quotes.
