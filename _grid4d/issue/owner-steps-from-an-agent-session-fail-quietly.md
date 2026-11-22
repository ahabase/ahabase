# Owner steps launched from an agent session fail without a clear trace

**Type:** team-work friction (AHA-0022 R_team)
**Found:** 2026-11-06, live, AHA-0022 R4 (work instance)

## Symptom

The owner's steps of the safe (`safe compare`, `safe target add`, `safe refresh`) need the owner at an interactive terminal: they ask for the name to be typed, or refuse with "needs its owner at an interactive terminal". The agent handed the steps to the Human as `! <command>` lines, but such a line runs inside the agent's session, which is not an interactive terminal. Separately, the Human ran the commands with the installed `ahabase`, while the steps needed the story's CLI from the worktree. That second attempt failed with "unknown target kind" - the correct fail-closed refusal, but one more round.

It took three rounds before the owner ran the right binary at a real terminal.

## Way forward

- An agent hands owner steps as plain terminal lines, never as `!` lines, and names the binary by its full path whenever a story's unreleased CLI is needed.
- The refusal text of an owner step could name its own remedy: "run this in your own terminal, not through an agent session".
