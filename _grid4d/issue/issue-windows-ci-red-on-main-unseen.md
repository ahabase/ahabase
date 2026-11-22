# issue: the Windows leg of the CI matrix is red on main and nobody saw it

**Status:** resolved (AHA-0025: the four tests fixed; the CI matrix on `main` green on every leg, last four runs checked 2026-11-09)
**Type:** rule breach (Both OS variants in the same story), silent failure
**First seen:** 2026-11-08, AHA-0024 R3a (the CI run of a story branch)

## Problem

The Epic rule "Both OS variants in the same story" relies on the CI matrix (macOS, Windows, Ubuntu) turning red in the story that breaks the other OS. The Windows leg has been red on `main` for at least the last four completed stories (the runs of AHA-0022 and AHA-0023 and their archive commits), and no story reported it. Measured 2026-11-08 on the run of the latest `main` commit: 4 failed, 206 passed, 2 skipped on Windows; macOS and Ubuntu green.

The four failures, each in a test written by an earlier story:

| Test | Failure | Cause class |
|------|---------|-------------|
| `tests/test_config_door.py::test_env_config_override_wins` | `'\\from-env' == '/from-env'` | the test compares a settings value with a POSIX path literal; the door expands it to the platform form |
| `tests/test_config_door.py::test_duplicate_key_warns_once_and_last_wins` | `'\\b' == '/b'` | the same |
| `tests/test_safe.py::test_gh_login_per_account_dir` | mode `0o777` instead of `0o700` | the test asserts a POSIX owner-only mode; Windows reports no such bits, so the code needs a Windows equivalent (an owner-only ACL) or the test needs to say what holds there |
| `tests/test_safe_git_helper.py::test_git_credential_fill_asks_the_helper` | `warning: failed to probe 'https://fixture.github.example/'` | the fixture's host is probed on a platform where the helper's git call behaves differently |

A story branch adds its own failures on top of these, which makes its own Windows result hard to read: AHA-0024 R3a found one of its own tests red this way and had to subtract the four.

## Why it matters

Windows is a supported platform of the open package ("built for macOS and Windows immediately"); a red leg that nobody reads is the same silent failure as an unread guard, and it lets a Windows-only defect (the owner-only mode on the gh login directory is a safe-first matter) ship.

## Candidate fixes

1. A story that fixes the four tests (the first two are test-only; the third decides what owner-only means on Windows and may change code; the fourth needs the fixture host made inert).
2. A completion gate: `story complete` reads the CI result of the story branch and refuses a red leg, naming the failing tests (the method's completion is the place; recorded as an idea there).
3. Until fixed, each story records the Windows failures it did not cause, so its own result stays readable.

## Related

- [AHABASE](AHABASE) - the Rules, "Both OS variants in the same story"
- [AHA-0024](AHA-0024) - the story that found it

---
