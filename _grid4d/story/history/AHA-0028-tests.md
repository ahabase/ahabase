# AHA-0028-tests

> Test definition for AHA-0028 with one test per requirement.

## Design

Test requirements for AHA-0028. One test per requirement.

## Definition

```yaml
tests:
  - name: R1_loader_keeps_every_field
    description: The loader test for the optional fields passes.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/llm/test_paths.py -k "keeps_every_optional_field"'
    expect:
      exit_code: 0
  - name: R2_blueprint_ladder_paragraph_and_frozen_section
    description: The ladder paragraph exists and the frozen seam contract hashes to the quoted value.
    command: 'B=_grid4d/subepic/ahabase-llm/implementation/implementation-ahabase-llm-blueprint.md; grep -q "The provider ladder is instance data" $B && python3 -c "import hashlib,re,sys; t=open(sys.argv[1]).read(); m=re.search(r\"^## Seam contract \\(frozen\\)\\n\",t,re.M); r=t[m.end():]; n=re.search(r\"^## \",r,re.M); b=r[:n.start()].strip(chr(10))+chr(10); sys.exit(0 if (len(b.encode())==2256 and hashlib.sha1(b.encode()).hexdigest().startswith(\"1eba783728bc\")) else 1)" $B'
    expect:
      exit_code: 0
  - name: R3_graduation_criteria_direct_use
    description: Check 6 is Direct use, the confirmation by the Human is check 7, and the neighbouring idea counts seven checks.
    command: 'grep -q "^6. \*\*Direct use\*\*" _grid4d/idea/graduation-criteria.md && grep -q "^7. \*\*The Human.s confirmation\*\*" _grid4d/idea/graduation-criteria.md && grep -q "list seven checks" _grid4d/idea/idea-graduation-checks-include-every-epic-rule.md'
    expect:
      exit_code: 0
  - name: R4_ci_recorded
    description: The Notes record the green matrix run.
    command: 'grep -q "CI measured (R4): green" _grid4d/story/AHA-0028.md'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_loader_keeps_every_field | ✅ | 2026-11-08 |
| R2_blueprint_ladder_paragraph_and_frozen_section | ✅ | 2026-11-08 |
| R3_graduation_criteria_direct_use | ✅ | 2026-11-08 |
| R4_ci_recorded | ✅ | 2026-11-08 |

Run at 576fc911299f26b04a2ad123a59446e197b29d5d
## Related

- [AHA-0028](AHA-0028) - Parent story

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
