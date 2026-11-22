"""Test isolation: nothing of the real instance is ever touched (AHA-0002 R5).

Every test runs with the workspace, the safe's manifest and the home
directory pointed at a temporary directory (HOME on POSIX, HOME and
USERPROFILE on Windows - ``Path.home()`` reads the latter there), and with
a keyring backend that fails the test if it is called - a test that needs
the OS store installs a fake one.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import keyring
import keyring.backend
import pytest


class GuardKeyring(keyring.backend.KeyringBackend):
    """Fails any test that reaches the OS store without a fake."""

    priority = 1

    def get_password(self, service, username):
        raise AssertionError("a test reached the real OS keyring")

    def set_password(self, service, username, password):
        raise AssertionError("a test reached the real OS keyring")

    def delete_password(self, service, username):
        raise AssertionError("a test reached the real OS keyring")


def _symlinks_supported() -> bool:
    """Whether this OS and account may create symlinks.

    POSIX always may; Windows needs Developer Mode or an elevated runner,
    and the binding tests that rebind through a link measure that ability.
    """
    if os.name != "nt":
        return True
    try:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "t"
            target.write_text("")
            (Path(tmp) / "l").symlink_to(target)
    except OSError:
        return False
    return True


SYMLINKS = _symlinks_supported()


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    # isolation through the home directory only: the safe's override
    # variables are what the threat model guards (T9), so tests use the
    # default location inside a temporary home, as production does
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    if sys.platform == "win32":
        monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("AHABASE_HOME", raising=False)
    monkeypatch.delenv("AHABASE_SAFE_MANIFEST", raising=False)
    # the config door's overrides (AHA-0021): a test points the door
    # somewhere explicitly or nowhere - never at the real instance
    monkeypatch.delenv("AHABASE_WORKSPACE", raising=False)
    monkeypatch.delenv("AHABASE_CONFIG", raising=False)
    previous = keyring.get_keyring()
    keyring.set_keyring(GuardKeyring())
    yield tmp_path
    keyring.set_keyring(previous)
