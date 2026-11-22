# ahabase LLM Blueprint

> The model door: one package for finding, checking and switching the way to a language model, with a credential that is always a reference.

**Implements:** [ontology-access-path-blueprint](ontology-access-path-blueprint), [ontology-verification-blueprint](ontology-verification-blueprint), [ontology-settings-switch-blueprint](ontology-settings-switch-blueprint), [ontology-discovery-registry-blueprint](ontology-discovery-registry-blueprint)
**Story:** [AHA-0024](AHA-0024)
**Code:** llm.__init__, llm.paths, llm.discovery, llm.verify, llm.switch, llm.session, cli_llm

## Overview

A tool that works with a language model reaches it through an access path. This blueprint fixes what lands in the open package, what stays with the method that uses it, how credentials are handled, and the seam contract between the two. The order of work is the Human's: ontology, then this blueprint, then the code. The seam contract below is frozen when this requirement closes and is quoted unchanged by the method-side story that consumes it.

## Rules

1. **A credential is a reference** - a path's auth is `safe://NAME`, a variable the safe injects, the subscription login, the cloud provider's own chain, or a key helper; a literal is refused (Safe first).
2. **Verify, then switch** - the settings change only after a successful verification of the target, after a backup, atomically; a failure carries its class (auth, transient, cli, unavailable).
3. **Local discovery only** - discovery uses cheap local checks: no network, no token, presence never value.
4. **Per-instance data stays with the instance** - the variants file, the registry, the backups and the payloads are written in the instance's data directory, never shipped with the code.
5. **The dependency is one way** - nothing under `ahabase.llm` imports a method; what the method must contribute (a guard, the compact window, the provider entries of the ladder) is passed in as an argument.
6. **Both operating systems in the same story** - what differs is isolated and the CI matrix runs the suite (Both OS variants).
7. **Written as public** - no host, account, local path or provider secret in code, tests or documents (Knowledge written as public; Links point inward).

## Module layout

| Module | Holds | Ported in |
|--------|-------|-----------|
| `ahabase.llm.paths` | path definitions and kinds, the variants loader, authentication resolution, the ladder and rescue order, the identity in force | R3a |
| `ahabase.llm.discovery` | introspection, local availability, the per-machine registry | R3a |
| `ahabase.llm.verify` | the preflight request, the launch proof, failure classification, the first working path, the cheap reachability probe | R3b |
| `ahabase.llm.switch` | the verified switch, the atomic settings write, backups and restore, output redaction | R3c |
| `ahabase.llm.session` | the per-session payload and its check | R3c |

Four concept families, ported in three commits (R3a, R3b, R3c). The door `ahabase llm ...` is registered behind the one registry (the Door concept) and calls only these modules.

## Function-level cut

Every top-level function and class of the four method modules that the cut touches, with its disposition: **M** moves unchanged in behaviour, **M\*** moves refactored (the reason names the change), **S** stays with the method, **SPLIT** divides. The table is generated from the syntax tree of the four files, so a function cannot be missing from it.

| Function | Disp. | Moves to | Reason |
|----------|-------|----------|--------|
| `path_resolution._load_config_paths` | M* | paths | variants loader; the file is per-instance data and stays; the loader takes a path argument |
| `path_resolution.pin_error` | M | paths | refusal text for a pin that cannot be built |
| `path_resolution.pinned_model` | M | paths | the model a pinned path serves |
| `path_resolution.rescue_order` | M | paths | ladder schema: the order paths are tried |
| `path_resolution.known_paths` | M* | paths | definition schema and native kinds move; provider entries become method-supplied data |
| `path_resolution.resolve_auth` | M* | paths | safe reference or injected variable; a literal is refused |
| `path_resolution.resolve_key` | M* | paths | key helper command kept; a literal is refused |
| `path_resolution._keychain_login_present` | M | paths | presence only |
| `path_resolution.subscription_login_source` | M | paths | presence only |
| `path_resolution.subscription_login_present` | M | paths | presence only |
| `path_resolution.bedrock_credentials_source` | M | paths | presence only |
| `path_resolution.bedrock_credentials_present` | M | paths | presence only |
| `path_resolution.current_path` | M | paths | identity in force, derived from settings and environment |
| `path_resolution.has_conversation` | S | - | conversation continuation of the tool, a launch concern of the method |
| `path_resolution.claude_running_in` | S | - | process check for continuation, a launch concern of the method |
| `path_resolution._settings_env` | M | paths | reads the settings env block |
| `path_verification.verify_path` | M | verify | the preflight request |
| `path_verification.key_headers` | M | verify | headers built from the resolved key, never logged |
| `path_verification._post_messages` | M | verify | the minimal messages request |
| `path_verification.verify_path_family` | M | verify | staggered verification of several paths |
| `path_verification.foreign_live_sessions` | S | - | reads the method session registry; the switch takes a guard callback the method supplies |
| `path_verification.switch_path` | M* | switch | verified switch; writes a key helper reference, never a literal; guard callback added |
| `path_verification.redacted` | M | switch | redaction of output |
| `path_verification.new_backup_path` | M | switch | backup naming |
| `path_verification.probe_cwd` | M | verify | working directory for a launch proof |
| `path_verification.launch_overlay` | M | verify | settings overlay for a launch proof |
| `path_verification.prove_launch` | M | verify | one tool turn through a path |
| `path_verification.parse_launch_stream` | M | verify | reads the launch result |
| `path_verification.classify_failure` | M | verify | auth, transient, cli, unavailable |
| `path_verification.first_working_path` | M | verify | the first candidate that answers and through which the tool answers |
| `path_verification.write_settings_atomically` | M | switch | atomic write |
| `path_verification.session_env` | M* | session | per-session payload; env overrides passed in by the caller; key helper reference |
| `path_verification._compact_window_table` | S | - | method settings table llm.compact_window |
| `path_verification.resolve_compact_window` | S | - | method tuning by role and model; the value is passed to session_env |
| `path_verification.session_env_out` | M* | session | writes the payload; carries a key helper reference, no resolved literal, no timestamped copies |
| `path_verification.session_env_check` | M | session | checks a payload |
| `path_verification.list_backups` | M | switch | lists backups |
| `path_verification._backup_target` | M | switch | backup location |
| `path_verification.restore_backup` | M | switch | restore; the backup must parse |
| `path_verification.validate_proxy_config` | S | - | proxy configuration, provider tooling |
| `path_verification.recover_service` | S | - | service recovery, provider tooling |
| `path_verification._probe_suffixes` | S | - | pattern-overridable probe sequence, method knowledge layer |
| `path_verification.path_sensors` | SPLIT | verify.reachable / method | the cheap probe is extracted as reachable(); the per-path sensor loop and reporting stay with the method |
| `discovery.get_registry_path` | M* | discovery | registry path from the config door instance root; the default filename becomes `llm-paths-registry.yml` (the method's wrapper passes its existing file as `registry_path`, so no existing registry is orphaned) |
| `discovery.machine_id` | M* | discovery | from the config door machine id |
| `discovery.load_registry` | M | discovery | reads the per-machine registry |
| `discovery.save_registry` | M | discovery | writes the per-machine registry |
| `discovery.assess_local_availability` | M* | discovery | cheap local checks only; gains the `safe://` branch (entry named in the manifest, presence only), the key helper branch, and the `builtin` / `variants_file` arguments |
| `discovery.discover` | M | discovery | introspection and registry update |
| `discovery.load_machine_availability` | M | discovery | this machine only |
| `paths.RestartPlan` | S | - | guarded proxy restart orchestration |
| `paths.recover_with_fallback` | S | - | guarded proxy restart orchestration |

Moving: 41 of 52 (31 unchanged, 10 refactored); staying: 10; split: 1. Files that stay with the method in full: the ambient session backend (it rides the launching session's connection, a method concern), model selection, the model catalogue and configuration, the pattern-driven hook guidance, the proxy and service tooling, local model runtimes and telemetry.

## Dependencies of the moving code

Measured over the syntax tree of the four method modules (module-level and nested imports, the calls, and the reads of attributes of the resolution module), restricted to the functions marked M or M\*:

| Needs | Used by | Resolution in the package |
|-------|---------|---------------------------|
| the data directory | `session_env_out` | the package's `ahabase.config.get_data_dir(*, epic)`, whose `epic` keyword is REQUIRED (the method's own function defaults it); the moved function takes `epic` as a required keyword and the method's delegating wrapper passes its epic, so no bare call remains |
| the instance root, the machine id | the discovery registry | `ahabase.config.get_instance_root()` and `get_machine_id()`, both argument-free in the package, called bare as today |
| an atomic file write (temp file in the same directory, flush and fsync, existing mode kept, `os.replace`, temp removed on any failure) | `write_settings_atomically` | a small private writer in `ahabase.llm.switch` with the same semantics; the method's runtime-state utility is not imported |
| the set of paths whose verification forces a tool-use probe (`TOOL_PROBE_PATHS`, derived from the provider entries) | `verify_path` | none: `verify_path` takes the set as a keyword argument, default empty; the method passes its own set (an explicit `require_tool_use` still overrides either way) |
| the context floor a launch must clear (`CONTEXT_FLOOR_ESTIMATE`, a measure of the tool's own schemas) | `session_env` | the constant is a property of the tool, not of a provider, and moves into `ahabase.llm.session` |
| the settings env reader (`_settings_env`) | the discovery functions | ported as `ahabase.llm.paths.settings_env` |
| the safe (`ahabase.safe`: the consumer check, the value read, the manifest entry test) | `resolve_auth`, `resolve_key`, the discovery of `safe://` paths | in the package already; imported late and only where a `safe://` reference is met, so a path set with no reference never loads it |
| the session registry of the method | the switch guard | none: the switch takes a `guard` callback and the method supplies it |
| the method's settings table for the compact window | the session payload | none: the caller passes `env_overrides` |
| the proxy default port | the provider entries of `known_paths` | none: the provider entries leave the package as method-supplied data |
| the probe sequence (the endpoint suffixes tried, overridable by the method's knowledge layer) | `reachable()`, the extracted half of `path_sensors` | none: the sequence is passed in as an argument; the method keeps `_probe_suffixes` and its pattern override and supplies the sequence |
| the pattern-driven hook guidance and the proxy configuration | only functions marked S | none: they stay |

After this table no function that moves imports from, or calls into, a function that stays. A static check in R3 asserts that nothing under `ahabase.llm` imports a method package.

## Credential flow (Safe first)

Every credential the moving code touches, and what is written to disk:

| Credential | How it arrives | Written to disk |
|------------|----------------|-----------------|
| A path's key | a reference `safe://NAME` resolved into the consumer process only, a variable the safe injects into that process (`safe run --env VAR=safe://NAME`), or the key helper `ahabase llm key PATH_ID` (below) | nothing |
| A literal token in a path definition | refused with a message naming the path, never echoed | nothing |
| The subscription login, the cloud provider's credential chain | presence is checked; the value is never returned, logged or persisted | nothing |
| The per-session payload | carries the path's environment and a key helper reference | the payload file holds no credential value; one payload per session is overwritten, never accumulated |
| Verification and switch output | redacted before it is shown or logged | nothing |
| The existence test of a credential file (the cloud chain) | the file text is read to test that it is non-empty and discarded; the value is never returned, logged or persisted | nothing |
| Machine settings after a switch | a key helper reference, not the resolved value | the settings file and its backups never gain a literal that the previous settings did not already hold |

**The key helper.** The tool asks a command for a path's key at the moment it needs it. The command is the door `ahabase llm key PATH_ID`: it reads the path's reference, obtains the value through the safe as a bound consumer and writes it to its own standard output, a pipe to the tool, and nowhere else. The safe releases a value only to a consumer its owner has bound, so the helper works only after an **owner step**, listed here because it needs the Human at a terminal and cannot be done by a script or an agent:

| Owner step | Command | What it does | If skipped |
|------------|---------|--------------|------------|
| Bind the key helper to a path's reference, once per credential | `ahabase safe bind NAME /absolute/path/to/HELPER --prefix llm --prefix key` (the owner types the name to confirm), where HELPER is the **bound helper**: the `ahabase` door when the caller has no table of its own, otherwise the caller's own helper command (the program that answers `llm key`, see Two executables) | allows exactly this command to receive that value | the helper answers "not a bound consumer" and the path cannot authenticate; nothing is written |
| Enter the value, once per credential | `ahabase safe set NAME` (hidden prompt) | stores the value in the owner's store | the reference resolves to nothing |

**Two executables.** The key helper involves two programs that are the same only when the caller has no table of its own: the **runner** (`safe_executable`, the program that provides `safe run`, by default `ahabase` on PATH) and the **bound helper** (`executable`, the command that prints the key and that the owner binds). A caller whose provider table lives outside the package passes its own command as the helper, so the owner binds that command (`ahabase safe bind NAME /absolute/path/to/helper --prefix llm --prefix key`), while the runner stays the ahabase door. `verify_path` and `switch_path` take both and, when the caller names its own helper, obtain the token of a `safe://` path through the bound run, never by an in-process resolution that the consumer check would refuse; a caller that names no helper keeps the released in-process check with its `argv` and `safe`.

**The door as its own caller (direct use).** `ahabase llm` is a caller like any other, with no table of its own beyond the instance's variants file, so it names ITSELF as both programs: `path-verify`, `path-switch`, `session-env` and `key` pass the door's absolute path as `executable` (the bound helper) and, where the library takes it, as `safe_executable` (the runner). The owner therefore binds the door once per credential (`ahabase safe bind NAME /absolute/path/to/ahabase --prefix llm --prefix key`) and `ahabase llm path-verify PATH` works on a `safe://` path with no evolucean code. The door resolves its own path from the command it was started as, else the command beside the interpreter, else PATH. **`ahabase llm session-launch PATH_ID [CLAUDE_ARGS]...`** writes the owner-only payload (it holds the key helper command, never a value) and replaces the process with `claude --settings FILE CLAUDE_ARGS`; the machine's settings are not touched, an unknown path or a missing `claude` is refused with the file named so the Human can launch by hand.

**The provider ladder is instance data.** The package ships the native routes only; every other path is an entry of `_config/llm-paths-variants.yaml` (outside git, one file per instance) that the door and any caller read through `load_variants`. An entry under `paths:` carries `status: available`, `base_url`, `model`, `auth` (a `safe://NAME` reference, an `env:NAME` variable, `oauth` or `aws-credentials`; a literal is refused), `description`, and the optional `tier_models`, `key_helper`, `provider`, `pin_model`, `context_window` and, for the cloud route, `region` and `aws_profile`; no key the library reads from a definition is dropped by the loader (a census test over the library source pins this, so a new key read without a loader entry turns it red). The file holds references and public provider facts, never a secret value.

**Resolution transport.** The safe's plain `resolve` and `get` do not check whether the caller is a bound consumer; only `safe run` (or a direct call of the consumer check) does. The helper therefore obtains the value through `safe run --env VAR=safe://NAME -- ahabase llm key PATH_ID --emit`, where the bound command is the inner one (its first two arguments are `llm key`, the prefix the owner bound) and the outer `ahabase llm key PATH_ID` passes the inner's standard output through and the value reaches only that child's environment, or it calls the consumer check itself before resolving; it never calls `resolve` directly. R3c measures the exact invocation against a real safe in an isolated home directory before the form is relied on; if the prefix-restricted binding does not cover it, the bind form is amended here and the Human is asked once for the exact binding.

**Residual.** `ahabase` is a dispatcher, so the prefix `llm key` is the only narrowing of the binding: the door `ahabase llm key` must never grow an option or a path id that prints another entry's value, and a test asserts that its argument list accepts exactly one path id and the single flag `--emit`, nothing else.

The ported modules never print, log or persist a credential value. A canary test under `tests/llm` plants a recognisable value in each source and asserts it appears in no output, no log line and no file.

## Platform dispatch (both operating systems)

The moving code uses the standard library only (`urllib` for the requests, `subprocess`, `pathlib`, `tempfile`), so the package gains no dependency. What differs between macOS and Windows is isolated in one place each:

| Difference | Where | Handling |
|------------|-------|----------|
| the presence of the subscription login | `paths` | on macOS the login lives in the system keychain (presence only, through the `security` command); elsewhere the credentials file is checked; both answer presence, never the value |
| the tool's binary | `verify` | located with `shutil.which`, not by a fixed path; a missing binary is a `cli` failure class, not a crash |
| the key helper command | `paths`, `session` | run through the platform shell, as the tool itself runs it |
| file mode of the payload and the atomic write | `switch`, `session` | `os.replace` on both; the owner-only mode is applied where the platform has one (POSIX) and the payload directory is owner-only where it has not; the dispatch follows the package's `_posix.py` / `_win.py` pattern |

The CI matrix of the package (macOS, Windows, Ubuntu, Python 3.11 as the oldest supported) runs `tests/llm` with the rest of the suite.

## Seam contract (frozen)

- **Type:** a Python import (library seam) for the method, and the door `ahabase llm ...` behind the one registry for people and sessions.
- **Surface (named functions per module, no module dump):**
  - `ahabase.llm.paths`: `known_paths(builtin=None, variants_file=None)`, `rescue_order(variants_file=None)`, `resolve_auth(spec, env=None)`, `resolve_key(definition, env=None)`, `current_path(...)`, `pinned_model(...)`, `pin_error(...)`, `subscription_login_present()`, `bedrock_credentials_present()`.
  - `ahabase.llm.discovery`: `discover(...)`, `assess_local_availability(...)`, `load_registry()`, `save_registry(...)`, `load_machine_availability()`, `get_registry_path()`, `machine_id()`.
  - `ahabase.llm.verify`: `verify_path(...)`, `verify_path_family(...)`, `classify_failure(detail)`, `first_working_path(...)`, `prove_launch(...)`, `reachable(base_url, ...)`.
  - `ahabase.llm.switch`: `switch_path(target, ..., guard=None)`, `list_backups()`, `restore_backup(...)`, `write_settings_atomically(...)`, `redacted(...)`.
  - `ahabase.llm.session`: `session_env(path_id, ..., env_overrides=None)`, `session_env_out(path_id, *, epic, ...)`, `session_env_check(...)`, `resolve_compact_window` is NOT in the surface (it stays with the method and passes its value in `env_overrides`).
- **Door commands (behind the one registry):** `ahabase llm path-list`, `path-verify`, `path-switch`, `path-restore`, `discover`, `session-env`, `key PATH_ID`.
- **Authentication contract:** a path's auth is `safe://NAME`, `env:NAME` (a variable injected by the safe), `oauth` (the subscription login) or a key helper command; a literal is refused.
- **Floor:** the first released ahabase tag that carries this package (the method pins `ahabase>=X` at a released tag, never a branch or a working tree).
- **Custody boundary:** implementations move; per-instance data (the variants file, the registry, backups), the provider entries of the ladder, model selection and the catalogue, hook guidance, proxy and service management, local model runtimes, telemetry, the ambient backend and the collaboration wiring stay with the method. The method keeps its module paths and delegates the moved functions to the package (definition-site delegation), so no importer changes.


## Notes on the surface (not part of the frozen contract text)

- Keyword-only parameters with defaults may be added to a surface function without reopening the contract; the positional forms named in the contract keep binding. The ported code adds `argv=` and `safe=` to `resolve_auth` and `resolve_key`, and `builtin=` and `variants_file=` to `current_path`, `assess_local_availability` and `discover`.
- A method wrapper that calls `resolve_auth(spec, env)` directly, outside a command the owner bound, is refused for a `safe://` spec (the call fails closed); the method reaches a `safe://` credential only through the door (`ahabase llm key`) or by launching under `safe run`.
- Functions may be added beside the frozen list without reopening the contract. The ported code adds `failure_class(verdict)` to `ahabase.llm.verify`: the one mapping from a failed verdict to its class (`config` for a definition error or a credential the command may not read, otherwise the text classification), used by the search and by the door.
- `KEYCHAIN_SERVICE` and the tool's settings and credentials locations under the home directory are the tool's own runtime identifiers, not instance details; they are deliberate.

## Tests and red controls

Unit tests under `tests/llm`, one file per module. Each moved function has a test; planted mutants turn the tests red (classification order, the verification gate before a switch, the redaction, the backup before a write, the refusal of a literal). A static check asserts that nothing under `ahabase.llm` imports a method package. The credential canary is a real test (see the credential flow).

## Structure

`src/ahabase/llm/` - `paths.py` (definitions, kinds, variants loader, authentication, ladder, identity), `discovery.py` (introspection, availability, registry), `verify.py` (preflight, launch proof, classification, first working path, reachable), `switch.py` (verified switch, atomic write, backups, restore, redaction), `session.py` (payload, check, key helper). The door is registered through the entry-point group `ahabase.plugins`. Tests: `tests/llm/test_<module>.py`, one file per module, plus `tests/llm/test_credentials_canary.py` and `tests/llm/test_no_method_import.py`.

## Template

```
ahabase llm path-list
ahabase llm discover
ahabase llm path-verify PATH_ID
ahabase llm path-switch PATH_ID --confirm
ahabase llm path-restore [--latest | BACKUP] --confirm
ahabase llm session-env PATH_ID --out FILE
ahabase llm key PATH_ID
```

## Example

```
$ ahabase llm discover
subscription: available (login present)
gateway: not available (no listener)
$ ahabase llm path-verify subscription
subscription: ok
$ ahabase llm path-switch gateway --confirm
refused: gateway failed verification (class: unavailable) - settings unchanged
$ ahabase llm path-switch subscription --confirm
backup written; settings now point at subscription
$ ahabase llm path-restore --latest --confirm
restored the previous settings
```

## Related

- [00-ahabase-llm-ontology-index](00-ahabase-llm-ontology-index) - the vocabulary
- [AHABASE-LLM](AHABASE-LLM) - the subepic identity
- [implementation-ahabase-safe-blueprint](implementation-ahabase-safe-blueprint) - the safe whose references the paths hold

---
