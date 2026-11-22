# AHABASE-SAFE

> The safe: values that grant access live in the user's own store, never in a document or a repository, and reach only the one process that needs them

**Type:** SubEpic
**Inherits:** ahabase
**StoryPrefix:** AHA-SAFE-
**CodeEvidence:** parent

## Overview

The safe is the first capability subepic of ahabase. The Human's shape ruling of 2026-10-31 ([AHA-0017](AHA-0017), executed by [AHA-0018](AHA-0018)): the Epic's ontology carries the architecture - structure that spans capabilities; a concrete capability's concepts live in that capability's subepic. The safe's ten concept blueprints moved here from the Epic's ontology; the structure they serve - the Boundary and the Trust Zone - stays there.

What the safe is: a value that grants access (a token, a password, a key) never sits in a knowledge document or a repository; it lives in the user's own store, configuration holds a reference to it, and only the one consumer process that needs it reads it. The manifest describes every secret without its value; the guards keep values away from agents and out of output.

The stories of this subepic are minted under the prefix `AHA-SAFE-`.

## Related

- [AHABASE](AHABASE) - the parent Epic
- [00-ahabase-safe-ontology-index](00-ahabase-safe-ontology-index) - the safe's concepts and their map
- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the implementation and its code
