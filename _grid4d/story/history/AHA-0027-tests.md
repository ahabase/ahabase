# AHA-0027-tests

> Test definition for AHA-0027 with one test per requirement.

## Design

Test requirements for AHA-0027. One test per requirement.

## Definition

```yaml
tests:
  - name: R1_door_names_itself
    description: The door tests for self-naming and the payload helper pass.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/llm/test_door.py -k "names_itself or payload_helper"'
    expect:
      exit_code: 0
  - name: R2_session_launch
    description: The session-launch tests pass.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/llm/test_door.py -k "session_launch"'
    expect:
      exit_code: 0
  - name: R3_frozen_seam_contract_unchanged
    description: The frozen seam contract section of the blueprint still hashes to the value quoted in the flip story (2256 bytes, sha1 prefix 1eba783728bc).
    command: 'python3 -c "import hashlib,re,sys; t=open(\"_grid4d/subepic/ahabase-llm/implementation/implementation-ahabase-llm-blueprint.md\").read(); m=re.search(r\"^## Seam contract \\(frozen\\)\\n\",t,re.M); r=t[m.end():]; n=re.search(r\"^## \",r,re.M); b=r[:n.start()].strip(chr(10))+chr(10); h=hashlib.sha1(b.encode()).hexdigest(); sys.exit(0 if (len(b.encode())==2256 and h.startswith(\"1eba783728bc\")) else 1)"'
    expect:
      exit_code: 0
  - name: R3_blueprint_and_ci
    description: The blueprint paragraph exists and the Notes record the green matrix run.
    command: 'grep -q "The door as its own caller (direct use)" _grid4d/subepic/ahabase-llm/implementation/implementation-ahabase-llm-blueprint.md && grep -q "CI measured (R3): green" _grid4d/story/AHA-0027.md'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_door_names_itself | ✅ | 2026-11-08 |
| R2_session_launch | ✅ | 2026-11-08 |
| R3_blueprint_and_ci | ✅ | 2026-11-08 |
| R3_frozen_seam_contract_unchanged | ✅ | 2026-11-08 |

Run at 4c75e42281c498d3fe94d291b2d870bf2ae99f8d
## Related

- [AHA-0027](AHA-0027) - Parent story

---
## _behavior

enforced_by:
  - pattern: gof-behavioral-template-method
    how: tests skeleton minted per story (R-per-requirement rows)
  - pattern: gof-behavioral-interpreter
    how: _behavior validation plus the stop-hook coverage matcher reading Execution rows

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
