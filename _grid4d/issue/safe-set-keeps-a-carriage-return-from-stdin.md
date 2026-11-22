# safe set keeps a carriage return from stdin

> A value piped into `ahabase safe set` with a Windows line ending keeps its carriage return, so `safe compare` against the file it came from answers "different".

**Status:** open
**Priority:** low

## Problem

Found in the review of [AHA-0003](AHA-0003), 2026-10-25, by the home primary reviewer (advisory). `set` strips only a trailing `\n` from stdin, while `compare --file` strips `\r\n`. A value piped with CRLF is stored with its `\r`; comparing it with the same file then reports "different". The failure is in the safe direction (a false "different", never a false "same"), and on the supported platforms piped input ends with `\n`.

## Expected

`set` strips the same line ending as `compare --file` (`\r\n`), with a test that a CRLF-piped value compares "same" against its file.

## Fix

A small package story, at the latest when Windows becomes a supported platform.

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 8, comparison without disclosure
- [AHA-0003](AHA-0003) - where it was found
