"""Planted mutants for the switch, the payload and the key helper (AHA-0024 R3c).

Run from the repository root: .venv/bin/python tests/llm/mutants_r3c.py .venv/bin/python
Each mutant is applied, the tests must turn red, and the original is restored.
"""
import pathlib
import subprocess
import sys

PY = sys.argv[1]
W = pathlib.Path('src/ahabase/llm/switch.py')
S = pathlib.Path('src/ahabase/llm/session.py')
MUTANTS = [
    ('the switch writes the resolved token (the legacy behaviour)', W, '        env_section["ANTHROPIC_AUTH_TOKEN"] = ""\n        env_section["ANTHROPIC_API_KEY"] = ""\n        if target_model:', '        env_section["ANTHROPIC_AUTH_TOKEN"] = (env or {}).get("SWITCH_KEY", "") or (env or {}).get("CANARY_KEY", "")\n        env_section["ANTHROPIC_API_KEY"] = ""\n        if target_model:'),
    ('the switch takes no backup', W, '    shutil.copy(settings_path, backup)', '    pass'),
    ('the switch ignores live sessions elsewhere', W, '    if foreign and not force:', '    if False:'),
    ('a failed proof leaves its backup', W, '            backup.unlink(missing_ok=True)  # nothing was written', '            pass'),
    ('a legacy literal is restored without consent', W, '    if _holds_literal(backup_config) and not allow_literal:', '    if False:'),
    ('a restore takes no pre-restore backup', W, '    shutil.copy(settings_path, pre_restore)', '    pass'),
    ('a restore keeps a helper the backup did not have', W, '    else:\n        config.pop("apiKeyHelper", None)', '    else:\n        pass'),
    ('the atomic write leaves its temp file on a crash', W, '            os.unlink(temp_name)', '            pass'),
    ('the atomic write drops the existing mode', W, '            os.chmod(temp_name, mode)', '            pass'),
    ('the payload carries the resolved value', S, '    payload = {**spec["settings"], "env": dict(spec["env"])}', '    payload = {**spec["settings"], "env": {**spec["env"], "ANTHROPIC_AUTH_TOKEN": env.get(spec["auth_env"] or "", "")}}'),
    ('the payload file is world-readable', S, '    descriptor = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)\n    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:\n        handle.write(text)\n    try:\n        path.chmod(0o600)\n    except OSError:\n        pass', '    path.write_text(text, encoding="utf-8")'),
    ('the key helper bypasses the safe\'s bound run', S, '        command = [exe, "safe", "run", "--env"', '        command = [exe, "safe", "get", "--env"'),
    ('the inner step emits without an injected value', S, '        if not value:\n            raise ValueError("no key was injected', '        if False:\n            raise ValueError("no key was injected'),
    ('a backup that does not parse is restored', W, '        raise ValueError(f"the backup does not parse, not restoring: {error.__class__.__name__}") from None', '        backup_config = {}'),
    ('the atomic write does not flush to disk', W, '            os.fsync(handle.fileno())', '            pass'),
    ('a helper next to a literal exempts the literal from the gate (the reviewer-found hole)', W, '    return bool(env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY"))', '    return bool(env.get("ANTHROPIC_AUTH_TOKEN") or env.get("ANTHROPIC_API_KEY")) and not config.get("apiKeyHelper")'),
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
