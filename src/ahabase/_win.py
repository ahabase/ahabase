"""The Windows arm of the platform dispatch.

Safe's platform specifics live in one sibling per platform, chosen once at
import (see ``safe.py``); this arm carries the Windows side of each. The
lock itself goes through the ``filelock`` library on both platforms -
``filelock`` locks via ``msvcrt`` here, and owner-only rests on the user
profile directory's ACLs, which the manifest and its lock file inherit
(the manifest lives under the profile; NTFS has no ``0o600`` bit to
honor).

Implements: implementation-ahabase-safe-windows-blueprint
Blueprint: implementation-ahabase-safe-windows-blueprint

Capability: platform-dispatch
"""

from __future__ import annotations

import contextlib
import os

from filelock import FileLock

# The askpass no-op: a program that exists on every Windows and exits
# immediately when given no DLL to load - rundll32 without arguments does
# nothing and returns, so git's askpass call yields nothing instead of
# popping a prompt (there is no ``true`` on Windows).
ASKPASS_NOOP = "rundll32"


def _pathext() -> list[str]:
    """The OS's executable suffixes, lowercased (PATHEXT decides here)."""
    raw = os.environ.get("PATHEXT", ".com;.exe;.bat;.cmd")
    return [s.strip().lower() for s in raw.split(";") if s.strip()]


@contextlib.contextmanager
def lock(path, timeout=-1.0):
    """Exclusive inter-process lock, released on process death.

    Owner-only is the parent directory's ACL (the user profile), which
    the lock file inherits; there is no mode bit to set on NTFS.
    ``timeout`` bounds the wait in seconds (-1 waits indefinitely); on
    expiry ``filelock.Timeout`` raises.
    """
    with FileLock(str(path), timeout=timeout):
        yield


def exec_base_name(path):
    """The name to match against NOT_BINDABLE - the PATHEXT suffix
    stripped (python.exe -> python): the suffix is how the OS finds the
    file, not part of who runs what (which file is executable at all is
    ``shutil.which``'s to answer, per OS)."""
    name = os.path.basename(str(path)).lower()
    for suffix in _pathext():
        if name.endswith(suffix) and len(name) > len(suffix):
            return name[: -len(suffix)]
    return name
