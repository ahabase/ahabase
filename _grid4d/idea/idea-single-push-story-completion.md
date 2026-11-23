# idea-single-push-story-completion

> The operating engine's story completion pushes main twice within seconds; one combined push (or a guard on the archive-only commit) removes a cancelled-run oddity.

**Type:** idea
**Epic:** [AHABASE](../story/AHABASE)
**Raised by:** AHA-0037, 2026-11-23

## Observation

A story completion pushes the completion commit to main, then the release tag, then a second main commit (`chore: archive old stories to history/`) seconds later. Measured on AHA-0036: main run 45119412297 at 05:42:01 (cancelled ~30 s later), tag run 45119425258 at 05:42:08, main run 45119437351 for the archive commit (success). The cancellation came from the workflow's concurrency group; AHA-0037 stops the cancellation. The double push itself stays.

## Options

1. One combined push: the completion commit and the archive commit leave in one `git push`, so main runs once per completion.
2. A guard in the workflow for the archive-only commit (path filter or message guard), at the cost of a rule only this commit shape satisfies.

The completion flow lives in the operating engine (the evolucean `story complete`), outside this repository; the follow-up belongs to the evolucean-story SubEpic.

## Related

- [AHA-0037](../story/AHA-0037) - the story that stops the cancellation
