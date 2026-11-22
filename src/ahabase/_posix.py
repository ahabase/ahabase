"""The POSIX arm of the platform dispatch (macOS, Linux).

Safe's platform specifics live in one sibling per platform, chosen once at
import (see ``safe.py``); this arm carries the POSIX side of each. The lock
itself goes through the ``filelock`` library on both platforms - only the
lock file's creation mode differs here.

Implements: implementation-ahabase-safe-windows-blueprint
Blueprint: implementation-ahabase-safe-windows-blueprint

Capability: platform-dispatch
"""

from __future__ import annotations

import contextlib
import os

from filelock import FileLock

# The askpass no-op: the Unix ``true`` - exists everywhere here, exits 0,
# so git's askpass call yields nothing instead of prompting.
ASKPASS_NOOP = "true"


@contextlib.contextmanager
def lock(path, timeout=-1.0):
    """Exclusive inter-process lock, released on process death.

    The lock file is created 0o600 so its bytes are owner-only from the
    first byte (``FileLock`` alone would create it world-readable under
    the default umask). ``timeout`` bounds the wait in seconds (-1 waits
    indefinitely); on expiry ``filelock.Timeout`` raises.
    """
    fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    os.close(fd)
    with FileLock(str(path), timeout=timeout):
        yield


def exec_base_name(path):
    """The name to match against NOT_BINDABLE (no exec suffix on POSIX)."""
    return os.path.basename(str(path)).lower()
