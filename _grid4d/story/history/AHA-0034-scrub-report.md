# AHA-0034-scrub-report

> Measured scrub record for the public fresh-start seed (AHA-0034 R2).
> Method (one, for baseline and seed alike, fixed at review round 1):
> case-insensitive, contiguous-token scan over every tracked file, counts are
> lines with at least one match; class tokens are kinds (account stems, the
> numeric id, schema, tool, project, company, host), stems counting their
> longer forms. Baseline figures are line counts over the committed private
> tree at da75107 (round-2 fix: the earlier figures were counted over a
> pre-commit working tree and reproduced under no ref). The two account stems
> overlap - the corporate stem is a substring of the personal surname - so
> class baselines are per-token line counts and every token zeroes
> independently; the overlap costs nothing at the gate. The literals live in
> the uncommitted workspace config - literals never enter committed files,
> including this report. The artifact
> containment scanner's own runtime-composed vocabulary (the split string
> literals that compose these same identifiers inside
> `src/ahabase/artifact_containment.py` and its test file, the AHA-0029
> composed-vocabulary design that ships no contiguous identifier) is the
> guard's own mechanism, not the guarded content: it sits outside every class
> population by rule, and the classes measure the contiguous identifier only.

## Classes (post-scrub: all zero)

- personal-account: 0 matches (baseline 4,337 + 8 - the account-name stem in any case form plus the numeric account id; line counts over the committed tree at da75107; the bulk was generated artifact-map path listings)
- corporate-account: 0 matches (baseline 4,344 + 9 - the work-account stem in any case form, covering its longer compounds, plus the company name; same ref and method - most of the stem's lines are the personal surname's tail per the overlap note above)
- enterprise-host: 0 matches (baseline 0 - no enterprise hostname was ever present; the subclasses measured schema 4, tool 967, project 18 + 10 at baseline, all 0 after scrub)
- internal-mirror: 0 matches in the seed (9 mirror-class artifact maps excluded by the measured rule - foreign-marker lines above the threshold: AHA-0011, 0017, 0018, 0019, 0020, 0024, 0025, 0026, 0030; the kept artifact maps are own-tree listings at 10 markers or fewer against the threshold of 100, re-verified fail-closed after exclusion; the private archive keeps the full record)
- secret-material: 0 matches (the export script's fixed shape scan over the whole seed - github pat classic and fine-grained, github oauth, AWS AKIA, sk-, slack, gitlab, google, PEM private-key headers - measured 0 candidate lines and fails closed on any hit; GitHub secret scanning with push protection arms automatically at the public flip, the second, independent net)

## Verification

The export script verifies every class at zero over the whole seed tree with
the same case-insensitive method the replacement used (counts only), exits
non-zero on any remainder, re-verifies the mirror rule over the kept maps,
and runs the secret-shape scan - all fail closed. The suite's R2 row re-runs
the export gate over the story tree itself whenever the uncommitted config is
present (a public clone without the config measures the committed report legs
only: there are no literals to scrub there). The AHA-0029 test rows already
held the package source (`src/`, `tests/`, README) to account-string absence;
this pass extends the guarantee to the story documents and the story history.

## Commit metadata (accepted non-goal, Human ruling 2026-11-22)

- commit-metadata: the maintainer identity (real name and personal address)
  stays in the seed and handover commits as author and committer - an
  explicitly accepted non-goal ("that is how open source works: the author
  is visible; my personal address is fine", Human, 2026-11-22). Measured at
  the ruling: the seed history carries exactly 1 distinct author identity
  and 1 distinct committer identity; the R3 suite row pins exactly-one at
  the flip, so no OTHER identity (a corporate account, a stray machine) can
  ever ride the public history unnoticed.
