# safe git target absence remedy explains nothing

> The git-credential `absence` message points at `git config --get-all credential.helper` - but on macOS the likeliest failure (a helper IS configured and its item is absent: locked keychain, never written) makes that command answer `osxkeychain` and explain nothing.

**Status:** open
**Priority:** medium

## Problem

Found in the delta review of [AHA-0012](AHA-0012) at b3b0df7, 2026-10-30, by the reviewer-deepseek seat, measured with system git against a scratch HOME: with the system config in play `--get-all` reports `osxkeychain` (rc=0) in a run whose resolution fed no helper; with `GIT_CONFIG_NOSYSTEM=1` it reports none (rc=1); a repo-local reset prints an empty value (rc=0). The message fires whenever `present()` is False, and its "with none configured, approve writes nothing" clause describes only one of the cases it fires on. Helper resolution is also cwd-sensitive, and the owner runs the remedy from wherever they are, not from where the safe ran.

## Expected

The absence message names the condition generically (no stored item behind the resolved helper chain) and both real causes - no helper configured, or a helper configured whose store holds no item (locked keychain, never written) - without claiming which one fired.

Along the way (same review, non-blocking): `test_presence_check_prompts_nothing` asserts the env dict the code built without arming against an ambient `GCM_INTERACTIVE`/`GCM_GUI` (the older `GIT_*` pair likewise) - `monkeypatch.delenv` before the call makes the assertions load-bearing.

## Fix

A small safe story, together with the stale-copy proof.

## Related

- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - rule 7, the absence messages
- [AHA-0012](AHA-0012) - where the message landed (754fe81)
