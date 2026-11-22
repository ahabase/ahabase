# Interactive checkpoints from the start

> Push design questions to the reviewer seats before the code exists - measured amendments beat end-review rework.

**Type:** Idea
**Origin:** AHA-0021's first landing checkpoint (2026-11-02)

## Observation

The landing story pushed its door-API design question to both reviewer
seats before writing any code (checkpoint 1). Both replies carried
measured amendments, not opinions: an independently reproduced 51-file
call-site census with the defect class named (a missed parameterless
site), a correction that the proposed settings convention was new
rather than ported (so missing-settings semantics had to be defined),
and a structural fact nobody had on the table (the data dir is the
root of the collaboration fabric - the store must not silently split
per epic). All three landed in the contract and the code before the
first commit; an end-of-story review would have found them as rework
over a landed API.

## The shape that worked

- The checkpoint names the decision, the measured facts, the options
  (A/B) and a recommendation - a seat can reply with a verdict plus
  amendments without re-deriving the context.
- Each seat gets a per-seat ask on the same question; two independent
  measurements of the same number (the 51-file census) is a stronger
  witness than one.
- The author closes the checkpoint with an explicit synthesis message
  (what was adopted, verbatim) so the thread's decisions are readable
  without reconstructing them from replies.

## Proposal

Make pushed checkpoints with per-seat asks part of the landing-story
practice for design-shape decisions (the story's R_team), not only the
completion-time verdict review: one checkpoint before the code, one on
the landed branch. The completion verdict review stays unchanged -
checkpoints are advisory to the author, verdicts gate completion.
