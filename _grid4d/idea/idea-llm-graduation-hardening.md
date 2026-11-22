# idea: harden the graduated llm module before the next llm step

**Status:** open
**Origin:** architecture review of the package, 2026-11-09 (robustness, maintainability, consistency, minimalism), weighed against [AHABASE](AHABASE) and [AHABASE-Priorities](AHABASE-Priorities)
**Addresses:** [issue-llm-variants-file-fails-quietly](issue-llm-variants-file-fails-quietly), [issue-llm-key-helper-runs-through-a-shell](issue-llm-key-helper-runs-through-a-shell), [issue-llm-tool-paths-bypass-the-config-door](issue-llm-tool-paths-bypass-the-config-door)
**Serves:** [AHABASE-Priorities](AHABASE-Priorities) row 2 (llm)

One story, three points, each with a red control:

1. **The variants file fails closed.** A missing file stays "no variants". An unreadable file or a YAML error raises a named error (the file, the line from `yaml.YAMLError`, the remedy), the same policy as the safe's manifest. `ahabase llm path-list` and `doctor` report it instead of listing native routes only. Red control: a file with a syntax error must not list zero instance paths silently.
2. **The key helper as an argument list.** Accept `key_helper` as a list (`["ahabase", "safe", "get", "NAME"]`) and run it without a shell; keep a string form only for the host tool's own `apiKeyHelper` contract, split with `shlex` on POSIX and refused with a clear message on Windows, or migrated by `ladder-init`. Report a failing helper (exit code, first stderr line, never the output) instead of returning the same `None` as an empty key.
3. **Host-tool paths through the config door.** Replace the import-time `SETTINGS_PATH` and `CREDENTIALS_PATH` with functions of the config door (`get_tool_settings_path()` or a `tool_home` setting with the current default), read at call time. Tests then set the setting instead of patching module constants.

Why one story: all three are in the code that just graduated, and the priorities rank llm second; fixing them before the proxy graduates keeps the proxy from building on them.
