# ahabase Release Containment Blueprint

> The standing gate over the built artifacts: the wheel and sdist carry only Users-zone bytes — allowlist, canonicality, redaction — demonstrated RED at the baseline before it is trusted to stand.

**Implements:** [ontology-trust-zone-blueprint](ontology-trust-zone-blueprint) - the Users-zone channel guard (zone 1)
**Story:** [AHA-0029](AHA-0029)
**Code:** artifact_containment

## Overview

The package channel is how knowledge leaves the repository for anyone holding the package (zone 1, Users). The trust-zone blueprint guards the channel with a channel grant; this blueprint is the machine check behind that grant: every artifact built for the channel is scanned — the exact built wheel and sdist, never a reconstruction — and a finding stops the release. The gate is the MVP ruling's row-4 brick (EVOLUCEAN-0555): it lands first, RED at the pre-scrub baseline naming the real leaks, and every later package change passes through it.

## Rules

1. **The exact built artifact is the substrate** — the scan runs over the wheel and sdist produced by the project's own build (`build_artifacts`), never over a directory listing or a zip reconstruction; what is checked is what ships.
2. **Allowlist: nothing outside the pinned list ships** — the wheel carries exactly the package directory (`ahabase/**`) plus its dist-info; the sdist carries exactly the pyproject include list plus the generated `PKG-INFO`. A member that is not a plain relative path (absolute, `..`) is a finding, and so is any non-regular member (a symlink, a link, a device) wherever it sits — reported by kind, its name never its target (review F2, AHA-0029).
3. **Canonicality: one canonical copy per module** — every repo-file member of an artifact is byte-identical to its repository source. The pin is the byte comparison, so the evolucean-side copy can exist in parallel (its deletion is a parallel story, not a prerequisite) while the artifact still ships exactly the canonical bytes.
4. **Redaction: a class, not a literal list** — the pattern set names kinds of corporate identifiers (a numeric account id beside a credential host, any e-mail address, the internal GitHub host, the internal directory and schema names); a new instance of a known kind is caught, not only the strings measured once. Internal names match as substrings, so an embedded form (`name_suffix`) cannot ride a word boundary (review F_d, AHA-0029). Beside the classes stands one tombstone — the retired account id, held as a sha256 digest and matched over every 8-digit window of every digit run, so no byte of the tree carries the value itself (review F1). The pattern set's own vocabulary is composed at runtime, never written as a literal: the definition site and its suite ship under the arm with no exemptions, and an artifact-level test asserts no member of either artifact carries an identifier byte. The set is fixed and named; extending it is a story decision.
5. **A guard, not a proof** — the redaction arm proves these patterns are absent, not that no secret exists (the public-release dossier's non-overclaim); the claim in every document says "no match of the defined pattern set".
6. **A violation reports where, never what** — the report names the arm, artifact, member, line and pattern; the matched text is never echoed into a log.
7. **The arm guards corporate identifiers, never environment-variable documentation** — a README that documents `env:NAME` (the Human's option A: a CI/transitional exception, never a default) stays green; the negative test holds this line.
8. **RED before green** — the scan was demonstrated RED at the pre-scrub baseline (the two docstrings in the wheel; those plus the test file's occurrences in the sdist), and the mutant family (the known string reintroduced; a different instance of the class; the retired id in every form — bare, letter-embedded, digit-embedded; an embedded internal name; a rogue member; a modified byte; a symlink member in either archive) keeps the arms from going blind.

## Structure

`src/ahabase/artifact_containment.py` — `CORPORATE_IDENTIFIER_PATTERNS` (the fixed set, its literals composed at runtime), `RETIRED_ID_SHA256` (the tombstone digest), `Violation` (the report line), `build_artifacts` (the substrate), `scan_wheel` / `scan_sdist` (the arms, non-regular members included), `scan_release` (the gate: both artifacts, all arms). `tests/test_artifact_containment.py` — the standing suite: green over the built artifacts, the mutant family over copies (fixtures composed at runtime), the artifact-level absence test, the env-example negative test. The TestPyPI dry-run pipeline (AHA-0029 R4) imports `scan_release` and stops before upload on any finding — the gate stands in the release path, not beside it.

## Known limits

- **A guard over the fixed pattern set** — identifiers of a kind not yet named (a new internal hostname form, a different secret shape) pass until the set grows; the set's history is the story trail.
- **The tombstone digest is not secrecy** — an 8-digit id is brute-forceable; the digest keeps the literal out of the tree and the artifacts, it does not make the id secret.
- **The dist-info and PKG-INFO are exempt from canonicality** (generated metadata) and scanned by redaction like every other member — no member is exempt from redaction.

## Example

The baseline run (AHA-0029, pre-scrub tree, counts only — no values echoed): the wheel's redaction arm names two findings — one line in the cli_safe docstring, one line in the safe parse usage (`keychain-account-id`); the sdist names those two plus twenty-two lines of the safe test file; allowlist and canonicality name none. After the scrub (a neutral, non-numeric example account) the same run names zero findings — and the mutant family keeps proving the arms: reintroduce the known string into either docstring — RED; a *different* numeric id beside the host, or an e-mail address, in any member — RED (the class, not the instance); add a rogue member outside the pinned list — RED; flip one byte of a shipped module — RED (canonicality).

## Template

```python
# the gate in a release path: both artifacts, all arms, zero findings
wheel, sdist = build_artifacts(project_root, outdir)
findings = scan_release(wheel, sdist, project_root)
if findings:                      # a finding stops the release
    for finding in findings:
        print(finding)            # where it is, never what it says
    raise SystemExit(1)
```
