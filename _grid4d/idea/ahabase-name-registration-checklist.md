# ahabase Name Registration Checklist

> The name `ahabase` was chosen because it is unused in software; this checklist holds it everywhere the product will need it - domains, package registries, installation platforms, community surfaces - with the measured state and the order to claim them.

## Measured state (2026-10-30)

| Place | State |
|---|---|
| ahabase.com | owned by the Human (registered 2017, renewed to 2027-01, parked on GitHub Pages) - canonical |
| ahabase.org | owned by the Human - community identity |
| ahabase.dev / ahabase.app | taken by others, dormant (nothing hosted) |
| ahabase.io / ahabase.net | free - cheap defensive redirects |
| GitHub org `ahabase` | ours (the repositories already live under it) |
| PyPI `ahabase` | free (404 on the registry API) |
| crates.io `ahabase` | free (404 on the registry API) |
| npm `ahabase` | free (404 on the registry API) |
| Docker Hub `ahabase` | free (404 on the user API) |

## Where the name matters

### Web

- `ahabase.com` canonical, `docs.ahabase.com` for documentation (GitHub Pages is enough).
- `/.well-known/security.txt` on the canonical domain - the standard place vulnerability reports look for.
- Status page when a service exists worth a status page.

### Installation platforms (the product's doors)

- **crates.io `ahabase`** - critical for the Rust CLI. A crate name is held by publishing, not by reserving: publish the first public 0.x as soon as the code is public. Decide the sub-crate scheme (`ahabase-cli`, `ahabase-core`, ...) before first publish, or stay one crate and keep the name-space tight.
- **PyPI `ahabase`** - the transitional Python door; a 0.0.1 with a README holds the name.
- **npm `ahabase`** - a stub, if a Node/MCP distribution ever ships.
- **Homebrew** - repository `ahabase/homebrew-tap` under the org (`brew install ahabase/tap/ahabase`); `homebrew-core` only once its popularity criteria are met.
- **winget** - publisher namespace `ahabase`, package id `ahabase.ahabase`; claimed by the first submission to winget-pkgs.
- **scoop** - repository `ahabase/scoop-bucket`, manifest `ahabase.json`.
- **Chocolatey** - package `ahabase` on the community feed.
- **Containers** - Docker Hub organization `ahabase` plus `ghcr.io/ahabase` (comes with the GitHub org); image `ahabase-mcp` for the MCP door.
- **MCP registry** - entry `ahabase`: the address AI tools will search for.

### Community

- GitHub Discussions as the primary forum (free, under the org) before any chat server.
- Matrix `#ahabase:matrix.org`, Bluesky / X handles, Reddit r/ahabase - defensively, when there is content; empty channels cost more than they return.

### Identity and trust

- **Release signing key** (minisign or sigstore) - long-term the name binds to the key more than to the domain; publish the public key from day one of binaries.
- GitHub Security Advisories (GHSA) - automatic with the org.
- OpenSSF best-practices badge when the criteria are reachable.
- **Trademark** (EUIPO / USPTO) once the project carries commercial weight - the only real legal defense; domains and handles are the cheap layer.

## Order

1. **Now, free under the org:** repositories `homebrew-tap`, `scoop-bucket`, `.github` (community health files). Domains `.io` / `.net` as redirects (the Human's purchase).
2. **With the first public release:** crates.io (real publish), PyPI 0.0.1, npm stub, Docker Hub org + MCP image, brew formula, winget submission.
3. **Earned later:** homebrew-core, social accounts with content, trademark.

All registrations (accounts, payments, publishes under the owner's credentials) are the Human's step; the project's part is the artifacts - winget manifest, brew formula, this checklist.

## Related

- [open-source-business-models](open-source-business-models) - why the mechanism is open and what is protected instead
- [documentation-structure-for-a-rust-ahabase](documentation-structure-for-a-rust-ahabase) - the distribution chapter names the same doors
