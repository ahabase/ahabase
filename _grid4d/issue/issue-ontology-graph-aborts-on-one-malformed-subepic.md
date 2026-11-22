# Ontology graph aborts wholly when one subepic ontology is malformed

> A subepic whose `ontology/` holds other than exactly one `00-*-ontology-index.md` aborts the whole `ahabase ontology graph` run (exit 2), taking every other scope's map down with it.

**Status:** open
**Priority:** low

## Problem

Found in [AHA-0018](AHA-0018), 2026-10-31, by the review seat (641903b1) as a non-blocking observation. `epic.py`'s `subepics()` returns every directory under `_grid4d/subepic/`, and `ontology_map.subepic_scopes` raises `EpicError` when such a directory holds an `ontology/` with other than exactly one `00-*-ontology-index.md`; that error aborts the entire `ontology graph` run, so one malformed subepic erases the projection of the whole Epic. Latent at the story's pin (one subepic, exactly one index); the trigger arrives with the second capability subepic.

## Expected

The failure of one unit does not erase the others: the error names the offending subepic (or lists every offender in one pass) and the remaining scopes still render and check.

## Fix

In this package, where the level rule and the scopes live (AHA-0018's code): isolate the scope error in `ontology_map.expected_scopes` / `cli_transparency.graph`, or collect all offenders before raising.
