"""Access paths (AHA-0024 R3a): definitions, authentication, ladder, identity."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from ahabase.llm import paths


class FakeSafe:
    """A safe that binds exactly one command; it records what was asked."""

    def __init__(self, value="the-secret", bound=("/bin/ahabase",)):
        self.value, self.bound, self.asked = value, bound, []

    def check_consumer(self, name, argv):
        self.asked.append((name, list(argv)))
        if argv[0] not in self.bound:
            from ahabase.safe import SafeError
            raise SafeError(f"{argv[0]} is not a bound consumer of {name!r}")
        return {"path": argv[0]}

    def get(self, name):
        return self.value


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Point every location the module reads at a temporary directory."""
    monkeypatch.setattr(paths, "SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr(paths, "CREDENTIALS_PATH", tmp_path / ".credentials.json")
    monkeypatch.setattr(paths, "AWS_CREDENTIALS_PATH", tmp_path / "aws" / "credentials")
    monkeypatch.setattr(paths, "AWS_SSO_CACHE_PATH", tmp_path / "aws" / "sso")
    monkeypatch.setenv("AHABASE_WORKSPACE", str(tmp_path / "ws"))
    for name in ("CLAUDE_CODE_USE_BEDROCK", "ANTHROPIC_MODEL", "AWS_ACCESS_KEY_ID"):
        monkeypatch.delenv(name, raising=False)
    return tmp_path


def write_variants(home: Path, text: str) -> Path:
    path = home / "variants.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# --- the form of an auth spec -------------------------------------------------

@pytest.mark.parametrize("spec,form", [
    ("", "none"), ("oauth", "oauth"), ("aws-credentials", "aws-credentials"),
    ("env:KEY", "env"), ("safe://NAME", "safe"), ("sk-looks-like-a-token", "literal"),
])
def test_auth_form(spec, form):
    assert paths.auth_form(spec) == form


def test_a_literal_credential_is_refused_without_echoing_it():
    canary = "sk-CANARY-literal-0123456789"
    with pytest.raises(paths.AuthError) as raised:
        paths.resolve_auth(canary)
    assert canary not in str(raised.value)
    with pytest.raises(paths.AuthError) as raised:
        paths.check_definition("p", {"auth": canary})
    assert canary not in str(raised.value) and "p" in str(raised.value)


# --- definitions and variants -------------------------------------------------

def test_only_the_native_routes_ship_with_the_package(home):
    assert sorted(paths.known_paths()) == ["bedrock", "claude-pro"]
    assert paths.known_paths()["claude-pro"]["auth"] == "oauth"


def test_the_callers_provider_entries_are_merged_and_checked(home):
    extra = {"gateway": {"base_url": "http://localhost:1", "model": "m", "auth": "env:K"}}
    assert "gateway" in paths.known_paths(builtin=extra)
    with pytest.raises(paths.AuthError):
        paths.known_paths(builtin={"bad": {"base_url": "x", "auth": "sk-literal-credential"}})


def test_variants_load_only_available_entries_with_optional_fields(home):
    file = write_variants(home, "paths:\n"
        "  a: {status: available, base_url: 'http://a', model: m, auth: 'env:A', key_helper: 'echo k', pin_model: true}\n"
        "  b: {status: disabled, base_url: 'http://b', model: m, auth: 'env:B'}\n")
    loaded = paths.load_variants(file)
    assert list(loaded) == ["a"]
    assert loaded["a"]["key_helper"] == "echo k" and loaded["a"]["pin_model"] is True


def test_a_variant_with_a_literal_credential_is_refused_naming_the_path(home):
    file = write_variants(home, "paths:\n  leak: {status: available, base_url: 'http://a', model: m, auth: 'sk-CANARY-in-a-file'}\n")
    with pytest.raises(paths.AuthError) as raised:
        paths.load_variants(file)
    assert "leak" in str(raised.value) and "sk-CANARY" not in str(raised.value)


def test_a_missing_or_broken_variants_file_reads_as_empty(home):
    assert paths.load_variants(home / "none.yaml") == {}
    assert paths.load_variants(write_variants(home, ": : not yaml [")) == {}


def test_later_sources_override_earlier_ones(home):
    file = write_variants(home, "paths:\n  claude-pro: {status: available, base_url: '', model: x, auth: oauth, description: mine}\n")
    assert paths.known_paths(variants_file=file)["claude-pro"]["description"] == "mine"


def test_the_default_variants_location_follows_the_workspace(home):
    assert paths.variants_path() == home / "ws" / "_config" / paths.VARIANTS_FILENAME


# --- the ladder ---------------------------------------------------------------

def test_rescue_order_is_named_or_the_available_variants_in_file_order(home):
    named = write_variants(home, "meta: {rescue_order: [z, y]}\npaths:\n  a: {status: available}\n")
    assert paths.rescue_order(named) == ["z", "y"]
    unnamed = write_variants(home, "paths:\n  a: {status: available}\n  b: {status: off}\n  c: {status: available}\n")
    assert paths.rescue_order(unnamed) == ["a", "c"]
    assert paths.rescue_order(home / "absent.yaml") == []


# --- the session pin ----------------------------------------------------------

def test_pin_error_names_the_fix_and_pinned_model_follows_the_flag():
    assert paths.pin_error("p", {}) is None
    assert "URL" not in (paths.pin_error("p", {"pin_model": True, "base_url": "u", "model": "m"}) or "")
    assert "endpoint" in paths.pin_error("p", {"pin_model": True, "model": "m"})
    assert "needs a model" in paths.pin_error("p", {"pin_model": True, "base_url": "u"})
    assert paths.pinned_model({"model": "m"}) == ""
    assert paths.pinned_model({"pin_model": True, "model": "m"}) == "m"
    assert paths.pinned_model({"pin_model": True, "model": "m"}, "other") == "other"


# --- resolving authentication -------------------------------------------------

def test_env_oauth_aws_and_empty_resolve(home):
    assert paths.resolve_auth("env:K", {"K": "v"}) == "v"
    assert paths.resolve_auth("env:K", {}) is None
    assert paths.resolve_auth("oauth") is None
    assert paths.resolve_auth("aws-credentials") is None
    assert paths.resolve_auth("") is None


def test_a_safe_reference_resolves_only_for_the_bound_command(home):
    fake = FakeSafe()
    assert paths.resolve_auth("safe://NAME", argv=["/bin/ahabase", "llm", "key"], safe=fake) == "the-secret"
    assert fake.asked[-1][0] == "NAME"
    with pytest.raises(paths.AuthError) as raised:
        paths.resolve_auth("safe://NAME", argv=["/tmp/other"], safe=fake)
    assert "the-secret" not in str(raised.value)


def test_the_running_command_is_the_default_consumer(home, monkeypatch):
    command = os.path.abspath("/abs/ahabase")  # the platform's own absolute form
    fake = FakeSafe(bound=(command,))
    monkeypatch.setattr(sys, "argv", [command, "llm", "path-verify", "x"])
    assert paths.resolve_auth("safe://N", safe=fake) == "the-secret"
    assert fake.asked[-1][1] == [command, "llm", "path-verify", "x"]


def test_a_relative_command_is_made_absolute_against_the_working_directory(home, monkeypatch, tmp_path):
    fake = FakeSafe(bound=(str(tmp_path / "ahabase"),))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["ahabase", "llm", "path-verify", "x"])
    assert paths.resolve_auth("safe://N", safe=fake) == "the-secret"
    assert fake.asked[-1][1][0] == os.path.abspath("ahabase") == str(tmp_path / "ahabase")


def test_a_key_helper_supplies_the_key(home):
    helper = f'"{sys.executable}" -c "print(chr(107)+chr(101)+chr(121))"'
    assert paths.resolve_key({"key_helper": helper}) == "key"
    assert paths.resolve_key({"key_helper": f'"{sys.executable}" -c "import sys; sys.exit(3)"'}) is None
    assert paths.resolve_key({"auth": "env:K"}, {"K": "v"}) == "v"


# --- presence of the tool's own credentials -----------------------------------

def test_the_subscription_login_is_found_by_its_file(home, monkeypatch):
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: False)
    assert paths.subscription_login_source() is None
    paths.CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
    assert paths.subscription_login_source().startswith("file:")
    assert paths.subscription_login_present()


def test_the_subscription_login_is_found_in_the_macos_keychain(home, monkeypatch):
    monkeypatch.setattr(paths.sys, "platform", "darwin")
    monkeypatch.setattr(paths, "_keychain_login_present", lambda *a, **k: True)
    assert paths.subscription_login_source() == f"macOS keychain: {paths.KEYCHAIN_SERVICE}"
    monkeypatch.setattr(paths.sys, "platform", "linux")
    assert paths.subscription_login_source() is None  # no file, and the keychain leg is macOS only


def test_the_cloud_chain_legs_are_checked_in_order_by_presence(home):
    assert paths.bedrock_credentials_source({}) is None
    assert paths.bedrock_credentials_source({"AWS_ACCESS_KEY_ID": "x"}).startswith("env:")
    paths.AWS_CREDENTIALS_PATH.parent.mkdir(parents=True)
    paths.AWS_CREDENTIALS_PATH.write_text("  \n", encoding="utf-8")
    assert paths.bedrock_credentials_source({}) is None  # blank file proves nothing
    paths.AWS_CREDENTIALS_PATH.write_text("[default]\nvalue\n", encoding="utf-8")
    assert paths.bedrock_credentials_source({}).startswith("file:")
    paths.AWS_CREDENTIALS_PATH.unlink()
    paths.AWS_SSO_CACHE_PATH.mkdir()
    (paths.AWS_SSO_CACHE_PATH / "a.json").write_text("{}", encoding="utf-8")
    assert paths.bedrock_credentials_source({}).startswith("sso cache:")


# --- the identity in force ----------------------------------------------------

LADDER = {
    "gw-a": {"base_url": "http://gw", "model": "ma", "auth": "env:K", "tier_models": {"SONNET": "ma"}},
    "gw-b": {"base_url": "http://gw", "model": "mb", "auth": "env:K"},
    "direct": {"base_url": "http://direct", "model": "m", "auth": "env:K"},
    "cloud-m": {"base_url": "", "model": "model-x", "auth": "aws-credentials"},
}


def test_identity_in_force(home):
    cur = lambda env: paths.current_path(env, builtin=LADDER)
    assert cur({"ANTHROPIC_BASE_URL": ""}) == "claude-pro"
    assert cur({"ANTHROPIC_BASE_URL": "http://direct"}) == "direct"
    assert cur({"ANTHROPIC_BASE_URL": "http://elsewhere"}) == "custom"
    assert cur({"ANTHROPIC_BASE_URL": "http://gw", "ANTHROPIC_DEFAULT_SONNET_MODEL": "mb"}) == "gw-b"
    assert cur({"ANTHROPIC_BASE_URL": "http://gw", "ANTHROPIC_DEFAULT_SONNET_MODEL": "ma"}) == "gw-a"
    assert cur({"ANTHROPIC_BASE_URL": "http://gw"}) == "gw-a"  # first candidate when nothing matches
    assert cur({"CLAUDE_CODE_USE_BEDROCK": "1"}) == "bedrock"
    assert cur({"CLAUDE_CODE_USE_BEDROCK": "true", "ANTHROPIC_MODEL": "model-x"}) == "cloud-m"


def test_a_settings_key_outranks_the_process_environment(home, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_USE_BEDROCK", "1")
    assert paths.current_path({"CLAUDE_CODE_USE_BEDROCK": ""}) == "claude-pro"
    assert paths.current_path({}) == "bedrock"


def test_settings_env_reads_the_settings_file(home):
    assert paths.settings_env() == {}
    paths.SETTINGS_PATH.write_text(json.dumps({"env": {"A": "b"}}), encoding="utf-8")
    assert paths.settings_env() == {"A": "b"}
    paths.SETTINGS_PATH.write_text("not json", encoding="utf-8")
    assert paths.settings_env() == {}


def test_the_variants_loader_keeps_every_optional_field_of_a_ladder_entry(tmp_path):
    """A provider ladder in instance data loses no field the library reads (AHA-0028)."""
    from ahabase.llm import paths as p
    variants = tmp_path / "variants.yaml"
    variants.write_text(
        "paths:\n  full:\n    status: available\n    base_url: https://x.example\n    model: m\n"
        "    auth: safe://NAME\n    description: d\n    tier_models: {sonnet: s}\n    provider: prov\n"
        "    pin_model: m\n    context_window: 123456\n    region: eu-central-1\n    aws_profile: prof\n")
    entry = p.load_variants(variants)["full"]
    assert entry["context_window"] == 123456 and entry["tier_models"] == {"sonnet": "s"}
    assert entry["provider"] == "prov" and entry["pin_model"] == "m"
    assert entry["region"] == "eu-central-1" and entry["aws_profile"] == "prof"


def test_every_definition_key_the_library_reads_survives_the_loader():
    """The census as a test: a key read from a definition and dropped by the loader is a silent loss (AHA-0028)."""
    import re
    from pathlib import Path
    from ahabase.llm import paths as p
    source = "".join(f.read_text() for f in Path(p.__file__).parent.glob("*.py"))
    read = set(re.findall(r'definition(?:\.get\(|\[)"(\w+)"', source))
    base = {"status", "base_url", "model", "auth", "description"}
    kept = base | {"tier_models", "key_helper", "provider", "pin_model", "context_window", "region", "aws_profile"}
    assert read - {"status"} <= kept, sorted(read - kept)
    src = Path(p.__file__).read_text()
    for name in kept - base:
        assert f'"{name}"' in src[src.index("def load_variants"):src.index("def native_paths")], name
