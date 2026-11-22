"""The key helper against the real safe (AHA-0024 R3c measurement).

These tests use the safe's own classes (a manifest in a temporary directory and
its in-memory store), so no keychain is touched and no owner step is performed.
They measure what the blueprint relies on: the safe releases a value only to a
command bound with the prefix ``llm key``, compared by exact string, and the
plain ``resolve`` does not check the consumer (which is why the helper never
uses it). The end-to-end run through the owner's terminal is an owner step.
"""

from __future__ import annotations

import os
import stat
import sys

import pytest

from ahabase.safe import MemoryStore, Safe, SafeError
from ahabase.llm import paths

pytestmark = pytest.mark.skipif(os.name == "nt", reason="the binding is measured on POSIX executables here")

VALUE = "CANARY-binding-0123456789abcdef"


@pytest.fixture
def bound(tmp_path):
    exe = tmp_path / "bin" / "ahabase"
    exe.parent.mkdir()
    exe.write_text("#!/bin/sh\nexit 0\n")
    exe.chmod(stat.S_IRWXU)
    safe = Safe(path=tmp_path / "safe.json", stores={"memory": MemoryStore()})
    safe.set("VAULT", VALUE, store="memory")
    safe.bind("VAULT", str(exe), prefix=("llm", "key"))
    return safe, str(exe), tmp_path


def test_the_bound_command_with_the_prefix_is_released_the_value(bound):
    safe, exe, _ = bound
    safe.check_consumer("VAULT", [exe, "llm", "key", "p", "--emit"])
    assert paths.resolve_auth("safe://VAULT", argv=[exe, "llm", "key", "p"], safe=safe) == VALUE


def test_another_prefix_or_command_is_refused(bound):
    safe, exe, tmp_path = bound
    for argv in ([exe, "llm", "other"], [exe, "safe", "get", "VAULT"], [exe]):
        with pytest.raises(paths.AuthError):
            paths.resolve_auth("safe://VAULT", argv=argv, safe=safe)
    other = tmp_path / "bin" / "other"
    other.write_text("#!/bin/sh\n")
    other.chmod(stat.S_IRWXU)
    with pytest.raises(paths.AuthError):
        paths.resolve_auth("safe://VAULT", argv=[str(other), "llm", "key", "p"], safe=safe)


def test_the_comparison_is_by_exact_string_so_relative_and_symlinked_forms_are_refused(bound, monkeypatch):
    safe, exe, tmp_path = bound
    monkeypatch.chdir(tmp_path / "bin")
    with pytest.raises(paths.AuthError):  # a bare name is resolved against the working directory by abspath
        paths.resolve_auth("safe://VAULT", argv=["ahabase", "llm", "key", "p"], safe=safe)
    link = tmp_path / "link"
    link.symlink_to(exe)
    with pytest.raises(paths.AuthError):
        paths.resolve_auth("safe://VAULT", argv=[str(link), "llm", "key", "p"], safe=safe)
    monkeypatch.setattr(sys, "argv", ["ahabase", "llm", "key", "p"])
    monkeypatch.chdir(tmp_path)  # elsewhere than the install directory
    with pytest.raises(paths.AuthError):  # the default consumer is abspath(argv[0]) too
        paths.resolve_auth("safe://VAULT", safe=safe)


def test_a_bare_name_is_granted_only_when_the_working_directory_is_the_bound_file_directory(bound, monkeypatch):
    """The residual: abspath of a bare argv[0] equals the bound path exactly when the working
    directory is the install directory. The grant is then to the very file that was bound (its
    digest is checked), so it is not a bypass; any other directory is refused (fail-closed)."""
    safe, exe, tmp_path = bound
    monkeypatch.chdir(tmp_path / "bin")
    monkeypatch.setattr(sys, "argv", ["ahabase", "llm", "key", "p"])
    assert paths.resolve_auth("safe://VAULT", safe=safe) == VALUE


def test_the_plain_resolve_does_not_check_the_consumer_so_the_helper_never_uses_it(bound):
    safe, _, _ = bound
    assert safe.resolve("safe://VAULT") == VALUE  # no consumer check: the reason the helper goes through safe run
    with pytest.raises(SafeError):
        safe.check_consumer("VAULT", ["/bin/echo", "x"])


def test_a_changed_executable_is_refused_until_it_is_bound_again(bound):
    safe, exe, _ = bound
    with open(exe, "a") as handle:
        handle.write("# changed\n")
    with pytest.raises(paths.AuthError):
        paths.resolve_auth("safe://VAULT", argv=[exe, "llm", "key", "p"], safe=safe)
