"""The wiki projection: the Epic's knowledge as a GitHub-wiki mirror.

Graduated from the method CLI's wiki layer (the AHA-0036 dossier): the
four proven operations - generate (``_Sidebar.md`` and ``Home.md`` from
the config), sync (the ``_grid4d/`` documents into the local mirror,
purging what the config no longer accounts for), check (duplicate
detection), clean (dedupe, root copy wins) - plus publish, the tail the
method side never had: the mirror becomes a clone of the repository's
wiki remote, the synced delta commits, and the push rides the safe's
credential chain under the Epic's declared GitHub account.

The mirror lives at ``<workspace>/_wikis/<epic>.wiki`` (one of the seven
standard folders) and the config at ``<workspace>/_config/<epic>.wiki.yaml``
- absent or empty means the defaults: the standard mirror path, the
``_grid4d/`` source, no document mapping. The door is epic-explicit: the
``--epic`` option names the Epic, never an ambient resolution.

Implements: implementation-ahabase-wiki-door-blueprint
Blueprint: implementation-ahabase-wiki-door-blueprint

Capability: wiki-projection
"""
