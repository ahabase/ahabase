# safe run guard member without a test

> The check that a bound consumer still exists and is executable has two conditions; only the first is held by a test.

**Status:** open
**Priority:** low

## Problem

Found after the release of [AHA-0007](AHA-0007), 2026-10-26, by the home deepseek seat (executed on a clone): the guard in the consumer check refuses a bound consumer that vanished or is not executable. A test holds the vanished case; removing only the executable condition leaves the whole suite green, and a bound consumer that lost its executable bit then ends in an uncaught permission error instead of the named refusal with its way through. It stays fail-closed - nothing runs - so this is the quality of the message, not a hole in the property.

## Expected

A test for a bound consumer without its executable bit asserting the named refusal; the mutation of the second condition turns it red.

## Fix

The next package story that touches the safe; the reviewer's fixture is ready (a mirror of the vanished test with the mode set to 644).

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 4
- [AHA-0007](AHA-0007) - where the guard was added
