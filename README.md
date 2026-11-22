# ahabase

The open door to an ahabase knowledge workspace: the grid4d format, the
services every door needs, and the doors themselves - the `ahabase` CLI
now, an MCP server and a Claude Code plugin next - over one registry that
plugins fill.

> **The source repository is private until the first release.** The
> package on its channel is the public face; the repository becomes
> public only by the owner's decision, together with the first real
> release.

## Install (consumers)

For a machine outside the development repositories: your own Epics in
your own repositories, the package from its channel. The dry-run
channel is TestPyPI today; at the public release the extra-index line
below is the one line that goes:

> **The `ahabase` name is not reserved on either index yet.** The
> install line below is trusted only once the first release reserves
> the name; until then it points at a dry-run channel.

```bash
python3 -m venv .venv
.venv/bin/pip install --extra-index-url https://test.pypi.org/simple/ ahabase
.venv/bin/ahabase --version
.venv/bin/ahabase doctor
```

The first commands after install, nothing else needed - no repository
access, no workspace on disk:

```bash
.venv/bin/ahabase --version   # the door opens
.venv/bin/ahabase doctor      # installation checks: Python, package, plugins
.venv/bin/python -c "import ahabase; print(ahabase.__version__)"
```

### Environment keys: the CI exception

Two environment keys override file configuration - a documented
explicit exception for CI and transitional use, never the default
path, and standing (there is no removal story for them):

- `AHABASE_WORKSPACE` - the workspace root (default: `~/ahabase`)
- `AHABASE_CONFIG` - a settings-file path, any epic

The `env` store of `ahabase safe` reads values from environment
variables the same way: read-only, for CI, never the interactive
default (see [Secrets](#secrets-ahabase-safe) below).

## Install (development)

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/ahabase --version
.venv/bin/ahabase doctor
.venv/bin/python -m pytest
```

## Plugins

A plugin is a Python distribution with an entry point in the group
`ahabase.plugins`, pointing at a module with `API_VERSION` (the registry
API major version it needs) and `register(registry)`:

```toml
[project.entry-points."ahabase.plugins"]
example = "example_plugin"
```

```python
import click

API_VERSION = 1

def register(registry):
    @click.command("hello")
    def hello():
        click.echo("hello")
    registry.add_command(hello)
    registry.add_check("example", lambda: (True, "ok"))
```

`ahabase doctor` lists every plugin with the distribution it came from;
a plugin that fails, needs another API version or takes a name already in
use is reported and never breaks the CLI. Installing a plugin means
trusting its code.

## Secrets: `ahabase safe`

Configuration holds references (`safe://NAME`), never values; the value
lives in your own store (the OS keychain by default) and reaches only the
consumers you bound to it, with no other exported value:

```bash
ahabase safe set jira-api --purpose "issue tracker"   # value read hidden
ahabase safe bind jira-api "$(command -v some-tool)"  # once, by absolute path
ahabase safe list                                     # names, metadata, consumers
ahabase safe run --env JIRA_TOKEN=safe://jira-api -- some-tool ...
ahabase safe compare jira-api --env JIRA_TOKEN        # same/different, no value
ahabase safe get jira-api --reveal                    # you, at a terminal
```

Shells, interpreters and general-purpose network tools (`curl`, `gh`,
`git`) cannot be bound - they would hand a value to whatever their
arguments say. `git` asks `ahabase safe credential`, the safe's own
read-only credential helper, and `gh` reads the login the safe's
`gh-login` target writes; see [docs/safe.md](docs/safe.md) - the
tutorial - and
`_grid4d/implementation/implementation-ahabase-safe-integration-blueprint.md`.
Every refusal tells you the command that proceeds.

## License

Apache-2.0 - see [LICENSE](LICENSE).
