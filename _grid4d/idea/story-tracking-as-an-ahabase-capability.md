# story tracking as an ahabase capability

> The story game (create, worktree, pool, per-collaboration bindings, complete, release, archive) is today evolucean's CLI - ahabase should grow it as a first-class capability, with the rough edges the ahabase seat measured on 2026-10-30 designed out from the start.

Story tracking is not evolucean-specific: every Epic in the namespace plays the same game, and ahabase (the macOS+Windows-first epic) is the natural home for the capability as a product. The experience of AHA-0012-AHA-0014 measured what the next design owes its players:

- **Epic resolution that cannot misfire:** `create` resolves the epic from the calling tree first, `--epic` explicitly, primary epic only as a warned fallback; the epic is echoed before anything is minted (issue: story-create-mints-on-the-primary-epic-regardless-of-cwd).
- **An undo window:** a just-minted, never-started story (no commits past baseline, no messages) is reversible with one command - worktree, branch, pool entry, pointer and join row removed in reverse order of creation; prune stops refusing every state but stale-released.
- **The pool model travels:** MRU pool, per-collaboration scope bindings with staleness TTL, the legacy global pointer only for id-less invocations - the model is sound, keep it; make its stores inspectable through one command.
- **Cross-epic by construction:** the registry knows every epic; story ids, worktrees and bindings are epic-addressed end to end, so an ahabase seat never sees evolucean stories it did not ask for.
- **Windows from the first line:** the capability itself follows the both-variants rule (AHA-0014) - locks, paths, exec detection and CI prove macOS and Windows in every story.

Seed: the 2026-10-30 ghost-story incident (EVOLUCEAN-0523 minted into the wrong epic, undone by hand) and the three-story safe arc it interrupted.
