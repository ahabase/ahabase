# AHA-0034-scrub-report

> Measured scrub record for the public fresh-start seed (AHA-0034 R2). Baseline counts were measured over the full tracked tree of the private repository on 2026-11-22; the seed is the scrubbed export (`scripts/export-public-seed.sh`; the literal patterns live in the uncommitted workspace config - literals never enter committed files, including this report).

## Classes (post-scrub: all zero)

- personal-account: 0 matches (baseline 4,334 + 8 - the personal username and the numeric account id; the bulk was generated artifact-map path listings)
- corporate-account: 0 matches (baseline 5 + 18 - the corporate account name and the company name)
- enterprise-host: 0 matches (baseline 0 - no enterprise hostname was ever present; the schema, tool and project subclasses measured 4, 967 and 18 at baseline, all 0 after scrub)
- internal-mirror: 0 matches in the seed (9 mirror-class artifact maps excluded by the measured rule - foreign-marker lines above the threshold: AHA-0011, 0017, 0018, 0019, 0020, 0024, 0025, 0026, 0030; the kept artifact maps are own-tree listings; the private archive keeps the full record)
- secret-material: 0 matches (token-shaped patterns ghp_/gho_/AKIA baseline 0; GitHub secret scanning with push protection arms automatically at the public flip - a flip-time alert halts the flip)

## Verification

The export script verifies every class at zero over the whole seed tree (counts only) and exits non-zero on any remainder. The AHA-0029 test rows already held the package source (`src/`, `tests/`, README) to account-string absence; this pass extends the guarantee to the story documents and the story history.
