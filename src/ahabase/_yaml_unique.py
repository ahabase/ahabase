"""YAML loading that does not hide a duplicated mapping key.

Graduated from the method CLI's loader (pilot graduation 1, AHA-0021).
``yaml.safe_load`` keeps the last of two equal keys without a word, so a
hand-added second key silently replaces the first block - the original
finding was a second ``subepics`` in the CLI settings dropping a whole
SubEpic. This loader finds every duplicate with its line; ``strict``
raises, otherwise one warning per duplicate goes to stderr and the usual
last-wins value is returned, so an instance keeps working until its file
is repaired (strict would stop every command on an instance until then).

Implements: implementation-ahabase-config-door-blueprint
Blueprint: implementation-ahabase-config-door-blueprint

Capability: config-management
"""

from __future__ import annotations

import sys

import yaml


class DuplicateKeyError(ValueError):
    """A mapping in a YAML document repeats a key."""


def _loader(found: list[tuple[str, int]]):
    class UniqueKeyLoader(yaml.SafeLoader):
        pass

    def construct_mapping(loader, node, deep=False):
        seen: set = set()
        for key_node, _ in node.value:
            key = loader.construct_object(key_node, deep=deep)
            try:
                if key in seen:
                    found.append((str(key), key_node.start_mark.line + 1))
                seen.add(key)
            except TypeError:  # an unhashable key - yaml itself refuses it later
                pass
        return yaml.SafeLoader.construct_mapping(loader, node, deep)

    UniqueKeyLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    return UniqueKeyLoader


def duplicates(text: str) -> list[tuple[str, int]]:
    """(key, line) of every repeated key in the document."""
    found: list[tuple[str, int]] = []
    yaml.load(text, Loader=_loader(found))  # noqa: S506 - a SafeLoader subclass
    return found


def load(text: str, source: str, strict: bool):
    """The parsed document; a repeated key raises (strict) or warns."""
    found: list[tuple[str, int]] = []
    data = yaml.load(text, Loader=_loader(found))  # noqa: S506 - a SafeLoader subclass
    if found:
        where = ", ".join(f"'{key}' at line {line}" for key, line in found)
        message = (f"{source}: duplicated key {where} - YAML keeps only the "
                   f"last, the earlier block is ignored; merge them")
        if strict:
            raise DuplicateKeyError(message)
        if message not in _WARNED:  # once per process: settings load often
            _WARNED.add(message)
            print(f"Warning: {message}", file=sys.stderr)
    return data


_WARNED: set[str] = set()
