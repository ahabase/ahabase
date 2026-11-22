# AHA-0029-tests

> Test definition for AHA-0029 with one test per requirement.

## Design

Test requirements for AHA-0029. One test per requirement.

## Definition

```yaml
tests:
  - name: R1_gate_suite_and_baseline_red
    description: The containment gate suite passes (green over the built artifacts, the mutant family including the symlink and embedded-form mutants, the artifact-level absence test, the env negative test) and the Notes record the RED baseline.
    command: 'PYTHONPATH=$PWD/src ~/ahabase/ahabase/.venv/bin/python -m pytest -q tests/test_artifact_containment.py && grep -q "Measured (R1, baseline RED" _grid4d/story/AHA-0029.md && grep -q "internal-github-host" _grid4d/story/AHA-0029.md'
    expect:
      exit_code: 0
  - name: R2_scrubbed_population_gone
    description: No shipped file carries any of the five identifier literals (the retired id, the internal host, username, schema prefixes) - composed at runtime in the definition site and both suites, and the rebuilt artifacts scan 0 findings.
    command: '! grep -q "<account-id>" src/ahabase/safe.py src/ahabase/cli_safe.py src/ahabase/artifact_containment.py tests/test_safe.py tests/test_artifact_containment.py && ! grep -q "<enterprise-tool>" src/ahabase/artifact_containment.py tests/test_artifact_containment.py tests/test_safe.py README.md && ! grep -q "<work-user>" src/ahabase/artifact_containment.py tests/test_artifact_containment.py tests/test_safe.py && ! grep -q "<schema>_" src/ahabase/artifact_containment.py tests/test_artifact_containment.py && ! grep -q "<enterprise-project>" src/ahabase/artifact_containment.py && grep -q "0 findings" _grid4d/story/AHA-0029.md'
    expect:
      exit_code: 0
  - name: R3_consumer_readme_section
    description: The README carries the consumer install (TestPyPI extra-index line, the first commands) and the two environment keys as the ruled CI exception.
    command: 'grep -q "## Install (consumers)" README.md && grep -q "extra-index-url https://test.pypi.org/simple/ ahabase" README.md && grep -q "AHABASE_WORKSPACE" README.md && grep -q "AHABASE_CONFIG" README.md && grep -q "never the" README.md && grep -q "no removal story" README.md'
    expect:
      exit_code: 0
  - name: R4_pipeline_gate_in_release_path
    description: The dry-run pipeline exists, is executable, stands the gate before the upload, consumes the token only through the safe, and the Notes record the full end-to-end run (upload included).
    command: 'test -x scripts/testpypi_dryrun.sh && grep -q "containment gate" scripts/testpypi_dryrun.sh && grep -q "twine upload" scripts/testpypi_dryrun.sh && grep -q "safe run" scripts/testpypi_dryrun.sh && grep -q "Measured (R4, full" _grid4d/story/AHA-0029.md'
    expect:
      exit_code: 0
  - name: R5_ci_recorded
    description: The Notes record the green matrix run on the story branch.
    command: 'grep -q "CI measured (R5): green" _grid4d/story/AHA-0029.md'
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_gate_suite_and_baseline_red | ✅ | 2026-11-20 |
| R2_scrubbed_population_gone | ✅ | 2026-11-20 |
| R3_consumer_readme_section | ✅ | 2026-11-20 |
| R4_pipeline_gate_in_release_path | ✅ | 2026-11-20 |
| R5_ci_recorded | ✅ | 2026-11-20 |

Run at 11bca08bd3898a32e43838d4eaa0c6f287caa3e2
## Related

- [AHA-0029](AHA-0029) - Parent story
