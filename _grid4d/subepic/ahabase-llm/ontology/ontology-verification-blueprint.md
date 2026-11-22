# Verification Blueprint

> Proof that a route answers, before it is trusted - and, when it does not, the class of the failure.

**Ontology:** [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) → Trust → Verification
**Placement:** base - a request, a result and a closed set of failure classes are structure software can verify
**State:** defined; the implementation lands in AHA-0024

## Overview

**Verification** = a real minimal request through an [Access Path](ontology-access-path-blueprint) that shows whether the path answers. A subscription path is verified by the presence of its login instead of a request. The result is ok, or a failure with a **class** that says what to do about it:

- **auth** - the credential is missing, expired or refused
- **transient** - a temporary condition (rate limit, timeout, an overloaded service); try again
- **cli** - the check itself failed (the tool is missing, an option unknown, a bare exit code)
- **unavailable** - anything else: the route does not answer

The class is decided in that order: auth first, so an expired login never reads as a dead service. A request costs a few tokens; verifying several paths is staggered, never a burst. Cheap **sensors** answer reachability without a request.

## Attributes

- **Target** - the path verified
- **Result** - ok or failed
- **Class** - auth, transient, cli, unavailable (failed results only)
- **Hint** - the sentence that tells the Human what to do for that class
- **Cost** - a real request (tokens) or a local check (none)

## Relations

- **checks** → [Access Path](ontology-access-path-blueprint)
- **gates** → [Settings Switch](ontology-settings-switch-blueprint) - a switch needs a successful Verification of its target

## Constraints

- A failure detail never contains a credential value; it is redacted before it is shown or logged.
- A result is never reported ok without the request or the login check having run.

## Related

- [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) - the vocabulary

---
