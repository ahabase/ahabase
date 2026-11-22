"""The model door: how a tool finds, checks and uses the way to a language model.

Capability: llm-paths

An access path is resolved (``paths``), checked with a classified failure
(``verify``), switched to with a backup (``switch``), pinned for one session
(``session``) and discovered on the machine (``discovery``). A path's
credential is always a reference to a value in the safe, a variable the safe
injects into the consumer process, the subscription login or the cloud
provider's own chain - never a literal value.

The package imports no method; what a method must contribute (the provider
entries of the ladder, a switch guard, the compact window, the probe
sequence) is passed in as an argument.

Implements: implementation-ahabase-llm-blueprint
"""
