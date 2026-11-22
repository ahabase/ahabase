"""Planted mutants for the verification family (AHA-0024 R3b).

Run from the repository root: .venv/bin/python tests/llm/mutants_r3b.py .venv/bin/python
Each mutant is applied, the tests must turn red, and the original is restored.
"""
import pathlib
import subprocess
import sys

PY = sys.argv[1]
V = pathlib.Path('src/ahabase/llm/verify.py')
MUTANTS = [
    ('auth no longer decided first', V, '    if any(marker in text for marker in AUTH_MARKERS):\n        return "auth"\n    if any(marker in text for marker in TRANSIENT_MARKERS) or TRANSIENT_STATUS.search(text):\n        return "transient"', '    if any(marker in text for marker in TRANSIENT_MARKERS) or TRANSIENT_STATUS.search(text):\n        return "transient"\n    if any(marker in text for marker in AUTH_MARKERS):\n        return "auth"'),
    ('the key is no longer redacted from an error body', V, '    def done(verdict: dict) -> dict:\n        return redacted(verdict, token)', '    def done(verdict: dict) -> dict:\n        return verdict'),
    ('a short secret is replaced (mangles ordinary text)', V, 'if secret and len(str(secret)) >= 8:', 'if secret:'),
    ('truncation read as incapability', V, '        if body.get("stop_reason") == "max_tokens":', '        if False:'),
    ('a status code inside a longer number counts as transient', V, 'TRANSIENT_STATUS = re.compile(r"\\b(429|500|502|503|504|529)\\b")', 'TRANSIENT_STATUS = re.compile(r"(429|500|502|503|504|529)")'),
    ('the family is not staggered', V, '        if index > 0 and stagger_seconds > 0:\n            sleep(stagger_seconds)', '        pass'),
    ('a failed proof leaves its payload behind', V, '            if not keep:\n                launch_file.unlink(missing_ok=True)', '            pass'),
    ('the full launch is not required when confirm_full is set', V, '            if proof["ok"] and confirm_full:', '            if False:'),
    ('a key helper path sends one header only', V, 'return HELPER_HEADERS if (definition or {}).get("key_helper") else TOKEN_HEADERS', 'return TOKEN_HEADERS'),
    ('probe_cwd trusts a directory others can write', V, '        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:', '        if info.st_uid != os.getuid():'),
    ('the tool probe set is ignored', V, '        require_tool_use = path_id in tool_probe_paths', '        require_tool_use = False'),
    ('an HTTP answer no longer proves reachability', V, '        except urllib.error.HTTPError as exc:\n            return True, exc.code', '        except urllib.error.HTTPError as exc:\n            continue'),
    ('the redaction threshold moves to nine', V, 'if secret and len(str(secret)) >= 8:', 'if secret and len(str(secret)) >= 9:'),
    ('the probe sequence is reversed', V, 'PROBE_SUFFIXES = ("/v1/models", "/", "/health")', 'PROBE_SUFFIXES = ("/health", "/", "/v1/models")'),
    ('the search drops the safe option from the verification', V, '("builtin", "variants_file", "tool_probe_paths", "argv", "safe")', '("builtin", "variants_file", "tool_probe_paths", "argv")'),
    ('the launch prompt is reworded', V, 'PROVE_PROMPT = "Reply with the single word OK."', 'PROVE_PROMPT = "Say OK."'),
    ('the request timeout moves to 29', V, 'VERIFY_TIMEOUT = 30', 'VERIFY_TIMEOUT = 29'),
    ('a bare exit code is searched for inside other text', V, 'CLI_EXIT.fullmatch(text.strip())', 'CLI_EXIT.search(text.strip())'),
    ('a refused credential is classified by its text again', V, '    if verdict.get("status") in ("definition", "auth-refused"):', '    if verdict.get("status") in ("definition",):'),
]
red = 0
for name, file, old, new in MUTANTS:
    original = file.read_text()
    assert original.count(old) == 1, f'mutation target not unique or absent: {name}'
    file.write_text(original.replace(old, new))
    proc = subprocess.run([PY, '-m', 'pytest', 'tests/llm', '-q', '-x', '--no-header'], capture_output=True, text=True)
    file.write_text(original)
    assert file.read_text() == original
    status = 'RED' if proc.returncode != 0 else 'SURVIVED'
    red += status == 'RED'
    print(f'{status:8} {name}')
print(f'{red}/{len(MUTANTS)} mutants red; originals restored')
sys.exit(0 if red == len(MUTANTS) else 1)
