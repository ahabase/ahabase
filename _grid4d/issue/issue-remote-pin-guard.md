# issue-remote-pin-guard

> A renamed repository's old URL silently resolves to whatever now owns the old name; an unpinned clone then pushes to the wrong repository without warning.

**Type:** issue
**Epic:** [AHABASE](../story/AHABASE)
**Raised by:** AHA-0034 handover incident, 2026-11-22
**Status:** open (machine guard deployed; CLI-side integration pending)

## The defect class

GitHub redirects a renamed repository's old URL to the renamed repository - until the freed name is taken by another repository, at which point the old URL resolves to the NEW owner with no warning anywhere. Any clone (main tree or worktree - they share one remote config) holding the stale URL ships its pushes to whichever repository currently owns the old name.

Measured instance: during the AHA-0034 public flip, three worktree pushes traveled through the pre-rename origin URL to the freshly flipped public repository, carrying the feature branch and its full private commit chain (the branch was deleted within the hour, the repository was recreated from a clean export, and the leaked commit IDs return 404 against the fresh object store; forks 0, watchers 0 at containment).

## Deployed machine guard (2026-11-22)

A `pre-push` hook in every ahabase-org tree (epic clone, private archive, seed clone, evolucean; worktrees inherit through the common git dir) compares the push destination URL against a pinned repo suffix in local config:

- `ahabase.remotePin` (local config) = the intended `owner/name.git` suffix
- a push whose destination does not end with the pin is REFUSED with the repin remedy printed
- no pin configured = pass-through (the guard is inert outside the ahabase-org trees)

Positive control measured: pointing a pinned clone at the quarantine repository refuses; restoring the pinned URL passes. Four trees verified MATCH (pin vs URL).

## Pending CLI-side integration (future story)

1. `epic init` writes `ahabase.remotePin` and installs the guard with the hook payload
2. `knowledge-usage doctor` reports clones whose origin URL diverges from their pin (the rename detector)
3. the rename runbook step: repin every clone and worktree of a renamed repository BEFORE any git operation anywhere in it
