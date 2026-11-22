"""The safe's git credential helper (AHA-0019 R1), on fictional secrets only."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import ahabase.safe as safe_module
import ahabase.cli_safe as cli_safe
from ahabase.safe import Safe, parse_credential_request

FAKE_VALUE = "fixture-value-0123456789"
HOST = "fixture.github.example"
REQUEST = f"protocol=https\nhost={HOST}\n\n"


def _safe_with_gh() -> Safe:
    s = Safe()
    s.set("fixture-gh", FAKE_VALUE, store="memory", purpose="git helper tests")
    s.target_add("fixture-gh", {"kind": "git-credential", "host": HOST,
                                "account": "1148"})
    return s


# request parsing -----------------------------------------------------------

def test_parse_splits_on_the_first_equals_and_lowercases_the_host():
    req = parse_credential_request("protocol=https\nhost=GitHub.COM\n"
                                   "password=a=b=c\nhost=ignored.example\n\n")
    assert req["host"] == "github.com"
    assert req["password"] == "a=b=c"


def test_parse_reads_a_url_line_when_git_did_not_split_it():
    req = parse_credential_request(f"url=https://{HOST}/org/repo.git\n\n")
    assert req["host"] == HOST and req["protocol"] == "https"


# the answer ----------------------------------------------------------------

def test_answers_the_value_of_the_matching_target():
    answer = _safe_with_gh().credential(parse_credential_request(REQUEST))
    assert answer == {"username": "1148", "password": FAKE_VALUE}


def test_unknown_host_answers_nothing():
    s = _safe_with_gh()
    assert s.credential(parse_credential_request(
        "protocol=https\nhost=other.example\n\n")) is None


def test_a_username_in_the_request_selects_the_account():
    s = _safe_with_gh()
    other = parse_credential_request(f"protocol=https\nhost={HOST}\n"
                                     "username=somebody-else\n\n")
    assert s.credential(other) is None  # not this target's account: no answer
    same = parse_credential_request(f"protocol=https\nhost={HOST}\n"
                                    "username=1148\n\n")
    assert s.credential(same) == {"username": "1148", "password": FAKE_VALUE}


def test_a_manifest_entry_without_its_value_names_the_remedy():
    s = _safe_with_gh()
    s.stores["memory"].delete("fixture-gh")  # the entry stands, the value is gone
    try:
        s.credential(parse_credential_request(REQUEST))
    except safe_module.SafeError as error:
        assert "fixture-gh" in str(error) and FAKE_VALUE not in str(error)
        assert "ahabase safe set fixture-gh" in str(error)
    else:
        raise AssertionError("a manifest entry without its value must fail loud")


# the CLI verb ----------------------------------------------------------------

def _invoke(monkeypatch, verb, request, *, s=None):
    s = s or _safe_with_gh()
    monkeypatch.setattr(cli_safe, "make_safe", lambda: s)
    from click.testing import CliRunner
    return CliRunner().invoke(cli_safe.safe_credential, [verb], input=request)


def test_get_prints_only_the_protocol_answer(monkeypatch):
    result = _invoke(monkeypatch, "get", REQUEST)
    assert result.exit_code == 0
    assert result.stdout == f"username=1148\npassword={FAKE_VALUE}\n\n"
    assert result.stderr == ""


def test_get_for_an_unknown_host_prints_nothing(monkeypatch):
    result = _invoke(monkeypatch, "get", "protocol=https\nhost=other.example\n\n")
    assert result.exit_code == 0 and result.stdout == ""


def test_store_and_erase_never_write_the_safe(monkeypatch):
    s = _safe_with_gh()
    for verb in ("store", "erase"):
        result = _invoke(monkeypatch, verb, s=s,
                         request=f"protocol=https\nhost={HOST}\nusername=1148\n"
                                 f"password={FAKE_VALUE}\n\n")
        assert result.exit_code == 0
        assert FAKE_VALUE not in result.stdout  # the value crosses no pipe here
        assert "ahabase safe set" in result.stderr
    assert set(s.entries()) == {"fixture-gh"}  # the manifest is untouched
    assert s.stores["memory"].get("fixture-gh") == FAKE_VALUE


def test_a_missing_value_fails_soft_with_the_remedy(monkeypatch):
    s = _safe_with_gh()
    s.stores["memory"].delete("fixture-gh")
    result = _invoke(monkeypatch, "get", REQUEST, s=s)
    assert result.exit_code == 0 and result.stdout == ""  # git's contract
    assert "ahabase safe set fixture-gh" in result.stderr
    assert FAKE_VALUE not in result.stderr


def test_capability_answers_empty(monkeypatch):
    result = _invoke(monkeypatch, "capability", "")
    assert result.exit_code == 0 and result.stdout == ""


# the protocol itself ----------------------------------------------------------

def test_git_credential_fill_asks_the_helper(tmp_path, monkeypatch):
    """A real ``git credential fill`` resolves through the helper end to end.

    The child process cannot see this process's stores, so the fixture
    manifest names the env store and the value rides an environment
    variable of the child only (the read surface under test is the same).
    """
    manifest = tmp_path / "safe.json"
    manifest.write_text(json.dumps({"secrets": {"fixture-gh": {
        "store": "env", "key": "FIXTURE_GH", "purpose": "git helper tests",
        "targets": [{"kind": "git-credential", "host": HOST, "account": "1148"}],
    }}}), encoding="utf-8")
    monkeypatch.setenv("AHABASE_SAFE_MANIFEST", str(manifest))
    monkeypatch.setenv("FIXTURE_GH", FAKE_VALUE)
    src = str(Path(safe_module.__file__).parent.parent)
    # git runs the helper through its own shell: forward slashes survive on Windows
    helper = f'!"{Path(sys.executable).as_posix()}" -m ahabase safe credential'
    out = subprocess.run(
        ["git", "-c", "credential.helper=", "-c", f"credential.helper={helper}", "credential", "fill"],  # the empty value resets system helpers (Windows runners ship Git Credential Manager)
        input=REQUEST, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": src}, timeout=60)
    assert out.returncode == 0, out.stderr
    assert "username=1148" in out.stdout
    assert f"password={FAKE_VALUE}" in out.stdout
