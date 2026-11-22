# The safe: a tutorial

> Who holds your secrets, who reads them, and how a tool receives a value
> without the value ever lying around in a file, a profile or a command
> line.

Everything below runs with generic names - `issue-tracker` is the secret,
`issue-tool` the program that consumes it, `git.example.com` the git host.
Substitute your own at the terminal; nothing real belongs in a document.

## What the safe is

One interface for secrets. Configuration holds a **reference**
(`safe://issue-tracker`), never a value; the **manifest** records names
and metadata only; the **value** lives in your own store (the operating
system's keychain by default) and leaves it only through the surfaces the
safe designs - the environment of one bound child process, git's
credential-helper pipe, or a target the safe alone writes (a gh login, a
helper's keychain item). No document, no log and no agent context ever
holds a value; a person reads one only through an explicit reveal, at a
terminal.

## The owner's walkthrough

The owner is you, a person at an interactive terminal. Every step that
touches a value is gated on that - the safe refuses it in a script or an
agent's shell, because that is exactly where a value must not travel.

### 1. Store a secret

```bash
ahabase safe set issue-tracker --purpose "issue tracker" --expires 2027-01-31
# value for issue-tracker:            # typed hidden, confirmed twice
stored issue-tracker in keyring (reference: safe://issue-tracker)
```

From a pipe (`printf '%s' "$TOKEN" | ahabase safe set ...`) the value is
read from stdin - hidden input is for terminals only. Configuration now
says `safe://issue-tracker` and holds no value.

### 2. See what the safe holds

```bash
ahabase safe list
issue-tracker: store=keyring, purpose=issue tracker, expires=2027-01-31; targets: none; consumers: none
```

Names, metadata, targets, consumers - never a value. `ahabase doctor`
adds the store's health: missing values, expiring secrets, targets that
stopped answering.

### 3. Give a fixed-purpose tool the value (bind, then run)

A tool that takes its destination from its **own configuration** is bound
once, by absolute path:

```bash
ahabase safe bind issue-tracker "$(command -v issue-tool)"
# type the name 'issue-tracker' to bind: issue-tracker
bound /usr/local/bin/issue-tool to issue-tracker (valid while the file is unchanged)
```

From then on the tool receives the value only as one environment variable
of one child process - and nothing else of yours:

```bash
ahabase safe run --env ISSUE_TOKEN=safe://issue-tracker -- issue-tool search "project = X"
```

The child sees `PATH`, locale, terminal, proxy and certificate settings,
the variables you named with `--keep`, and `ISSUE_TOKEN` - no other
exported value. A tool that is not bound gets nothing (below).

Shells, interpreters and general-purpose network tools (`curl`, `gh`,
`git`, `ssh`) cannot be bound - their arguments say where they go, so a
binding would hand the value to whatever arrives. They get their value
through the next two surfaces instead.

### 4. Give git the credential (the helper)

git asks a credential helper; the safe **is** one, read-only over its
store. Two config lines wire it for one host, and the OS keychain helper
keeps serving every other host:

```bash
git config --global credential.https://git.example.com.helper ""
git config --global --add credential.https://git.example.com.helper "!ahabase safe credential"
```

The empty entry resets git's helper list for that host only - the OS
keychain helper is then not consulted for it at all, and it keeps serving
every other host. The second line must be `--add`: a plain set would
replace the empty entry, and the reset would be lost. From now on
`git push`, `fetch`, `clone` over https to that host ask the safe:

```
protocol=https
host=git.example.com          # git's request, on the helper's stdin
        ↓
username=42                   # the safe's answer, on stdout to git only
password=...the value...
```

The safe answers only a host an entry's `git-credential` target names -
see step 5 - so a request for any other host falls through to the next
helper, untouched. When git reports a successful authentication it calls
`store` on every helper; the safe answers:

```
the safe stores nothing from git - a value enters only through
`ahabase safe set`, the owner's step at a terminal
```

and keeps the store unchanged: values enter through `set` only, ever.
`erase` behaves the same.

### 5. Tell the safe which host is whose (targets)

The helper's host scoping comes from a **target** on the entry - the same
declaration that names a gh login:

```bash
ahabase safe target add issue-tracker git-credential git.example.com 42
ahabase safe target add issue-tracker gh-login                    # gh's login, github.com by default
# each: type the name 'issue-tracker' to add a target to: issue-tracker
target git-credential git.example.com/42 added to issue-tracker - `safe set issue-tracker` writes it, `safe refresh issue-tracker` rewrites it
```

A target is a copy in a tool's own store that the safe writes and keeps
current: the `git-credential` target names the host and account the
helper answers for (the custody route - the safe writes the item through
`git credential approve`), the `gh-login` target is gh's login (written
from the safe's value, verified by read-back, never printed). One entry
per account: a second account on the same host is a second secret with
its own target - never a second value under one name.

gh keeps one login per host in one config directory, so a second account
on the same host is the distinct kind `gh-login-account`, naming the
account:

```bash
ahabase safe target add github-alice gh-login-account github.com alice
ahabase safe target add github-bob   gh-login-account github.com bob
```

Each account's login then lives in its own gh config directory,
`<workspace>/_config/ahabase-gh/<account>` (owner-only); the safe is its
only writer, and a caller selects the account with
`GH_CONFIG_DIR=$(ahabase safe gh-config-dir <account>) gh ...` - the
command is the contract, callers never form the path themselves. The
token stays in the keyring: when gh finds no keyring it writes the token
in plain text into its config files - the safe finds its value there,
removes the file and refuses the refresh. A distinct kind rather than an
extra field on `gh-login`: an older ahabase refuses an unknown kind,
where it would ignore an unknown field and write the account's token
into the host's default login.

The directory isolates which login gh *uses*, not where the token is
*stored*: gh's keyring entry is keyed by host and user, so a default gh
config that also knows the account reads the same keyring entry (measured:
a stale default entry of the account turned valid after the account
target's refresh), and `gh auth logout -u <account>` there removes the
token the account target relies on - `safe refresh` writes it back.

A `git-credential` target can also be declared **scope-only**, for the
pure call-model - the safe answers for the host through the helper, and
no tool store holds a second copy of the value anywhere:

```bash
ahabase safe target add issue-tracker git-credential git.example.com 42 --no-copy
# type the name 'issue-tracker' to add a target to: issue-tracker
target git-credential git.example.com/42 added to issue-tracker (scope only) - the credential helper answers for the host; the safe maintains no copy
```

The helper still answers for the host - it reads the safe's stored value,
not a copy - and rotation then touches no tool store for that target:

```bash
printf '%s' "$NEW_TOKEN" | ahabase safe set issue-tracker
stored issue-tracker in keyring (reference: safe://issue-tracker)
scope target git-credential git.example.com/42 - no copy is maintained
```

`ahabase safe list` shows the variant as `git-credential
git.example.com/42 (no copy)`, and `ahabase safe target remove` matches
it with or without the flag. One target has one custody mode: re-declaring
an existing `git-credential` target with (or without) the flag converts it
(`converted to scope only` - a copy already written in the tool's store,
if any, stays until removed by hand), so the two modes never coexist on
one host. The flag is a `git-credential` option only:
a `gh-login` target is a copy by definition, with no scope role to
declare.

### 6. Prove the copy before the switch

Before removing an old copy, prove the safe holds the same value:

```bash
ahabase safe compare issue-tracker --env ISSUE_TOKEN
compare 'issue-tracker' with its current source? [Y/n]:
issue-tracker: same
```

`--file PATH` and `--git-remote REPO` compare against a file and the
credential in a repository's remote URL. The answer is `same`,
`different`, or which side is missing - never the value, never a
fingerprint. Remove the old copy only after `same`.

### 7. Rotate (one place)

Setting an existing name again is the rotation - the one place it
happens:

```bash
printf '%s' "$NEW_TOKEN" | ahabase safe set issue-tracker
stored issue-tracker in keyring (reference: safe://issue-tracker)
refreshed target git-credential git.example.com/42
refreshed target gh-login github.com
```

Every reachable target is rewritten from the new value and proven by
reading it back; a target that could not be reached is named, the exit
code says the rotation is not finished, and `ahabase safe refresh
issue-tracker` rewrites the targets once its cause is fixed. Nothing else
needs touching: consumers read the safe each run, git asks the helper.

### 8. Read a value by eye (the owner's window)

```bash
ahabase safe get issue-tracker --reveal
# type the name 'issue-tracker' to reveal: issue-tracker
...the value, on your terminal only...
```

This is the one deliberate read of a value - a person, at a terminal,
naming the secret. Without `--reveal` the command refuses; no document,
log or agent transcript ever carries what it prints.

### 9. Remove what you no longer need

Each removal is the owner's step at a terminal, like the binding it
undoes:

```bash
ahabase safe unbind issue-tracker "$(command -v issue-tool)"
# type the name 'issue-tracker' to unbind: issue-tracker
unbound /usr/local/bin/issue-tool from issue-tracker
ahabase safe target remove issue-tracker gh-login
# type the name 'issue-tracker' to remove a target from: issue-tracker
removed target gh-login github.com from issue-tracker
ahabase safe delete issue-tracker
# type the name 'issue-tracker' to delete: issue-tracker
deleted issue-tracker
```

`delete` removes the entry and its stored value together; other secrets,
their targets and their bindings are untouched. Remove a binding or a
target only after the consumer or tool that needed it is off - what
removes the value from a running workflow is rotation (step 7), not
deletion.

## The user's walkthrough

You are a seat on the machine - an agent session, a service, a teammate
who is not the owner. The safe gives you three things to call and
nothing to store.

**Call the references.** Configuration hands you `safe://issue-tracker`;
the owner has wired the rest. git authenticates by itself (the helper);
gh runs on the safe's login; the programs you run are bound consumers
already. You never copy a value, and you never need one.

**Run a bound consumer through the safe.** The wrapper is the whole
interface:

```bash
ahabase safe run --env ISSUE_TOKEN=safe://issue-tracker -- issue-tool search "project = X"
```

**Expect refusals, and read them.** The safe fails closed - every
refusal names the command that proceeds. The ones you will meet:

- An unbound tool, or a bound tool called directly:

  ```
  Error: '/usr/local/bin/issue-tool' is not a bound consumer of 'issue-tracker' - nothing resolved; if it should receive it, its owner runs: ahabase safe bind issue-tracker /usr/local/bin/issue-tool
  ```

  You cannot fix this one - binding is the owner's step. Route the need
  to the owner; never route around the safe.

- A binding that no longer matches (the tool was updated, replaced,
  moved out of its package):

  ```
  Error: '/usr/local/bin/issue-tool' changed since it was bound (an update, or a replacement) - if the change is yours: ahabase safe bind issue-tracker /usr/local/bin/issue-tool
  ```

- The helper answering nothing (git then asks the next helper or
  prompts; a stderr notice from the safe names the remedy):

  ```
  safe credential: secret 'issue-tracker' is in the manifest but not in its store 'keyring' - the helper answers nothing until its owner stores it: ahabase safe set issue-tracker
  ```

  Again the owner's step. A missing value is never papered over with an
  old copy from somewhere else.

What you never do: put a value in a file, a profile, a command line, a
URL, a settings export or a chat message. If a workflow seems to need
exactly that, it needs a bound consumer or a target instead - file the
friction; the safe's answer to "where do I keep this token?" is always
"nowhere but the safe".
