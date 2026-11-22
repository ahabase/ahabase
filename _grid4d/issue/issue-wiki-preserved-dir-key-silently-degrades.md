# wiki preserved-dir key silently degrades unquoted

> The wiki config's preserved-directory directive (`"dir/::"` under `documents:`) is indistinguishable from a typo when the key is left unquoted: YAML eats the second colon, the directive becomes a phantom manual mapping, and sync purges the wiki-only pages the author meant to preserve - no warning anywhere.

**Status:** open
**Priority:** high

## Problem

Measured at the AHA-0036 golden capture (2026-11-22, landing day, live donor run over the fixture epic): the line

```yaml
documents:
  keepdir/::          # unquoted - the trap
```

parses as the key `keepdir/:` mapped to null (the first colon ends the key, the second is eaten as the separator, the empty value is null). The preserved-dir pass looks for the `::`-suffixed convention, does not find it, and the row falls through to the manual-mapping skip path - the summary even counts it ("Documents skipped (manual): 2") under the phantom name. The directory is never registered as preserved, so the orphan purge removes its wiki-only pages: in the capture, `keepdir/kept.md` was deleted. Silent data loss in the mirror, caused by a quoting slip the loader never surfaces.

The port keeps the behavior byte-faithful to the donor (the golden depends on it) and documents the quoted form - blueprint rule 5 of [implementation-ahabase-wiki-door-blueprint](implementation-ahabase-wiki-door-blueprint) - but a convention that only works quoted and fails silently unquoted is a recurring trap for every config author, not a documentation problem.

## Expected

The config loader fails closed: a `documents:` key that ends `/::` after YAML parsing (the degraded shape - a trailing `/:` with a null value) refuses with the remedy naming the quoting rule ("quote the key: `\"dir/::\"`"), the same fail-closed style as the publish identity gate. The refusal turns silent data loss into a one-line fix. The design question the fix story answers: whether to also accept the degraded shape as the directive (tolerant) - rejected here because tolerance keeps the typo class (a real document genuinely named `dir/:`) ambiguous; refusal is unambiguous.

## Fix

Deliberately out of AHA-0036: the landing story pins byte parity with the donor (the committed golden), so the quirk rides along, documented. The fix is a loader guard plus a suite row with both polarities (unquoted refuses; quoted preserves through a purge) in the wiki door's suite - its own small story or a rider on the next wiki-door story.

## Related

- [AHA-0036](AHA-0036) - the landing that measured the quirk (capture provenance in its Notes)
- [implementation-ahabase-wiki-door-blueprint](implementation-ahabase-wiki-door-blueprint) - rule 5, the quoted-form convention as shipped
- [ontology-wiki-blueprint](ontology-wiki-blueprint) - the concept
