"""Verification (AHA-0024 R3b): the request, the classes of failure, the launch proof, the search."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from ahabase.llm import paths, verify

KEY = "CANARY-key-0123456789abcdef"


class Gateway:
    """A local endpoint whose answer a test chooses."""

    def __init__(self, status=200, body=None, raw=None):
        self.status, self.body, self.raw = status, body, raw
        self.requests = []
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _answer(self):
                length = int(self.headers.get("content-length") or 0)
                payload = self.rfile.read(length).decode() if length else ""
                gateway.requests.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()}, "body": payload})
                data = gateway.raw if gateway.raw is not None else json.dumps(gateway.body or {}).encode()
                self.send_response(gateway.status)
                self.send_header("content-type", "application/json")
                self.send_header("content-length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = _answer

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def gateway():
    created = []

    def make(**kwargs):
        created.append(Gateway(**kwargs))
        return created[-1]

    yield make
    for item in created:
        item.close()


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(paths, "CREDENTIALS_PATH", tmp_path / ".credentials.json")
    monkeypatch.setattr(paths, "AWS_CREDENTIALS_PATH", tmp_path / "aws" / "credentials")
    monkeypatch.setattr(paths, "AWS_SSO_CACHE_PATH", tmp_path / "aws" / "sso")
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: False)
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    for name in ("AWS_ACCESS_KEY_ID", "CANARY_KEY"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


MESSAGE = {"type": "message", "content": [{"type": "text", "text": "pong"}], "model": "m1"}


# --- the request --------------------------------------------------------------

def test_a_plain_probe_is_ok_only_on_200_with_a_message(gateway):
    g = gateway(body=MESSAGE)
    result = verify._post_messages(g.url, "m1", KEY, headers=verify.TOKEN_HEADERS)
    assert result["ok"] and result["status"] == 200
    sent = json.loads(g.requests[-1]["body"])
    assert sent["max_tokens"] == 8 and g.requests[-1]["path"] == "/v1/messages"
    assert g.requests[-1]["headers"]["authorization"] == f"Bearer {KEY}"
    assert "x-api-key" not in g.requests[-1]["headers"]


def test_a_key_helper_path_sends_both_headers(gateway):
    g = gateway(body=MESSAGE)
    verify._post_messages(g.url, "m1", KEY, headers=verify.HELPER_HEADERS)
    names = set(g.requests[-1]["headers"])
    assert {"x-api-key", "authorization"} <= names
    assert verify.key_headers({"key_helper": "x"}) == verify.HELPER_HEADERS
    assert verify.key_headers({}) == verify.TOKEN_HEADERS


def test_an_unexpected_or_unreadable_body_is_not_ok(gateway):
    assert verify._post_messages(gateway(body={"x": 1}).url, "m")["status"] == "bad-response"
    assert verify._post_messages(gateway(raw=b"not json").url, "m")["status"] == "bad-response"


def test_an_http_error_is_reported_with_its_status_and_the_key_is_redacted(gateway):
    g = gateway(status=401, body={"error": f"invalid key {KEY}"})
    result = verify._post_messages(g.url, "m", KEY)
    assert not result["ok"] and result["status"] == 401
    assert KEY not in result["detail"] and "<key>" in result["detail"]


def test_an_unreachable_endpoint_is_reported(gateway):
    g = gateway()
    url = g.url
    g.close()
    result = verify._post_messages(url, "m", KEY)
    assert not result["ok"] and result["status"] == "unreachable"


def test_the_forced_tool_probe_verdicts(gateway):
    ok = gateway(body={"content": [{"type": "tool_use", "name": "verify_tool_probe"}], "model": "m"})
    assert verify._post_messages(ok.url, "m", require_tool_use=True)["ok"]
    sent = json.loads(ok.requests[-1]["body"])
    assert sent["tool_choice"] == {"type": "tool", "name": "verify_tool_probe"} and sent["max_tokens"] == 1000
    truncated = gateway(body={"content": [], "stop_reason": "max_tokens"})
    assert verify._post_messages(truncated.url, "m", require_tool_use=True)["status"] == "inconclusive-truncated"
    plain = gateway(body={"content": [{"type": "text", "text": "x"}], "stop_reason": "end_turn"})
    assert verify._post_messages(plain.url, "m", require_tool_use=True)["status"] == "no-tool-use"


# --- verify_path --------------------------------------------------------------

def test_unknown_path_and_a_pin_the_definition_cannot_honour(home):
    assert verify.verify_path("nope")["status"] == "unknown-path"
    ladder = {"p": {"base_url": "", "model": "m", "auth": "env:K", "pin_model": True}}
    result = verify.verify_path("p", builtin=ladder)
    assert result["status"] == "definition" and not result["ok"]


def test_the_subscription_route_verifies_by_its_login(home):
    assert verify.verify_path("claude-pro")["status"] == "no-login"
    paths.CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
    assert verify.verify_path("claude-pro") ["ok"]


def test_the_cloud_route_verifies_by_its_credential_chain(home):
    assert verify.verify_path("bedrock", env={})["status"] == "no-credentials"
    assert verify.verify_path("bedrock", env={"AWS_ACCESS_KEY_ID": "x"})["status"] == "credentials"


def test_an_endpoint_path_sends_the_resolved_key_and_redacts_it(gateway, home):
    g = gateway(status=500, body={"error": f"boom {KEY}"})
    ladder = {"gw": {"base_url": g.url, "model": "m", "auth": "env:CANARY_KEY"}}
    result = verify.verify_path("gw", env={"CANARY_KEY": KEY}, builtin=ladder)
    assert not result["ok"] and KEY not in json.dumps(result)
    assert g.requests[-1]["headers"]["authorization"] == f"Bearer {KEY}"


def test_a_missing_variable_is_a_note_not_a_gate(gateway, home):
    g = gateway(body=MESSAGE)
    ladder = {"gw": {"base_url": g.url, "model": "m", "auth": "env:CANARY_KEY"}}
    result = verify.verify_path("gw", env={}, builtin=ladder)
    assert result["ok"] and "no key sent" in result["detail"]


def test_the_tool_probe_set_is_passed_in_and_an_explicit_flag_overrides_it(gateway, home):
    g = gateway(body={"content": [{"type": "tool_use"}], "model": "m"})
    ladder = {"gw": {"base_url": g.url, "model": "m", "auth": "env:CANARY_KEY"}}
    verify.verify_path("gw", env={}, builtin=ladder, tool_probe_paths=frozenset({"gw"}))
    assert "tool_choice" in json.loads(g.requests[-1]["body"])
    verify.verify_path("gw", env={}, builtin=ladder, tool_probe_paths=frozenset({"gw"}), require_tool_use=False)
    assert "tool_choice" not in json.loads(g.requests[-1]["body"])
    verify.verify_path("gw", env={}, builtin=ladder)
    assert "tool_choice" not in json.loads(g.requests[-1]["body"])


def test_a_reference_the_command_may_not_read_is_an_auth_refusal_without_a_value(home):
    class Refusing:
        def check_consumer(self, name, argv):
            from ahabase.safe import SafeError
            raise SafeError("not a bound consumer")

        def get(self, name):
            raise AssertionError("must not be read")
    ladder = {"v": {"base_url": "http://127.0.0.1:1", "model": "m", "auth": "safe://NAME"}}
    result = verify.verify_path("v", builtin=ladder, argv=["x"], safe=Refusing())
    assert result["status"] == "auth-refused" and not result["ok"]


def test_a_definition_with_a_literal_credential_is_refused_not_verified(home):
    with pytest.raises(paths.AuthError):
        verify.verify_path("x", builtin={"x": {"base_url": "http://a", "auth": "sk-literal-0123456789"}})


def test_the_family_is_staggered_and_one_failure_does_not_skip_the_rest(home):
    slept = []
    rows = verify.verify_path_family(["nope", "claude-pro", "bedrock"], stagger_seconds=2.5,
                                    env={}, sleep=slept.append)
    assert [r["path"] for r in rows] == ["nope", "claude-pro", "bedrock"]
    assert slept == [2.5, 2.5]
    assert verify.verify_path_family(["nope", "nope"], stagger_seconds=0, sleep=slept.append)
    assert slept == [2.5, 2.5]


# --- reachability -------------------------------------------------------------

def test_reachable_counts_any_http_answer_and_tries_the_suffixes_in_order(gateway):
    assert verify.reachable(gateway(status=200, body={}).url) == (True, 200)
    assert verify.reachable(gateway(status=404, body={}).url) == (True, 404)
    g = gateway()
    url = g.url
    g.close()
    assert verify.reachable(url, timeout=1) == (False, None)


# --- classification -----------------------------------------------------------

@pytest.mark.parametrize("detail,cls", [
    ("Please run /login to continue", "auth"),
    ("the OAuth token has expired", "auth"),
    ("ExpiredToken: the security token included in the request is expired", "auth"),
    ("HTTP 429 from http://x", "transient"),
    ("rate limit reached", "transient"),
    ("no answer within 180s", "transient"),
    ("the claude command is not on PATH", "cli"),
    ("exit 2", "cli"),
    ("exit -1", "cli"),
    ("", "cli"),
    ("HTTP 404 from http://x: no such model", "unavailable"),
    ("1500 tokens were used", "unavailable"),
    ("the processor associated with this model", "unavailable"),
])
def test_classify_failure(detail, cls):
    assert verify.classify_failure(detail) == cls


def test_auth_is_decided_before_transient():
    assert verify.classify_failure("token has expired after a timeout") == "auth"


def test_every_class_has_a_hint():
    assert set(verify.FAILURE_HINTS) == {"auth", "transient", "cli", "unavailable", "config"}


def test_redaction_replaces_only_secrets_long_enough_to_be_specific():
    assert verify.redacted({"detail": f"x {KEY} y"}, KEY)["detail"] == "x <key> y"
    assert verify.redacted({"detail": "abc abc"}, "abc")["detail"] == "abc abc"
    assert verify.redacted({"detail": "x"}, None, "")["detail"] == "x"


# --- the launch proof ---------------------------------------------------------

def test_probe_cwd_is_one_private_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(verify.tempfile, "gettempdir", lambda: str(tmp_path))
    first = verify.probe_cwd()
    assert first == verify.probe_cwd() and first.is_dir()


def test_probe_cwd_replaces_a_planted_file_a_symlink_and_a_writable_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(verify.tempfile, "gettempdir", lambda: str(tmp_path))
    planted = tmp_path / "ahabase-llm-prove"
    planted.write_text("x")
    assert verify.probe_cwd() != planted and verify.probe_cwd().is_dir()
    planted.unlink()
    if hasattr(os, "getuid"):
        planted.mkdir()
        planted.chmod(0o777)
        assert verify.probe_cwd() != planted
        planted.rmdir()
        target = tmp_path / "elsewhere"
        target.mkdir()
        planted.symlink_to(target)
        assert verify.probe_cwd() != planted


def test_launch_overlay_states_every_connection_key_and_unsets_what_the_target_drops():
    overlay = verify.launch_overlay({"env": {"OLD": "1", "ANTHROPIC_BASE_URL": "http://old"}, "apiKeyHelper": "h"},
                                    {"env": {"ANTHROPIC_BASE_URL": "http://new"}})
    env = overlay["env"]
    assert env["OLD"] == "" and env["ANTHROPIC_BASE_URL"] == "http://new"
    assert all(env[key] == "" for key in paths.CONNECTION_ENV_KEYS if key != "ANTHROPIC_BASE_URL")
    assert overlay["apiKeyHelper"] == ""
    assert verify.launch_overlay({}, {"env": {}, "apiKeyHelper": "cmd"})["apiKeyHelper"] == "cmd"
    assert "apiKeyHelper" not in verify.launch_overlay({}, {"env": {}})


def test_the_launch_stream_is_read_for_the_answering_models_and_the_result():
    stream = "\n".join([
        "not json", "[1]",
        json.dumps({"type": "assistant", "message": {"model": "m-b"}}),
        json.dumps({"type": "assistant", "message": {"model": "m-a"}}),
        json.dumps({"type": "result", "result": "OK", "is_error": False}),
    ])
    result, models = verify.parse_launch_stream(stream)
    assert result["result"] == "OK" and models == {"m-a", "m-b"}
    assert verify.parse_launch_stream("") == ({}, set())


def fake_runner(stdout="", returncode=0, raises=None, seen=None):
    def run(cmd, **kwargs):
        if seen is not None:
            seen.append((cmd, kwargs))
        if raises:
            raise raises
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="")
    return run


OK_STREAM = "\n".join([json.dumps({"type": "assistant", "message": {"model": "m1"}}),
                       json.dumps({"type": "result", "result": "OK", "is_error": False})])


def test_prove_launch_ok_and_its_overlay_file_is_owner_only_and_removed(tmp_path, monkeypatch):
    monkeypatch.setattr(verify.tempfile, "gettempdir", lambda: str(tmp_path))
    seen = []
    result = verify.prove_launch({"env": {"A": "b"}}, runner=fake_runner(OK_STREAM, seen=seen), lean=True)
    assert result["ok"] and result["models"] == ["m1"]
    cmd, kwargs = seen[0]
    settings = Path(cmd[cmd.index("--settings") + 1])
    assert not settings.exists()  # removed with its private directory
    assert verify.LEAN_FLAGS[0] in cmd and kwargs["stdin"] == subprocess.DEVNULL
    full = []
    verify.prove_launch({"env": {}}, runner=fake_runner(OK_STREAM, seen=full))
    assert verify.LEAN_FLAGS[0] not in full[0][0]


def test_prove_launch_failures_are_reported_and_the_key_is_redacted(tmp_path, monkeypatch):
    monkeypatch.setattr(verify.tempfile, "gettempdir", lambda: str(tmp_path))
    err = json.dumps({"type": "result", "result": f"401 bad key {KEY}", "is_error": True})
    result = verify.prove_launch({"env": {"ANTHROPIC_AUTH_TOKEN": KEY}}, runner=fake_runner(err, returncode=1))
    assert not result["ok"] and KEY not in json.dumps(result) and "<key>" in result["detail"]
    assert verify.prove_launch({"env": {}}, runner=fake_runner("", returncode=3))["detail"] == "exit 3"
    missing = verify.prove_launch({"env": {}}, runner=fake_runner(raises=FileNotFoundError()))
    assert missing["detail"] == "the claude command is not on PATH"
    slow = verify.prove_launch({"env": {}}, runner=fake_runner(raises=subprocess.TimeoutExpired("c", 1)))
    assert "no answer within" in slow["detail"]


# --- the search for a working path --------------------------------------------

def test_first_working_path_skips_failures_reports_classes_and_keeps_only_the_winner(home, tmp_path, gateway):
    good = gateway(body=MESSAGE)
    ladder = {
        "dead": {"base_url": "http://127.0.0.1:1", "model": "m", "auth": "env:NOKEY"},
        "good": {"base_url": good.url, "model": "m", "auth": "env:NOKEY"},
    }
    written, rows = [], []

    def session_out(path_id, env=None, **kwargs):
        file = tmp_path / f"{path_id}.json"
        file.write_text(json.dumps({"env": {"ANTHROPIC_BASE_URL": "http://x"}}))
        written.append(file)
        return {"file": str(file)}

    result = verify.first_working_path(["nope", "dead", "good"], env={}, prove=lambda payload, lean=False: {"ok": True, "detail": "fine"},
                                       report=rows.append, session_out=session_out, builtin=ladder)
    assert result["path"] == "good" and Path(result["file"]).exists()
    assert [r["path"] for r in rows] == ["nope", "dead", "good"]
    assert rows[0]["class"] == "cli" or rows[0]["class"] == "unavailable"
    assert rows[1]["class"] in ("unavailable", "transient") and rows[2]["ok"]


def test_a_failed_proof_leaves_no_payload_and_the_search_goes_on(home, tmp_path, gateway):
    g = gateway(body=MESSAGE)
    ladder = {"a": {"base_url": g.url, "model": "m", "auth": "env:K"}, "b": {"base_url": g.url, "model": "m", "auth": "env:K"}}
    files = []

    def session_out(path_id, env=None, **kwargs):
        file = tmp_path / f"{path_id}.json"
        file.write_text(json.dumps({"env": {}}))
        files.append(file)
        return {"file": str(file)}

    def prove(payload, lean=False):
        return {"ok": len(files) == 2, "detail": "Please run /login"}

    rows = []
    result = verify.first_working_path(["a", "b"], env={}, prove=prove, report=rows.append, session_out=session_out, builtin=ladder)
    assert result["path"] == "b" and not files[0].exists() and files[1].exists()
    assert rows[0]["class"] == "auth"


def test_confirm_full_demotes_a_candidate_whose_full_launch_fails(home, tmp_path, gateway):
    g = gateway(body=MESSAGE)
    ladder = {"a": {"base_url": g.url, "model": "m", "auth": "env:K"}}

    def session_out(path_id, env=None, **kwargs):
        file = tmp_path / "a.json"
        file.write_text(json.dumps({"env": {}}))
        return {"file": str(file)}

    rows = []
    prove = lambda payload, lean=False: {"ok": lean, "detail": "needs tools"}
    assert verify.first_working_path(["a"], env={}, prove=prove, report=rows.append, session_out=session_out,
                                     builtin=ladder, confirm_full=True) is None
    assert "lean turn answered, full launch failed" in rows[0]["detail"]
    assert not (tmp_path / "a.json").exists()


def test_a_payload_that_cannot_carry_the_key_is_a_config_class(home, tmp_path, gateway):
    g = gateway(body=MESSAGE)
    ladder = {"a": {"base_url": g.url, "model": "m", "auth": "env:K"}}

    def session_out(path_id, env=None, **kwargs):
        raise ValueError("K is not set")

    rows = []
    assert verify.first_working_path(["a"], env={}, session_out=session_out, report=rows.append, builtin=ladder) is None
    assert rows[0]["class"] == "config" and "not launchable" in rows[0]["detail"]


# --- pins found missing by a reviewer's survivors -----------------------------------

def test_the_redaction_threshold_is_eight_characters():
    assert verify.redacted({"detail": "x 12345678 y"}, "12345678")["detail"] == "x <key> y"
    assert verify.redacted({"detail": "x 1234567 y"}, "1234567")["detail"] == "x 1234567 y"


def test_the_probe_sequence_and_its_order_are_pinned(gateway):
    assert verify.PROBE_SUFFIXES == ("/v1/models", "/", "/health")
    g = gateway(status=200, body={})
    verify.reachable(g.url, suffixes=("/b", "/a"))
    assert g.requests[0]["path"] == "/b"  # tried in the order given: the first answer wins


def test_the_request_timeout_and_the_launch_constants_are_pinned(monkeypatch, tmp_path):
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps(MESSAGE).encode()

    def fake_urlopen(request, timeout=None):
        seen["timeout"] = timeout
        return Response()
    monkeypatch.setattr(verify.urllib.request, "urlopen", fake_urlopen)
    assert verify._post_messages("http://x", "m")["ok"] and seen["timeout"] == 30
    monkeypatch.setattr(verify.tempfile, "gettempdir", lambda: str(tmp_path))
    ran = []
    verify.prove_launch({"env": {}}, runner=fake_runner(OK_STREAM, seen=ran))
    assert ran[0][0][-1] == "Reply with the single word OK." and ran[0][1]["timeout"] == 180


def test_first_working_path_passes_the_safe_options_to_the_verification(home, tmp_path, gateway):
    g = gateway(body=MESSAGE)
    asked = []

    class Fake:
        def check_consumer(self, name, argv):
            asked.append((name, argv))
            return {}

        def get(self, name):
            return "k"
    ladder = {"v": {"base_url": g.url, "model": "m", "auth": "safe://NAME"}}

    def session_out(path_id, env=None, **kwargs):
        file = tmp_path / "v.json"
        file.write_text(json.dumps({"env": {}}))
        return {"file": str(file)}
    verify.first_working_path(["v"], env={}, prove=lambda payload, lean=False: {"ok": True, "detail": "fine"},
                              session_out=session_out, builtin=ladder, safe=Fake(), argv=["/x/ahabase", "llm", "key", "v"])
    assert asked and asked[0][0] == "NAME" and asked[0][1][0] == "/x/ahabase"


def test_a_bare_exit_code_is_the_check_failing_but_the_words_inside_other_text_are_not():
    assert verify.classify_failure("exit 2") == "cli" and verify.classify_failure("Exit -1") == "cli"
    assert verify.classify_failure("the probe printed exit 2 among other text") == "unavailable"
    assert verify.classify_failure("process exit 3 after the upstream said no") == "unavailable"


def test_one_mapping_from_a_verdict_to_its_class():
    assert verify.failure_class({"status": "definition", "detail": "Please run /login"}) == "config"
    assert verify.failure_class({"status": "auth-refused", "detail": "token has expired"}) == "config"
    assert verify.failure_class({"status": 500, "detail": "HTTP 429 from x"}) == "transient"
    assert verify.failure_class({"status": "unreachable", "detail": "Please run /login"}) == "auth"
    assert verify.failure_class({"status": "no-login", "detail": ""}) == "cli"


def test_the_search_reports_a_refused_credential_as_config_not_as_an_expired_login(home, tmp_path):
    class Refusing:
        def check_consumer(self, name, argv):
            from ahabase.safe import SafeError
            raise SafeError("not a bound consumer")

        def get(self, name):
            raise AssertionError("must not be read")
    ladder = {"v": {"base_url": "http://127.0.0.1:1", "model": "m", "auth": "safe://NAME"}}
    rows = []
    assert verify.first_working_path(["v"], env={}, report=rows.append, builtin=ladder, safe=Refusing(),
                                     argv=["x"], session_out=lambda *a, **k: {}) is None
    assert rows[0]["class"] == "config"


# --- a safe:// path is verified through the bound run (AHA-0026) ---------------------------

def test_a_safe_path_is_verified_with_the_token_from_the_bound_run(gateway, home):
    g = gateway(body=MESSAGE)
    ladder = {"v": {"base_url": g.url, "model": "m", "auth": "safe://VAULT"}}
    seen = []

    def runner(command, **kwargs):
        seen.append(command)
        return subprocess.CompletedProcess(command, 0, stdout=KEY + "\n", stderr="")
    result = verify.verify_path("v", env={}, builtin=ladder, executable="/m/helper", safe_executable="/a/ahabase", runner=runner)
    assert result["ok"] is True and seen[0][0] == os.path.abspath("/a/ahabase")
    assert KEY in json.dumps(g.requests[0]["headers"])
    assert KEY not in json.dumps(result)


def test_a_refused_bound_run_is_auth_refused_without_a_value(gateway, home):
    g = gateway(body=MESSAGE)
    ladder = {"v": {"base_url": g.url, "model": "m", "auth": "safe://VAULT"}}
    runner = lambda command, **kwargs: subprocess.CompletedProcess(command, 1, stdout="", stderr="not bound")
    result = verify.verify_path("v", env={}, builtin=ladder, executable="/m/helper", safe_executable="/a/ahabase", runner=runner)
    assert result["ok"] is False and result["status"] == "auth-refused"
    assert KEY not in json.dumps(result) and not g.requests


def test_an_env_path_ignores_the_helper_pair(gateway, home):
    g = gateway(body=MESSAGE)
    ladder = {"gw": {"base_url": g.url, "model": "m", "auth": "env:CANARY_KEY"}}
    boom = lambda *a, **k: (_ for _ in ()).throw(AssertionError("runner must not run for env paths"))
    result = verify.verify_path("gw", env={"CANARY_KEY": KEY}, builtin=ladder, executable="/m/helper",
                                safe_executable="/a/ahabase", runner=boom)
    assert result["ok"] is True


def test_switch_forwards_both_executables_to_the_verification(monkeypatch, home):
    from ahabase.llm import switch
    captured = {}

    def fake_verify(path_id, **kwargs):
        captured.update(kwargs)
        return {"ok": False, "status": "x", "detail": "stop here"}
    monkeypatch.setattr(switch, "verify_path", fake_verify)
    with pytest.raises(ValueError):
        switch.switch_path("v", confirm=True, executable="/m/helper", safe_executable="/a/ahabase", builtin={})
    assert captured["executable"] == "/m/helper" and captured["safe_executable"] == "/a/ahabase"
