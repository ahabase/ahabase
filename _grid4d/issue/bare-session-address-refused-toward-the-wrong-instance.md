# Bare session address refused toward the wrong instance

> A collab send addressed by a bare session UUID to a seat on this instance is refused with a message naming a different instance, sending the author to the wrong network.

**Status:** open
**Priority:** medium

## Problem

Found in [AHA-0016](AHA-0016), 2026-10-30/31, by the author seat (6e4b5b8c). Inviting the two reviewers of the story, both seats on instance home (85a6bfd8, 641903b1), the send addressed by the bare session UUID (`--to-session <uuid>`) was refused with `not-in-story-team toward instance:work` - although no seat of instance work was addressed at all. The refusal names an instance the address never named, so the natural reading (go register on work) chases a ghost: the seat is on home and its join would land on home.

The unified form (`--to home:<session>`) was accepted for both seats; the mis-refusal appears when the bare session form lets the CLI resolve the instance on its own.

## Expected

A refusal keys the instance the address actually named. A bare session address that the resolver cannot attribute to one instance is refused as ambiguous, naming the candidates, not as a refusal toward an instance the caller never addressed.

## Fix

In evolucean's repository (the collab send path resolves the address; the surface rule: evolucean's internals are described there) - logged here from the ahabase story that hit it.

## Related

- [AHA-0016](AHA-0016) - the story whose reviewer invites surfaced the refusal
