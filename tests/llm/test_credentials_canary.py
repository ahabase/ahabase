"""Safe first (AHA-0024): a planted credential value never reaches output, a log or a file.

A recognisable value is planted in every source the ported code can read - an
injected variable, a safe entry, a key helper's output, a literal in a
definition - and the code is exercised on each path. The value must appear in
no captured output, no log record and no file written under the temporary
home. This module grows with each family; R3a covers paths and discovery.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

from ahabase.llm import discovery, paths

CANARY = "CANARY-7f3a91c2-credential-value"


class FakeSafe:
    def check_consumer(self, name, argv):
        return {}

    def get(self, name):
        return CANARY


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(paths, "CREDENTIALS_PATH", tmp_path / ".credentials.json")
    monkeypatch.setattr(paths, "AWS_CREDENTIALS_PATH", tmp_path / "aws" / "credentials")
    monkeypatch.setattr(paths, "AWS_SSO_CACHE_PATH", tmp_path / "aws" / "sso")
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: False)
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("CANARY_KEY", CANARY)
    return tmp_path


def files_under(root: Path):
    return [p for p in root.rglob("*") if p.is_file()]


def test_the_value_reaches_the_caller_only(home, capsys, caplog):
    caplog.set_level(logging.DEBUG)
    ladder = {
        "by-env": {"base_url": "http://a", "model": "m", "auth": "env:CANARY_KEY"},
        "by-safe": {"base_url": "http://b", "model": "m", "auth": "safe://ANY"},
        "by-helper": {"base_url": "http://c", "model": "m", "auth": "env:NONE",
                      "key_helper": f'"{sys.executable}" -c "print(\'{CANARY}\')"'},
    }
    # the values are returned to the caller ...
    assert paths.resolve_key(ladder["by-env"]) == CANARY
    assert paths.resolve_key(ladder["by-safe"], argv=["x"], safe=FakeSafe()) == CANARY
    assert paths.resolve_key(ladder["by-helper"]) == CANARY
    # ... and every other surface that touches the same sources stays clean
    registry = home / "registry.yml"
    result = discovery.discover(env={}, registry_path=registry, builtin=ladder)
    discovery.assess_local_availability(env={"CANARY_KEY": CANARY}, builtin=ladder)
    paths.known_paths(builtin=ladder)
    paths.current_path({}, builtin=ladder)
    try:
        paths.resolve_auth("sk-" + CANARY)
    except paths.AuthError as error:
        assert CANARY not in str(error) and CANARY not in repr(error)

    out, err = capsys.readouterr()
    assert CANARY not in out + err
    assert CANARY not in caplog.text
    assert CANARY not in repr(result)
    for file in files_under(home):
        assert CANARY not in file.read_text(encoding="utf-8", errors="ignore"), file


def test_a_literal_in_a_variants_file_is_refused_and_not_copied(home):
    variants = home / "variants.yaml"
    variants.write_text(f"paths:\n  leak: {{status: available, base_url: 'http://a', model: m, auth: '{CANARY}'}}\n",
                        encoding="utf-8")
    with pytest.raises(paths.AuthError) as raised:
        discovery.discover(env={}, update_registry=False, variants_file=variants)
    assert CANARY not in str(raised.value)


# --- R3b: verification ----------------------------------------------------------

def test_a_key_echoed_by_an_endpoint_never_survives_verification(home, capsys, caplog, tmp_path):
    import json as _json
    from ahabase.llm import verify
    from .test_verify import Gateway

    caplog.set_level(logging.DEBUG)
    echo = Gateway(status=500, body={"error": f"upstream rejected {CANARY}"})
    try:
        ladder = {"gw": {"base_url": echo.url, "model": "m", "auth": "env:CANARY_KEY"}}
        results = [
            verify.verify_path("gw", builtin=ladder),
            *verify.verify_path_family(["gw", "claude-pro"], stagger_seconds=0, builtin=ladder),
        ]
        rows = []

        def session_out(path_id, env=None, **kwargs):
            file = tmp_path / "payload.json"
            file.write_text(_json.dumps({"env": {"ANTHROPIC_AUTH_TOKEN": CANARY}}))
            return {"file": str(file)}

        failing = lambda payload, lean=False: verify.redacted(
            {"ok": False, "detail": f"401 {CANARY}"}, payload["env"].get("ANTHROPIC_AUTH_TOKEN"))
        verify.first_working_path(["gw"], prove=failing, report=rows.append, session_out=session_out, builtin=ladder)
        results.extend(rows)
        assert not (tmp_path / "payload.json").exists()  # a failed proof leaves no payload carrying the key
    finally:
        echo.close()
    out, err = capsys.readouterr()
    assert CANARY not in _json.dumps(results) and CANARY not in out + err and CANARY not in caplog.text
    for file in files_under(home):
        assert CANARY not in file.read_text(encoding="utf-8", errors="ignore"), file


# --- R3c: the switch, the payload, the restore ------------------------------------

def test_the_switch_the_payload_and_the_restore_never_write_the_value(home, capsys, caplog):
    import json as _json
    from ahabase.llm import session, switch
    from .test_verify import MESSAGE, Gateway

    caplog.set_level(logging.DEBUG)
    gateway = Gateway(body=MESSAGE)
    try:
        exe = str(Path(sys.executable).resolve())
        ladder = {"gw": {"base_url": gateway.url, "model": "m", "auth": "env:CANARY_KEY"}}
        paths.SETTINGS_PATH.write_text(_json.dumps({"env": {"ANTHROPIC_BASE_URL": gateway.url}}), encoding="utf-8")
        written = session.session_env_out("gw", env={"CANARY_KEY": CANARY}, epic="e", builtin=ladder, executable=exe)
        result = switch.switch_path("gw", confirm=True, env={"CANARY_KEY": CANARY}, builtin=ladder,
                                    prove=False, executable=exe)
        restored = switch.restore_backup(latest=True, confirm=True, prove=False)
        listing = switch.list_backups()
    finally:
        gateway.close()
    out, err = capsys.readouterr()
    everything = _json.dumps([written, result, restored, listing])
    assert CANARY not in everything and CANARY not in out + err and CANARY not in caplog.text
    contents = [p for p in files_under(home)]
    assert len(contents) >= 4  # settings, two backups, the payload
    for file in contents:
        assert CANARY not in file.read_text(encoding="utf-8", errors="ignore"), file
