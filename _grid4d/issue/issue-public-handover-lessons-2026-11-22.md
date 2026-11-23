# issue-public-handover-lessons-2026-11-22

> Lessons learned from the AHA-0034 public handover session - every defect and idea recorded with its fix and its guard, so the same error class never repeats.

**Type:** issue
**Epic:** [AHABASE](AHABASE)
**Status:** open (all fixes deployed; the team-work ideas are the standing improvement)

## The session's error inventory

Every error below was found and fixed the same day; each carries the guard now in place.

1. **Rename trap (the leak).** Three worktree pushes traveled through a pre-rename origin URL after the flip - the old name resolved to the freshly public repository - shipping the private commit chain. Guard: the remote-pin pre-push guard in every ahabase-org tree ([issue-remote-pin-guard](issue-remote-pin-guard)); rule: repin every clone of a renamed repository (main tree AND worktrees - one shared remote config) before any git operation anywhere.
2. **Staging CI unwatched.** The staging repository's Actions were red on three consecutive seed pushes (hours before the flip) - the same test fixture failure that later broke the public CI. Nobody's habit or suite row watched them. Guard: cold-CI below; the flip checklist gains "staging CI green at the seed tip".
3. **No cold CI on the scrubbed artifact.** The full package test suite never ran against the SCRUBBED tree before public pushes - the only environment where scrub-induced breakage is visible. Guard: the handover procedure now runs a fresh-venv install + full pytest on the export before every public push (measured green: 478 passed before the remediation push).
4. **Untracked files ride directory exports.** The export script's directory mode copied the whole working tree - six untracked files (editor state, empty and draft blueprints) shipped public. Guard: a git-tree source exports TRACKED CONTENT ONLY (git archive HEAD); .git-less review copies keep the directory mode.
5. **Pre-flip-red rows hide row bugs.** Two suite rows carried defects (a case-sensitive visibility comparison; a piped `grep -q` that SIGPIPEs under pipefail) that were invisible while earlier legs kept the rows red by design - the rows had simply never executed their tails. Lesson: rehearse every row leg-by-leg at authoring time, both outcomes.
6. **`gh` prints visibility UPPERCASE.** Compare the `isPrivate` boolean, never a visibility string.
7. **`grep -q` early-exits and SIGPIPEs its producer.** Under pipefail this is a deterministic exit 141. In pipes, read the whole input (`grep PATTERN >/dev/null`).
8. **`story complete` fetches origin mid-run.** Its merge branch builds from origin/main - after renames this fetched the wrong repository and aborted on unrelated histories. Rule: complete runs only with repinned, verified remotes (the pin guard covers the pushes; the doctor-side divergence check is the pending CLI follow-up).
9. **A credential in a remote URL.** The test epic's origin carried an embedded PAT in plaintext. Removed; keychain auth verified; rotation recommended. Rule: secrets never live in remote URLs - the URL is config, the keychain is the vault.
10. **Composed-fixture fragment hygiene.** A runtime-composed test fixture carried one fragment with a contiguous class token; the scrubber replaced it, the composed name turned invalid, and the failure printed the composed stem into the public run log. Rule: every fragment of a composed identifier must itself be token-free (and the leaked run log was deleted).

## Ideas - team work as the error-rate reducer

The Human's question: could better use of team work minimize this error rate? Yes - every error above was single-seat execution, and each has a seat-shaped guard:

- **Execution checkpoint review.** Irreversible operations (renames, deletes, public pushes, flips) send the exact command list to a second seat before execution - the collab ask/review flow applied to commands, not just documents. The flip plan was reviewed; the command list never was.
- **A seat owns CI until green.** After every push to staging/public, one seat watches the run to conclusion and reports - red staging CI would have been caught three pushes early.
- **Cold-CI is a gate step, not a habit.** The export gate (or the story R2 row of any future public-push story) runs the artifact's own suite on the export before push - measured, not remembered.
- **Per-leg row rehearsal at authoring.** The author of a suite row runs each leg standalone in both polarities before committing it; a reviewer seat re-runs the never-executed tails (the legs after the first red-by-design leg) explicitly.

These become the standing practice for public-push stories; the CLI-side integrations (pin guard in `epic init`, doctor divergence check, gate cold-CI step) are recorded in [issue-remote-pin-guard](issue-remote-pin-guard).
