"""Verification: proof that a path answers, and the class of a failure.

Capability: llm-paths

Implements: implementation-ahabase-llm-blueprint

A path is verified with a real minimal request (a few tokens), or, for the
tool's own routes, by the presence of its login or credential chain. A failure
carries a class that says what to do about it: ``auth``, ``transient``,
``cli`` or ``unavailable`` (``config`` when the definition itself is wrong).
Auth is tested first, so an expired login never reads as a dead service.

Nothing here prints or persists a credential value; every verdict is redacted
against the key it was obtained with before it is returned.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from . import paths as res

VERIFY_TIMEOUT = 30  # seconds for the preflight messages request
PROVE_TIMEOUT = 180  # seconds for the one-turn launch proof
PROVE_PROMPT = "Reply with the single word OK."
PROBE_SUFFIXES = ("/v1/models", "/", "/health")

# The headers the tool sends a key in: a key helper value goes out as x-api-key
# AND Bearer, an injected token as Bearer only. The check sends exactly what
# the written settings will send, so a gateway that refuses Bearer fails the
# check, not the first real request.
HELPER_HEADERS = ("x-api-key", "bearer")
TOKEN_HEADERS = ("bearer",)

# The forced tool-choice probe: a trivial tool with no required input. The
# forced choice makes the model call it instead of hoping the prompt earns one.
_TOOL_PROBE_DEFINITION = {
    "name": "verify_tool_probe",
    "description": "Call this tool to confirm tool use works.",
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

# The lean launch: no default system prompt, no tools, no MCP servers - the same
# connection and settings at a small fraction of the cost. A switch proves the
# full launch.
LEAN_FLAGS = ("--system-prompt", "Answer in one word.", "--tools", "", "--strict-mcp-config")

# Failure classes from the tool's own error text. Phrases, never a bare "sso":
# it is a substring of "associated" and "processor".
AUTH_MARKERS = ("please run /login", "oauth token has expired",
                "could not load aws credentials", "could not load credentials",
                "expiredtoken", "security token", "token has expired", "aws sso",
                "sso session", "sso token", "sso login",
                "unrecognizedclient", "invalidclienttokenid", "refresh your aws")
TRANSIENT_MARKERS = ("throttl", "too many requests", "rate limit", "limit exhausted", "quota",
                     "timeout", "timed out", "no answer within", "serviceunavailable",
                     "internalserver", "overloaded")
# the check's own failure shapes - never evidence about the connection
CLI_MARKERS = ("the claude command is not on path", "unknown option", "error: unknown",
               "unrecognized option")
CLI_EXIT = re.compile(r"exit -?\d+")
# HTTP status codes as whole numbers only - "1500 tokens" is not a 500
TRANSIENT_STATUS = re.compile(r"\b(429|500|502|503|504|529)\b")
# what the Human can do about each class
FAILURE_HINTS = {
    "auth": "the login expired - renew it (the provider's login command, or claude login) and retry",
    "transient": "a limit, throttling or a timeout - it may come back by itself",
    "cli": "the check itself could not run - is the claude command installed and current?",
    "unavailable": "the endpoint refused - the model or the service is gone or denied",
    "config": "the connection is not set up in this environment - export its key, fix its key helper or its definition",
}


def redacted(verdict: dict, *secrets) -> dict:
    """``verdict`` with every secret replaced in its detail.

    Capability: llm-paths

    An endpoint may echo the request's key in an error body; the detail is
    printed and stored, so the literal never survives into it. A secret shorter
    than eight characters is not replaced (it would mangle ordinary text).
    """
    detail = str(verdict.get("detail", ""))
    for secret in secrets:
        if secret and len(str(secret)) >= 8:
            detail = detail.replace(str(secret), "<key>")
    return {**verdict, "detail": detail}


def key_headers(definition: Optional[dict]) -> tuple:
    """The headers a path's settings deliver its key in.

    Capability: llm-paths
    """
    return HELPER_HEADERS if (definition or {}).get("key_helper") else TOKEN_HEADERS


def _post_messages(base_url: str, model: str, token: Optional[str] = None,
                   require_tool_use: bool = False,
                   headers: tuple = HELPER_HEADERS) -> dict:
    """The shared minimal messages probe: ``{ok, status, detail}``.

    Capability: llm-paths

    HTTP 200 with a message body is the only ``ok`` for a plain probe.
    ``require_tool_use`` swaps it for a forced tool-choice request: ``ok`` only
    when the response carries a ``tool_use`` block; a model that ignores the
    choice reports ``no-tool-use``, and one cut off by the token budget reports
    ``inconclusive-truncated`` (truncation is not evidence of incapability).
    The verdict is redacted against ``token`` before it is returned.
    """
    url = base_url.rstrip("/") + "/v1/messages"
    body_payload = {
        "model": model,
        # Reasoning models think before calling a tool; a small budget cuts that
        # off mid-thought and reads as a false no-tool-use.
        "max_tokens": 1000 if require_tool_use else 8,
        "messages": [{"role": "user", "content":
                      "call the verify_tool_probe tool" if require_tool_use else "ping"}],
    }
    if require_tool_use:
        body_payload["tools"] = [_TOOL_PROBE_DEFINITION]
        body_payload["tool_choice"] = {"type": "tool", "name": "verify_tool_probe"}
    request = urllib.request.Request(url, data=json.dumps(body_payload).encode(), method="POST")
    request.add_header("content-type", "application/json")
    if token and "x-api-key" in headers:
        request.add_header("x-api-key", token)
    if token and "bearer" in headers:
        request.add_header("authorization", f"Bearer {token}")
    request.add_header("anthropic-version", "2023-06-01")

    def done(verdict: dict) -> dict:
        return redacted(verdict, token)

    try:
        with urllib.request.urlopen(request, timeout=VERIFY_TIMEOUT) as response:
            body = json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        detail = f"HTTP {exc.code} from {url}"
        try:
            detail += f": {exc.read().decode()[:200]}"
        except Exception:  # noqa: BLE001 - an unreadable error body is not a failure of the check
            pass
        return done({"ok": False, "status": exc.code, "detail": detail})
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return done({"ok": False, "status": "unreachable", "detail": f"{url}: {exc}"})
    except json.JSONDecodeError:
        return done({"ok": False, "status": "bad-response", "detail": "non-JSON body"})

    used = body.get("model", model)
    if require_tool_use:
        blocks = body.get("content") or []
        if any(isinstance(b, dict) and b.get("type") == "tool_use" for b in blocks):
            return done({"ok": True, "status": 200,
                         "detail": f"tool_use verified via {url} (model {used})"})
        if body.get("stop_reason") == "max_tokens":
            return done({"ok": False, "status": "inconclusive-truncated",
                         "detail": f"model {used} hit max_tokens before a tool_use block "
                                   "appeared - raise the probe's token budget and retry, "
                                   "this is not a capability verdict"})
        return done({"ok": False, "status": "no-tool-use",
                     "detail": f"model {used} responded without a tool_use block: {str(body)[:160]}"})
    if body.get("type") == "message" or body.get("content"):
        return done({"ok": True, "status": 200, "detail": f"verified via {url} (model {used})"})
    return done({"ok": False, "status": "bad-response", "detail": f"unexpected body: {str(body)[:120]}"})


def verify_path(path_id: str, base_url: Optional[str] = None, model: Optional[str] = None,
                env: Optional[dict] = None, require_tool_use: Optional[bool] = None, *,
                builtin: Optional[dict] = None, variants_file: Optional[Path] = None,
                tool_probe_paths=frozenset(), argv: Optional[list] = None,
                safe=None, executable: Optional[str] = None,
                safe_executable: Optional[str] = None, runner=subprocess.run) -> dict:
    """Preflight a path with a real minimal request: ``{ok, status, detail}``.

    Capability: llm-paths

    The request is tiny (``max_tokens=8``) and must return HTTP 200 with a
    message body. The subscription route verifies by its login and the cloud
    route by its credential chain (no request). A path in ``tool_probe_paths``
    defaults to the forced tool-choice probe; ``require_tool_use`` overrides it
    either way. A ``pin_model`` the definition cannot honour fails with status
    ``definition`` before any request. A credential that cannot be resolved
    (a literal, or a reference the running command may not read) fails with
    status ``auth-refused`` and a message that never holds a value. A ``safe://``
    key is obtained through the safe's bound run when the caller names its own
    helper (``executable`` the bound helper, ``safe_executable`` the runner); without
    ``executable`` the released in-process check with ``argv`` and ``safe`` stays.
    """
    definitions = res.known_paths(builtin, variants_file)
    definition = definitions.get(path_id)
    if base_url is None and definition is None:
        return {"ok": False, "status": "unknown-path", "detail": f"unknown path {path_id!r}"}
    pin_problem = res.pin_error(path_id, definition)
    if pin_problem:
        return {"ok": False, "status": "definition", "detail": pin_problem}
    auth_spec = (definition or {}).get("auth", "")
    if auth_spec == "oauth" and base_url is None:
        source = res.subscription_login_source()
        if source:
            return {"ok": True, "status": "login",
                    "detail": f"subscription login present ({source})"}
        return {"ok": False, "status": "no-login",
                "detail": "no subscription login - run 'claude login' in a terminal and retry"}
    if auth_spec == "aws-credentials" and base_url is None:
        source = res.bedrock_credentials_source(env)
        if source:
            return {"ok": True, "status": "credentials",
                    "detail": f"cloud credentials present ({source})"}
        return {"ok": False, "status": "no-credentials",
                "detail": "no cloud credentials on the chain - sign in with the provider's "
                          "login command (or export its access key) and retry"}
    base_url = base_url or (definition or {}).get("base_url", "")
    model = model or (definition or {}).get("model", "")
    try:
        if (executable is not None and definition and not definition.get("key_helper")
                and res.auth_form(str(definition.get("auth", ""))) == "safe"):
            from .session import key_value  # imported late: the session module follows
            token = key_value(path_id, env=env, builtin=builtin, variants_file=variants_file,
                              executable=executable, safe_executable=safe_executable, runner=runner)
        else:
            token = res.resolve_key(definition, env, argv=argv, safe=safe) if definition else None
    except (res.AuthError, ValueError) as error:
        return {"ok": False, "status": "auth-refused", "detail": str(error)}
    if require_tool_use is None:
        require_tool_use = path_id in tool_probe_paths
    verdict = _post_messages(base_url, model, token, require_tool_use=require_tool_use,
                             headers=key_headers(definition))
    if verdict["ok"] and not token and auth_spec.startswith("env:"):
        # the endpoint answered WITHOUT a key; a session cannot be launched until
        # the variable is set - a note, not a gate (a gateway may run open)
        verdict = {**verdict, "detail": verdict["detail"] + f" - no key sent: "
                   f"{auth_spec[4:]} is not set, a session payload will refuse"}
    return redacted(verdict, token)


def verify_path_family(path_ids: list, stagger_seconds: float = 3.0,
                       env: Optional[dict] = None, sleep=time.sleep, **options) -> list:
    """Verify several paths live, one at a time, with a mandatory delay.

    Capability: llm-paths

    Provider credits-per-minute are per provider, so firing several real
    preflight requests in one burst risks tripping a limit a single verify
    never would: each path after the first sleeps ``stagger_seconds`` first
    (the sleep is injectable so tests run instantly). One row per input, in
    order; a failure on one path never skips the rest. ``options`` pass through
    to :func:`verify_path`.
    """
    rows: list = []
    for index, path_id in enumerate(path_ids):
        if index > 0 and stagger_seconds > 0:
            sleep(stagger_seconds)
        rows.append({"path": path_id, **verify_path(path_id, env=env, **options)})
    return rows


def reachable(base_url: str, suffixes=PROBE_SUFFIXES, timeout: float = 5) -> tuple:
    """Whether an endpoint answers at all, without a token: ``(reachable, status)``.

    Capability: llm-paths

    Any HTTP answer (including 401 and 404) proves the endpoint is reachable;
    a full model probe is :func:`verify_path`'s job. Cheap suffixes are tried
    in the given order; the caller supplies the sequence (a slow health route
    belongs last). A silent endpoint moves on to the next suffix.
    """
    base = base_url.rstrip("/")
    for suffix in suffixes:
        try:
            urllib.request.urlopen(urllib.request.Request(base + suffix, method="GET"), timeout=timeout)
            return True, 200
        except urllib.error.HTTPError as exc:
            return True, exc.code
        except (urllib.error.URLError, TimeoutError, OSError):
            continue
    return False, None


def probe_cwd() -> Path:
    """The one working directory every launch proof runs in.

    Capability: llm-paths

    The tool records a project folder per working directory, so one stable
    private directory keeps it to one. Anything but an owned, owner-only
    directory at that path (a planted file, a symlink, a directory others can
    write, one that another user owns) gets a fresh private directory instead.
    Ownership and mode are checked where the platform has them (POSIX).
    """
    work = Path(tempfile.gettempdir()) / "ahabase-llm-prove"
    try:
        work.mkdir(mode=0o700, exist_ok=True)
    except FileExistsError:
        return Path(tempfile.mkdtemp(prefix="ahabase-llm-prove-"))
    if work.is_symlink() or not work.is_dir():
        return Path(tempfile.mkdtemp(prefix="ahabase-llm-prove-"))
    if hasattr(os, "getuid"):
        info = work.lstat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            return Path(tempfile.mkdtemp(prefix="ahabase-llm-prove-"))
    return work


def launch_overlay(current: dict, target: dict) -> dict:
    """The ``--settings`` overlay that turns ``current`` into ``target`` for one launch.

    Capability: llm-paths

    ``--settings`` merges per key over the machine settings, so a key the target
    drops is sent as an empty string (the tool's unset). Every connection key is
    stated, so neither the machine settings nor the shell's exports decide.
    """
    env_now, env_new = current.get("env") or {}, target.get("env") or {}
    env = {key: "" for key in env_now if key not in env_new}
    env.update({key: "" for key in res.CONNECTION_ENV_KEYS if key not in env_new})
    env.update(env_new)
    overlay = {"env": env}
    if target.get("apiKeyHelper"):
        overlay["apiKeyHelper"] = target["apiKeyHelper"]
    elif current.get("apiKeyHelper"):
        overlay["apiKeyHelper"] = ""
    return overlay


def parse_launch_stream(stream: str) -> tuple:
    """``(the result event, the models that answered)`` from the tool's stream-json.

    Capability: llm-paths

    The configured model name can be a router alias that picks a model per
    request, so the answering model is read from each assistant message, never
    from the configuration.
    """
    result: dict = {}
    answered: set = set()
    for line in stream.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "assistant":
            model = (event.get("message") or {}).get("model")
            if model:
                answered.add(str(model))
        elif event.get("type") == "result":
            result = event
    return result, answered


def prove_launch(overlay: dict, runner=subprocess.run, lean: bool = False) -> dict:
    """Launch the tool for one turn through ``overlay``; ``ok`` only when it answers.

    Capability: llm-paths

    The endpoint check proves the gateway answers; this proves the tool itself
    reaches a model with the settings about to be written. The overlay file is
    owner-only in a private directory and removed afterwards; no key value is
    printed. Returns ``{ok, detail, models}``.
    """
    # the resolved path finds a Windows command shim; an absent command fails at the launch
    command = shutil.which("claude") or "claude"
    with tempfile.TemporaryDirectory(prefix="llm-prove-") as work:
        try:
            os.chmod(work, 0o700)
        except OSError:
            pass
        overlay_file = Path(work) / "settings.json"
        overlay_file.write_text(json.dumps(overlay))
        try:
            overlay_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
        try:
            proc = runner([command, "-p", "--settings", str(overlay_file),
                           "--output-format", "stream-json", "--verbose",
                           *(LEAN_FLAGS if lean else ()), PROVE_PROMPT],
                          cwd=str(probe_cwd()), capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, timeout=PROVE_TIMEOUT)
        except FileNotFoundError:
            return {"ok": False, "detail": "the claude command is not on PATH", "models": []}
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": f"no answer within {PROVE_TIMEOUT}s", "models": []}
    body, answered = parse_launch_stream(proc.stdout or "")
    models = sorted(answered)
    if proc.returncode == 0 and not body.get("is_error") and body.get("result"):
        return {"ok": True, "detail": f"the tool answered (model {', '.join(models) or '?'})",
                "models": models}
    reason = str(body.get("result") or "").strip() or f"exit {proc.returncode}"
    env = overlay.get("env") or {}
    return redacted({"ok": False, "detail": reason[:200], "models": models},
                    env.get("ANTHROPIC_AUTH_TOKEN"), env.get("ANTHROPIC_API_KEY"))


def classify_failure(detail: str) -> str:
    """``auth``, ``transient``, ``cli`` or ``unavailable`` for a failed check's detail.

    Capability: llm-paths

    Tells the Human WHY a connection does not answer. Auth is tested first: an
    expired login must never read as a dead service. ``cli`` is only the
    check's own failure shapes (the command missing, a bare "exit N", an
    unknown option, an empty detail); anything else that is neither auth nor
    transient is ``unavailable``.
    """
    text = (detail or "").lower()
    if any(marker in text for marker in AUTH_MARKERS):
        return "auth"
    if any(marker in text for marker in TRANSIENT_MARKERS) or TRANSIENT_STATUS.search(text):
        return "transient"
    if not text.strip() or any(marker in text for marker in CLI_MARKERS) \
            or CLI_EXIT.fullmatch(text.strip()):
        return "cli"
    return "unavailable"


def failure_class(verdict: dict) -> str:
    """The class of a failed verdict: ``config`` when the definition or the credential access is wrong.

    Capability: llm-paths

    A definition the tool cannot honour, or a credential that this command may not read, is the
    Human's configuration to fix (the hint names the fix); anything else is classified by the text
    of the failure, auth first. Every door that reports a class uses this one mapping.
    """
    if verdict.get("status") in ("definition", "auth-refused"):
        return "config"
    return classify_failure(str(verdict.get("detail", "")))


def first_working_path(candidates: list, env: Optional[dict] = None, prove=None, report=None,
                       confirm_full: bool = False, *, session_out: Optional[Callable] = None,
                       **options) -> Optional[dict]:
    """The first candidate whose endpoint answers AND through which the tool answers.

    Capability: llm-paths

    Each candidate is checked like a switch (the endpoint check, then one tool
    turn through the session payload); the machine settings are never touched.
    ``report`` gets one ``{path, ok, detail, class}`` row per attempt. The turn
    is the lean launch; ``confirm_full`` proves the chosen candidate once more
    with the full launch before it is returned, and a candidate failing that
    proof is reported and the search goes on. Returns ``{path, file, proof}``
    for the first that works, None when none does.

    ``session_out`` writes the session payload (default: the session module's
    writer); ``options`` pass through to :func:`verify_path` and the writer.
    """
    prove = prove or prove_launch
    if session_out is None:
        from .session import session_env_out as session_out  # imported late: the session module follows
    for path_id in candidates:
        verdict = verify_path(path_id, env=env, **{k: v for k, v in options.items()
                                                   if k in ("builtin", "variants_file", "tool_probe_paths", "argv", "safe",
                                                                 "executable", "safe_executable")})
        if not verdict["ok"]:
            if report:
                cls = failure_class(verdict)
                report({"path": path_id, "ok": False, "detail": verdict["detail"], "class": cls})
            continue
        try:
            written = session_out(path_id, env=env, **{k: v for k, v in options.items()
                                                       if k in ("epic", "builtin", "variants_file", "env_overrides")})
        except ValueError as exc:
            if report:
                report({"path": path_id, "ok": False,
                        "detail": f"endpoint answers, but not launchable: {exc}",
                        "class": "config"})
            continue
        launch_file = Path(written["file"])
        keep = False
        try:
            payload = launch_overlay({"env": {}}, json.loads(launch_file.read_text()))
            launch_file.write_text(json.dumps(payload, indent=2))
            proof = prove(payload, lean=True)
            if proof["ok"] and confirm_full:
                full = prove(payload)
                if not full["ok"]:
                    proof = {**full, "detail": f"lean turn answered, full launch failed: {full['detail']}"}
            if report:
                report({"path": path_id, "ok": proof["ok"], "detail": proof["detail"],
                        "class": None if proof["ok"] else classify_failure(proof["detail"])})
            if proof["ok"]:
                keep = True
                return {"path": path_id, "file": written["file"], "proof": proof}
        finally:
            # a failed or raising proof never leaves the file (it may carry a key) behind
            if not keep:
                launch_file.unlink(missing_ok=True)
    return None
