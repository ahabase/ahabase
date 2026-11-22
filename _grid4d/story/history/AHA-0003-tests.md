# AHA-0003-tests

> Test definition for AHA-0003 with one test per requirement.

## Design

The package's pytest suite carries the contract on fictional values with the isolation of AHA-0002 (temporary workspace, manifest and HOME; a guard keyring backend). Every guard stands alone with an explicit exit, so a failing check cannot pass under `set -e`. Nothing of the instance is read or changed.

## Definition

```yaml
tests:
  - name: R1_safe_compare
    description: compare gives same/different against env, file and git remote; missing side and wrong source count exit 2; no value or fingerprint in the output
    command: |
      .venv/bin/python -m pytest -q tests/test_safe.py -k "compare"
      if ! grep -q "compare_digest" src/ahabase/cli_safe.py; then echo "no constant-time compare"; exit 1; fi
      if grep -q "hexdigest" src/ahabase/cli_safe.py; then echo "a fingerprint may be printed"; exit 1; fi
    expect:
      exit_code: 0
      timeout: 300
  - name: R2_run_position
    description: a malformed --env after a valid one is reported as argument 2, without its text
    command: |
      .venv/bin/python -m pytest -q tests/test_safe.py -k "right_position or argument"
    expect:
      exit_code: 0
      timeout: 300
  - name: R3_public_rule
    description: the identity states that the Epic's knowledge is written as public
    command: |
      if ! grep -q "Knowledge written as public" _grid4d/story/AHABASE.md; then echo "rule missing"; exit 1; fi
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file _grid4d/story/AHABASE.md
    expect:
      exit_code: 0
  - name: R_docs_compare
    description: blueprint rule, template, example and README describe compare; the whole suite passes; the instance has no safe manifest
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-blueprint.md
      if ! grep -q "Comparison without disclosure" "$f"; then echo "no rule"; exit 1; fi
      if ! grep -q "^ahabase safe compare" "$f"; then echo "no template line"; exit 1; fi
      if ! grep -q "safe compare jira-api" README.md; then echo "no README line"; exit 1; fi
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$f"
      .venv/bin/python -m pytest -q
      if [ -e ~/ahabase/_config/safe.json ]; then echo "instance manifest exists"; exit 1; fi
    expect:
      exit_code: 0
      timeout: 300
  - name: R4_model_gaps
    description: the safe blueprint names the five gaps and consumers by kind; the story notes the inventory correction
    command: |
      f=_grid4d/implementation/implementation-ahabase-safe-blueprint.md
      for s in "Processes without a login session" "Loss of the OS store" "Expiry is only seen when checked" "## Consumers by kind" "credential helper" "before the first token with a wide reach"; do
        if ! grep -q "$s" "$f"; then echo "missing: $s"; exit 1; fi
      done
      if ! grep -q "templated from configuration files" _grid4d/story/AHA-0003.md; then echo "no inventory note"; exit 1; fi
    expect:
      exit_code: 0
  - name: R5_safe_first
    description: the safe-first rule is in the identity; the idea exists with its sections and links the story
    command: |
      i=_grid4d/idea/safe-first-public-capability.md
      if ! grep -q "Safe first" _grid4d/story/AHABASE.md; then echo "no identity rule"; exit 1; fi
      for s in "## Human direction" "## Motivating scenario" "## The gap" "## The capability" "## Conditions before it is offered" "## Open questions" "## Promotion path" "\[AHA-0003\]"; do
        if ! grep -q "$s" "$i"; then echo "missing: $s"; exit 1; fi
      done
      ~/ahabase/evolucean/knowledge-usage-cli/.venv/bin/knowledge-usage verify-file "$i"
    expect:
      exit_code: 0
  - name: R6_links_point_inward
    description: current documents link only within the repository and name no closed-zone document, except the listed generator lines tied to their issues; rule and issue exist
    command: |
      if ! grep -q "Links point inward" _grid4d/story/AHABASE.md; then echo "no rule"; exit 1; fi
      if [ ! -f _grid4d/issue/open-zone-documents-link-into-the-closed-zone.md ]; then echo "no issue"; exit 1; fi
      python3 - <<'PY'
      import pathlib, re, sys
      root = pathlib.Path("_grid4d")
      names = {p.stem for p in root.rglob("*.md")}
      released = re.compile(r"^AHA-000[12][.-]")  # released stories keep their text
      # known generator exceptions, each tied to its issue - anything else fails
      known = {
          ("AHA-0003.md", "implementation-story-blueprint"): "open-zone-documents-link-into-the-closed-zone",  # exception entry
          ("AHA-0003-knowledge-map.md", "evolucean/ahabase-foundation-roadmap"): "knowledge-map-links-a-document-of-another-repository",  # exception entry
          ("AHA-0003-knowledge-map.md", "evolucean/ontology-trust-zone-blueprint"): "knowledge-map-links-a-document-of-another-repository",  # exception entry
      }
      pattern_line = "closed = re.compile("  # the one line of this test that carries the pattern
      closed = re.compile(r"\bontology-[a-z-]+-blueprint\b|\bEVOLUCEAN-[A-Z]|ahabase-package-architecture|foundation-roadmap")
      bad, seen = [], set()
      for p in sorted(root.rglob("*.md")):
          if released.search(p.name):
              continue
          for n, line in enumerate(p.read_text().splitlines(), 1):
              if p.name == "AHA-0003-tests.md" and (pattern_line in line or "# exception entry" in line):
                  continue
              hits = [t for t in re.findall(r"\]\(([^)#]+)\)", line)
                      if not t.startswith("http") and pathlib.Path(t).stem not in names]
              if closed.search(line) and not hits:
                  hits = ["(name in text)"]
              for t in hits:
                  key = next((k for k in known if k[0] == p.name and k[1] in line), None)
                  if key:
                      seen.add(key)
                  else:
                      bad.append(f"{p}:{n}: {t}")
      for k in known:
          print(f"known exception {k[0]} -> {k[1]} ({known[k]})" + ("" if k in seen else " - no longer present, remove it"))
      print("\n".join(bad) or "links point inward")
      sys.exit(1 if bad else 0)
      PY
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_safe_compare | ✅ | 2026-10-25 |
| R2_run_position | ✅ | 2026-10-25 |
| R3_public_rule | ✅ | 2026-10-25 |
| R_docs_compare | ✅ | 2026-10-25 |
| R4_model_gaps | ✅ | 2026-10-25 |
| R5_safe_first | ✅ | 2026-10-25 |
| R6_links_point_inward | ✅ | 2026-10-25 |

## Related

- [AHA-0003](AHA-0003) - Parent story
