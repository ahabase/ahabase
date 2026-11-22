# AHA-0008-tests

> Test definition for AHA-0008 with one test per requirement.

## Design

The story is analysis; the rows check that every lane delivered its document with the tree and moment it read and a separation of read from inferred, and that the synthesis carries its parts. Every guard stands alone with an explicit exit. The rows stay red until the lanes land.

## Definition

```yaml
tests:
  - name: R1_lane_outputs
    description: every lane document exists, names what it read and separates read from inferred
    command: |
      for lane in ahabase-state evolucean-root evolucean-subepics transparency plan-realism; do
        f=_grid4d/story/AHA-0008-lane-$lane.md
        if [ ! -f "$f" ]; then echo "missing lane: $lane"; exit 1; fi
        # the tree and moment read, in a Read line or the lane's header
        if ! grep -qE "\*\*(Trees |Date )?[Rr]ead( on)?:\*\*" "$f"; then echo "$lane: does not name what it read"; exit 1; fi
        # read and inferred kept apart: as sections, or as inline marks
        if ! grep -qiE "^## (Read|Measured)|\*\*read\*\*|\(read\)|^\*\*Read\.\*\*" "$f"; then echo "$lane: no read marks"; exit 1; fi
        if ! grep -qiE "^## Inferred|\*\*inferred|\(inferred\)|^\*\*Inferred\.\*\*" "$f"; then echo "$lane: no inferred marks"; exit 1; fi
      done
    expect:
      exit_code: 0
  - name: R2_synthesis
    description: the synthesis states the state, the realism, the order, the transparency design and the decisions for the Human
    command: |
      f=_grid4d/story/AHA-0008-synthesis.md
      if [ ! -f "$f" ]; then echo "no synthesis"; exit 1; fi
      for s in "## Where both Epics stand" "## Is the plan realistic" "## Order of the next stories" "## Transparency to build first" "## Decisions for the Human"; do
        if ! grep -qF "$s" "$f"; then echo "missing: $s"; exit 1; fi
      done
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_lane_outputs | ✅ | 2026-10-26 |
| R2_synthesis | ✅ | 2026-10-26 |

## Related

- [AHA-0008](AHA-0008) - Parent story
