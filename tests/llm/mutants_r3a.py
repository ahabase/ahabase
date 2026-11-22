import subprocess, sys, pathlib, shutil
PY = sys.argv[1]
ROOT = pathlib.Path('.')
P = ROOT/'src/ahabase/llm/paths.py'
D = ROOT/'src/ahabase/llm/discovery.py'
MUTANTS = [
 ('literal accepted (the legacy behaviour)', P, '    raise AuthError("the auth is a literal credential - refused")', '    return spec'),
 ('definitions never checked for literals', P, '    if auth_form(str(definition.get("auth", ""))) == "literal":', '    if False:'),
 ('safe reference resolved without the consumer check', P, '            service.check_consumer(name, command)\n', ''),
 ('named rescue order ignored', P, '    if named:\n        return [str(p) for p in named]', '    if False:\n        return [str(p) for p in named]'),
 ('settings key no longer outranks the process env', P, 'bedrock_val = (state[BEDROCK_FLAG] if BEDROCK_FLAG in state\n                   else os.environ.get(BEDROCK_FLAG, ""))', 'bedrock_val = os.environ.get(BEDROCK_FLAG, "") or state.get(BEDROCK_FLAG, "")'),
 ('evidence leaks the variable value', D, 'available, evidence = True, f"process env: {name}"', 'available, evidence = True, f"process env: {name}={merged.get(name)}"'),
 ('a blank credentials file proves the cloud chain', P, 'AWS_CREDENTIALS_PATH.is_file() and AWS_CREDENTIALS_PATH.read_text().strip()', 'AWS_CREDENTIALS_PATH.is_file()'),
 ('the macOS keychain leg dropped from the subscription login', P, '    if sys.platform == "darwin" and _keychain_login_present():', '    if False:'),
 ('a relative command is no longer made absolute', P, '[os.path.abspath(sys.argv[0]), *sys.argv[1:]]', '[sys.argv[0], *sys.argv[1:]]'),
 ('the deprecated clock is back', D, 'datetime.now(timezone.utc).replace(tzinfo=None).isoformat()', 'datetime.utcnow().isoformat()'),
 ('another machine\'s record read as this one\'s', D, '    entry = machines.get(machine or machine_id())', '    entry = next(iter(machines.values()), None)'),
]
red = 0
for name, file, old, new in MUTANTS:
    original = file.read_text()
    assert original.count(old) == 1, f'mutation target not unique/absent: {name}'
    file.write_text(original.replace(old, new))
    changed = file.read_text() != original
    proc = subprocess.run([PY, '-m', 'pytest', 'tests/llm', '-q', '-x', '--no-header'], capture_output=True, text=True)
    file.write_text(original)
    assert file.read_text() == original
    status = 'RED' if proc.returncode != 0 else 'SURVIVED'
    red += status == 'RED'
    print(f'{status:8} landed={changed} {name}')
print(f'{red}/{len(MUTANTS)} mutants red; originals restored')
sys.exit(0 if red == len(MUTANTS) else 1)
