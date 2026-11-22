"""The artifact containment gate suite (AHA-0029).

The exact built wheel and sdist are the substrate: the green test
scans them as built; the mutant family scans tampered COPIES (the
known string reintroduced, a different instance of the class, a rogue
member, a non-source file riding the package directory, a flipped
byte, a symlink member in either archive) so the arms are proven, not
assumed; the pattern table names its kind and passes the neutral
forms; the tombstone test holds every form of the retired id (bare,
letter-embedded, digit-embedded); the embedded-name test holds the
substring match; the artifact-level absence test proves no member of
either artifact carries an identifier byte; and the env-example
negative test holds the line that the arm guards corporate
identifiers, never environment-variable documentation (the Human's
option A).

The suite ships in the sdist, and the arm runs over every member with
no exemption: every fixture that matches a pattern is composed at
runtime, so no fixture byte in this file carries a full corporate
identifier (reviews F1 and F_d, AHA-0029).

Capability: artifact-containment
"""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from ahabase.artifact_containment import (
    CORPORATE_IDENTIFIER_PATTERNS,
    _redaction_findings,
    build_artifacts,
    scan_release,
    scan_sdist,
    scan_wheel,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PATTERNS = dict(CORPORATE_IDENTIFIER_PATTERNS)

# the retired id, composed so no suite byte carries it as one literal
RETIRED = "1148" + "5049"
# the public host: the pairing (host + id in one string) is the
# identifier, so the fixture pairs are assembled at runtime
_GH = "github.com "
# a non-reserved documentation address, assembled at runtime
_EMAIL = "someone@" + "example.corp"


@pytest.fixture(scope="session")
def artifacts(tmp_path_factory):
    """The exact built wheel and sdist of this tree, built once per session."""
    return build_artifacts(PROJECT_ROOT, tmp_path_factory.mktemp("artifacts"))


def _rewritten_wheel(wheel: Path, target: Path, edits: dict[str, bytes]) -> Path:
    """A copy of the wheel with edited member bytes (the mutant's carrier)."""
    with zipfile.ZipFile(wheel) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    with zipfile.ZipFile(target, "w") as copy:
        for info, data in entries:
            copy.writestr(info.filename, edits.get(info.filename, data))
        for name, data in edits.items():
            if name not in {info.filename for info, _ in entries}:
                copy.writestr(name, data)
    return target


def _rewritten_sdist(sdist: Path, target: Path,
                     edits: dict[str, bytes]) -> Path:
    """A copy of the sdist with edited member bytes (the mutant's carrier)."""
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        payloads = {m.name: (archive.extractfile(m).read() if m.isfile()
                             else b"") for m in members}
    with tarfile.open(target, "w:gz") as copy:
        for member in members:
            data = edits.get(member.name, payloads[member.name])
            if member.isfile():
                member.size = len(data)
                copy.addfile(member, io.BytesIO(data))
            else:
                copy.addfile(member)
    return target


def test_green_over_the_built_artifacts(artifacts):
    """The gate: both artifacts, all arms, zero findings on the story tree."""
    wheel, sdist = artifacts
    assert scan_release(wheel, sdist, PROJECT_ROOT) == []


def test_the_pattern_table_names_its_kinds():
    """Each pattern is a class: its kind matches, the neutral forms pass."""
    assert PATTERNS["keychain-account-id"].search(_GH + "12345678")
    assert PATTERNS["keychain-account-id"].search("github.com/" + "87654321")
    assert PATTERNS["keychain-account-id"].search('["gith' + 'ub.com", "12345678"]')
    assert not PATTERNS["keychain-account-id"].search("github.com octocat")
    assert not PATTERNS["keychain-account-id"].search("github.com")
    assert not PATTERNS["keychain-account-id"].search("github.com for 2026")
    assert PATTERNS["email-address"].search(_EMAIL)
    assert not PATTERNS["email-address"].search("@click.command()")
    assert PATTERNS["internal-github-host"].search("host github.tim" + "br.ai")
    assert PATTERNS["internal-username"].search("user kamen" + "skl")
    assert PATTERNS["internal-username"].search("kamen" + "skl_<company>")
    assert PATTERNS["internal-schema-prefix"].search("schema mmds" + "bx_x")
    assert PATTERNS["internal-schema-prefix"].search("xmmds" + "bx_y")


def test_the_tombstone_catches_every_form():
    """The retired id, in any form: bare, embedded in letters or digits."""
    bare = f'"account": "{RETIRED}"'.encode()
    letter_embedded = f"user x{RETIRED}y suffix".encode()
    digit_embedded = f"ref 9{RETIRED}3 end".encode()
    for mutant in (bare, letter_embedded, digit_embedded):
        findings = _redaction_findings("wheel", "ahabase/safe.py", mutant)
        assert [f.detail for f in findings] == ["line 1: pattern retired-account-id"]
    # beside the host (the list-literal form) the class pattern fires too
    paired = ('["gith' + 'ub.com", "' + RETIRED + '"]').encode()
    details = [f.detail for f in
               _redaction_findings("wheel", "ahabase/safe.py", paired)]
    assert details == ["line 1: pattern retired-account-id",
                       "line 1: pattern keychain-account-id"]
    # the report never echoes the value, and a different id is not the tombstone
    for findings in (_redaction_findings("wheel", "ahabase/safe.py", bare),
                     _redaction_findings("wheel", "ahabase/safe.py", paired)):
        assert RETIRED not in " ".join(str(f) for f in findings)
    near_miss = ("12345678 9" + "87654321").encode()
    assert _redaction_findings("wheel", "ahabase/safe.py", near_miss) == []


def test_the_embedded_internal_name_fires():
    """F_d: name_suffix is the login, not a new word - the substring arm fires."""
    fixture = ("acct github.com kamen" + "skl_<company>\n").encode()
    findings = _redaction_findings("sdist", "tests/test_safe.py", fixture)
    assert [f.detail for f in findings] == ["line 1: pattern internal-username"]


def test_the_reserved_domain_allowance():
    """RFC 2606/6761 domains are examples, not leaks; others stay findings."""
    fixture = (b'https://u:fixture%2Fpass%40word@git.example.com/o/r.git\n'
               b'# someone@' + b'example.corp is not documentation\n')
    findings = _redaction_findings("sdist", "tests/test_safe.py", fixture)
    assert [f.detail for f in findings] == [
        "line 2: pattern email-address"]


def test_the_env_example_stays_green():
    """The arm guards corporate identifiers, never env documentation (option A).

    The frame names the wheel's dist-info METADATA member: the README's
    content rides the wheel inside it (measured, review note 5898), so
    the wheel is the stronger substrate for this negative.
    """
    documented = ("Set env:NAME in CI to name the runner - a documented\n"
                  "transitional exception, never a default.\n").encode()
    assert _redaction_findings(
        "wheel", "ahabase-0.0.1.dist-info/METADATA", documented) == []


def test_no_identifier_bytes_ship_in_any_member(artifacts):
    """F1: not one member of either artifact carries an identifier literal."""
    wheel, sdist = artifacts
    needles = [RETIRED.encode(), b"tim" + b"br", b"kamen" + b"skl",
               b"mmds" + b"bx_", b"mn" + b"dm"]
    haystacks: list[bytes] = []
    with zipfile.ZipFile(wheel) as archive:
        haystacks += [archive.read(name) for name in archive.namelist()
                      if not name.endswith("/")]
    with tarfile.open(sdist, "r:gz") as archive:
        haystacks += [archive.extractfile(m).read() for m in archive.getmembers()
                      if m.isfile()]
    for needle in needles:
        assert all(needle not in data for data in haystacks), \
            "an identifier literal ships in an artifact member"


def test_mutant_known_string_reintroduced(artifacts, tmp_path):
    """The known instance: the string back in either docstring spot is RED."""
    wheel, _ = artifacts
    member = "ahabase/safe.py"
    with zipfile.ZipFile(wheel) as archive:
        original = archive.read(member)
    tampered = _rewritten_wheel(
        wheel, tmp_path / "known.whl",
        {member: original + b"\n    # e.g. " + b"github.com "
                       + RETIRED.encode() + b"\n"})
    findings = scan_wheel(tampered, PROJECT_ROOT)
    redaction = [f for f in findings if f.arm == "redaction"]
    names = {f.detail.rsplit("pattern ", 1)[1] for f in redaction}
    assert {"keychain-account-id", "retired-account-id"} <= names
    assert all(f.member == member for f in redaction)
    # the report never echoes the matched text
    assert all(RETIRED not in str(f) for f in findings)


def test_mutant_a_different_instance_of_the_class(artifacts, tmp_path):
    """The class, not the instance: a new id and an e-mail are both RED."""
    wheel, _ = artifacts
    member = "ahabase/config.py"
    with zipfile.ZipFile(wheel) as archive:
        original = archive.read(member)
    tampered = _rewritten_wheel(
        wheel, tmp_path / "class.whl",
        {member: original + b"\n# host " + b"github.com " + b"987654321\n"
                           + b"# owner someone@" + b"example.corp\n"})
    details = " ".join(f.detail for f in scan_wheel(tampered, PROJECT_ROOT)
                       if f.arm == "redaction")
    assert "keychain-account-id" in details
    assert "email-address" in details


def test_mutant_identifier_in_a_new_module(artifacts, tmp_path):
    """R3 (AHA-0030): the gate bites on the grown surface - an identifier
    literal seeded into the grid4d module's member is RED."""
    wheel, _ = artifacts
    member = "ahabase/grid4d.py"
    with zipfile.ZipFile(wheel) as archive:
        original = archive.read(member)
    tampered = _rewritten_wheel(
        wheel, tmp_path / "grown.whl",
        {member: original + b"\n# host github.com " + b"987654321\n"})
    details = " ".join(f.detail for f in scan_wheel(tampered, PROJECT_ROOT)
                       if f.arm == "redaction")
    assert "keychain-account-id" in details


def test_mutant_a_rogue_member(artifacts, tmp_path):
    """Allowlist: a member outside the package and dist-info is RED."""
    wheel, _ = artifacts
    tampered = _rewritten_wheel(wheel, tmp_path / "rogue.whl",
                                {"notes.md": b"internal notes"})
    findings = [f for f in scan_wheel(tampered, PROJECT_ROOT)
                if f.arm == "allowlist"]
    assert findings and all(f.member == "notes.md" for f in findings)


def test_mutant_junk_riding_the_package_directory(artifacts, tmp_path):
    """Allowlist: a non-source file under ahabase/ is RED (build residue)."""
    wheel, _ = artifacts
    tampered = _rewritten_wheel(wheel, tmp_path / "junk.whl",
                                {"ahabase/config.pyc": b"\x00junk"})
    findings = [f for f in scan_wheel(tampered, PROJECT_ROOT)
                if f.arm == "allowlist"]
    assert findings and all(f.member == "ahabase/config.pyc" for f in findings)


def test_mutant_markdown_outside_the_pinned_data_directory(artifacts, tmp_path):
    """Allowlist: the package-data allowance is pinned to patterns/ - a
    .md member anywhere else under ahabase/ is RED (AHA-0030 R3)."""
    wheel, _ = artifacts
    tampered = _rewritten_wheel(wheel, tmp_path / "notes.whl",
                                {"ahabase/NOTES.md": b"internal notes"})
    findings = [f for f in scan_wheel(tampered, PROJECT_ROOT)
                if f.arm == "allowlist"]
    assert findings and all(f.member == "ahabase/NOTES.md" for f in findings)


def test_the_shipped_templates_are_canonical_package_data(artifacts):
    """Green over the real artifacts: the four pattern templates ride the
    wheel as allowed members, byte-identical to their sources (AHA-0030)."""
    wheel, _ = artifacts
    with zipfile.ZipFile(wheel) as archive:
        members = sorted(n for n in archive.namelist()
                         if n.startswith("ahabase/patterns/"))
    assert members == ["ahabase/patterns/epic.md", "ahabase/patterns/knowledge-map.md",
                       "ahabase/patterns/story.md", "ahabase/patterns/tests.md"]
    for member in members:
        source = PROJECT_ROOT / "src" / "ahabase" / "patterns" / member.split("/")[-1]
        with zipfile.ZipFile(wheel) as archive:
            assert archive.read(member) == source.read_bytes(), member


def test_mutant_a_flipped_byte(artifacts, tmp_path):
    """Canonicality: one byte off from the repository source is RED."""
    wheel, _ = artifacts
    member = "ahabase/config.py"
    with zipfile.ZipFile(wheel) as archive:
        original = bytearray(archive.read(member))
    original[-1] ^= 0x01
    tampered = _rewritten_wheel(wheel, tmp_path / "flip.whl",
                                {member: bytes(original)})
    findings = [f for f in scan_wheel(tampered, PROJECT_ROOT)
                if f.arm == "canonicality"]
    assert findings and all(f.member == member for f in findings)


def test_mutant_symlink_in_the_sdist(artifacts, tmp_path):
    """F2: a non-regular member in the sdist is RED, its target never echoed."""
    _, sdist = artifacts
    with tarfile.open(sdist, "r:gz") as archive:
        members = archive.getmembers()
        payloads = {m.name: (archive.extractfile(m).read() if m.isfile()
                             else b"") for m in members}
    wrapper = members[0].name.split("/", 1)[0]
    target = tmp_path / "symlink.tar.gz"
    with tarfile.open(target, "w:gz") as copy:
        for member in members:
            if member.isfile():
                copy.addfile(member, io.BytesIO(payloads[member.name]))
            else:
                copy.addfile(member)
        rogue = tarfile.TarInfo(wrapper + "/link.py")
        rogue.type = tarfile.SYMTYPE
        rogue.linkname = "/etc/hosts"
        copy.addfile(rogue)
    findings = [f for f in scan_sdist(target, PROJECT_ROOT)
                if f.arm == "allowlist"]
    assert findings and all(f.member == wrapper + "/link.py" for f in findings)
    assert all("symlink" in f.detail for f in findings)
    assert all("/etc/hosts" not in str(f) for f in findings)


def test_mutant_symlink_in_the_wheel(artifacts, tmp_path):
    """F2: a zip entry with the symlink bit is RED."""
    wheel, _ = artifacts
    with zipfile.ZipFile(wheel) as archive:
        entries = [(info.filename, archive.read(info.filename))
                   for info in archive.infolist()]
    target = tmp_path / "symlink.whl"
    with zipfile.ZipFile(target, "w") as copy:
        for name, data in entries:
            copy.writestr(name, data)
        rogue = zipfile.ZipInfo("ahabase/link.py")
        rogue.external_attr = 0o120777 << 16
        copy.writestr(rogue, b"symlink payload")
    findings = [f for f in scan_wheel(target, PROJECT_ROOT)
                if f.arm == "allowlist"]
    assert findings and all(f.member == "ahabase/link.py" for f in findings)
    assert all("symlink" in f.detail for f in findings)


def test_sdist_arm_catches_the_test_file(artifacts, tmp_path):
    """The sdist arm: a string in a shipped test member is RED."""
    _, sdist = artifacts
    with tarfile.open(sdist, "r:gz") as archive:
        name = next(m.name for m in archive.getmembers()
                    if m.name.endswith("tests/test_safe.py"))
        original = archive.extractfile(name).read()
    tampered = _rewritten_sdist(
        sdist, tmp_path / "sdist.tar.gz",
        {name: original + b"\n# e.g. " + b"github.com " + b"987654321\n"})
    findings = [f for f in scan_sdist(tampered, PROJECT_ROOT)
                if f.arm == "redaction"]
    assert findings and all("keychain-account-id" in f.detail
                            for f in findings)
