# Epic bootstrap gaps for a non-dbt Epic

> Bootstrapping this Epic showed gaps of evolucean's tooling for an Epic that is a Python package; the fixes belong to evolucean's repository.

**Status:** open
**Priority:** high

## Problem

Found in [AHA-0001](AHA-0001), 2026-10-24, from this repository's side (the surface rule: evolucean's internals are described in evolucean's own repository, not here):

1. The containment check of the story guard does not run on commits of this repository; it is run by hand before every push until fixed.
2. The story prefix chosen by the Human (`AHA-`) had to be set after bootstrap.
3. A pre-push hook meant for dbt projects was installed; it was moved aside.
4. No tests document was minted for the first story; it was written by hand.

## Proposed fix

A story of evolucean's distribution layer in evolucean's repository, which records the details there.

## Stories

- [AHA-0001](AHA-0001) - found
