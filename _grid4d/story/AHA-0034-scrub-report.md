# AHA-0034-scrub-report

> Measured scrub record for the public fresh-start seed (AHA-0034 R2).
> Method (one, for baseline and seed alike, fixed at review round 1):
> case-insensitive, contiguous-token scan over every tracked file, counts are
> lines with at least one match; class tokens are kinds (account stems, the
> numeric id, schema, tool, project, company, host), stems counting their
> longer forms. The literals live in the uncommitted workspace config -
> literals never enter committed files, including this report. The artifact
> containment scanner's own runtime-composed vocabulary (the split string
> literals that compose these same identifiers inside
> `src/ahabase/artifact_containment.py` and its test file, the AHA-0029
> composed-vocabulary design that ships no contiguous identifier) is the
> guard's own mechanism, not the guarded content: it sits outside every class
> population by rule, and the classes measure the contiguous identifier only.

## Classes (post-scrub: all zero)

- personal-account: 0 matches (baseline 4,339 + 8 - the account-name stem in any case form plus the numeric account id; the bulk was generated artifact-map path listings)
- corporate-account: 0 matches (baseline 4,346 + 9 - the work-account stem in any case form, covering its longer compounds, plus the company name)
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

## Pending (review round 1, for the Human)

- commit-metadata: the seed's two commits currently carry the maintainer's
  real name and address as author and committer; a public flip would publish
  them permanently. Decision open: neutral no-reply authorship for the seed
  and handover pushes, or an explicitly recorded accepted non-goal. The
  chosen outcome becomes a measured line here and a suite row at the flip.
