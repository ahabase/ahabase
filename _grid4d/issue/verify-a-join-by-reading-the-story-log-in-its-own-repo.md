# Verify a join by reading the story log in its own repository

## Problem

Checking story-team registration with the wrong instrument reports a
false gap and sends needless remedy notes: a shallow grep over commit
messages on the collab branch of a DIFFERENT repository than the
story's own finds nothing even when the join landed minutes earlier.
Each Epic repository carries its own team log (`stories/<STORY>.log`
on its collab branch) - an ahabase story's seats live on the ahabase
repository's collab branch, not the method repository's.

## Occurrences

1. AHA-0021 (2026-11-02): the author verified both reviewer joins by
   grepping commit messages on the evolucean repository's collab
   branch (`git log --oneline origin/collab | grep AHA-0021`) and
   reported "no join" - while `stories/AHA-0021.log` on the ahabase
   repository's collab branch held all three rows (author 15:53:48Z,
   both reviewers 16:08:21Z/16:08:45Z, backing commits ce23062 and
   854db81). The seats' ACKs had been accurate; two unnecessary
   re-join reminders went out before the reviewer's own measurement
   (reading the log file, `git show origin/collab:stories/AHA-0021.log`
   from the story worktree) corrected the author.

## Fix direction

The verification instrument is the log file itself, read from the
story's own repository:
`git -C <story-worktree> show origin/collab:stories/<STORY>.log` (after
a fetch). Never infer membership from commit-message greps, and never
from another repository's branch. A doctor-side guard could flag this
class (join verification that does not read the story's own log), but
the practice fix is one line: read the file.
