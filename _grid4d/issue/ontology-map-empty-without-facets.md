# Ontology map writes an empty map into a flat Vocabulary

> `ahabase ontology graph` builds a subepic index's map nodes only from `###` facet headings inside `## Vocabulary`; a flat Vocabulary (links without facets) yields zero nodes, and the command writes an honestly empty `## Ontology map` block into the index - a map that maps nothing while the index holds four concepts.

**Status:** open
**Priority:** medium

## Problem

Measured 2026-11-20 (AHA-0030, regenerating the maps after adding a concept): `ahabase ontology graph` wrote `## Ontology map` with an empty mermaid `flowchart LR` into `subepic/ahabase-llm/ontology/00-ahabase-llm-ontology-index.md` and reported `0 concepts, 0 facets, 0 relations` - while that index's `## Vocabulary` lists four linked concepts (Access Path, Verification, Settings Switch, Discovery Registry). The builder reads nodes from the `###` facet headings of `## Vocabulary` (the shape of the root and safe indexes); the llm index's Vocabulary is flat, so every concept is invisible to the map. The write was reverted from the AHA-0030 tree (out of the story's scope); the next full map regeneration writes it again.

## Expected

Either a flat Vocabulary is a shape the map builds (one implicit facet, all links nodes), or the command refuses loudly (`no ### facets in Vocabulary - nothing to map`) instead of writing an empty map that reads as "no concepts".

## Fix

In the ontology map builder (`ontology_map.expected_scopes` / the facet walk) with a red control on a flat-Vocabulary fixture; until then regeneration runs leave the llm index's map hand-reverted.

## Related

- [AHA-0030](AHA-0030) - where it was measured (the story's tree was kept free of the unrelated write)
- [ontology-grid4d-blueprint](ontology-grid4d-blueprint) - the format core whose landing surfaced it
