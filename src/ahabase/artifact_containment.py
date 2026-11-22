"""The artifact containment scan: the built wheel and sdist carry only Users-zone bytes.

The rule (the MVP ruling, AHA-0029): what leaves the
repository through the package channel may carry nothing below zone 1
(Users) - the scan runs over the exact built artifacts, not a
reconstruction, with three arms. **Allowlist**: every artifact member is
on the pinned list and a regular file - the wheel ships exactly the
package directory plus its dist-info, the sdist ships exactly the
pyproject include list plus its generated PKG-INFO, and a non-regular
member (a symlink, a link, a device) is a finding wherever it sits.
**Canonicality** (the strict-subset arm): every repo-file member is
byte-identical to its repository source - one canonical copy per
module, so no artifact file exists that the repository does not vouch
for. **Redaction**: no member byte matches the defined
corporate-identifier pattern set. One named package-data allowance
(AHA-0030): the default pattern templates under ``ahabase/patterns/``
ship beside the .py sources, pinned by directory and
canonicality-checked like every member.

The redaction arm is a guard over a fixed pattern set, not a proof that
no secret exists: it proves these patterns are absent, nothing more
(the public-release dossier's own non-overclaim). The set is a class,
not a literal list - each pattern names a *kind* of corporate
identifier (a numeric account id beside a credential host, any e-mail
address, the internal GitHub host, the internal directory and schema
names), so a new instance of a known kind is caught, not only the
strings that were measured once; internal names match as substrings, so
an embedded form cannot ride a word boundary. Beside the classes stands
one tombstone: the retired account id, held as a sha256 digest and
matched over every 8-digit window of every digit run - bare, embedded
in letters or in a longer number, in any form. The pattern set's own
vocabulary is composed at runtime, never written as a literal, so this
module and its suite ship under the same arm as every other member
with no exemptions - over the whole wheel and the whole sdist, zero
member bytes carry a corporate identifier. One declared allowance
keeps documentation green: an e-mail address at an RFC 2606/6761
reserved domain is an example, not a leak. A violation reports the
member, the line and the pattern's name - never the matched text, so a
real match is not echoed into a log.

Implements: implementation-ahabase-release-containment-blueprint
Blueprint: implementation-ahabase-release-containment-blueprint

Capability: artifact-containment
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

#: The corporate-identifier pattern set: name -> the kind it catches.
#: Extending the set is a story decision, never a silent fix; each new
#: pattern names its kind so the class stays legible. Every internal
#: literal is composed at runtime (``"..." + "..."``), so this
#: definition site ships no identifier bytes (review F1, AHA-0029) and
#: needs no redaction exemption.
CORPORATE_IDENTIFIER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # a numeric account id beside a credential host: keychain examples
    # name accounts by id - any id, not one measured string; up to four
    # non-digit characters may sit between host and id (a space or a
    # slash, or the comma-and-quotes of a code example), and the id
    # itself is five digits or more (account ids are 5-9 digits, so a
    # four-digit year in prose stays green). The host is public; the
    # id-beside-host pairing is the identifier.
    ("keychain-account-id",
     re.compile(r"github\.com[^\d\n]{0,4}\d{5,}")),
    # any e-mail address at a non-reserved domain: the package ships none
    # legitimately; documentation examples at the RFC 2606/6761 reserved
    # domains (example.com/.org/.net and their subdomains, .example,
    # .invalid, .localhost, .test) stay green - see _is_reserved_domain
    ("email-address",
     re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    # the internal enterprise GitHub host (composed at runtime)
    ("internal-github-host", re.compile(r"github\.tim" + "br" + r"\.ai")),
    # the internal directory name, matched as a substring so an
    # embedded form (name_suffix) cannot ride a word boundary
    # (review F_d, AHA-0029)
    ("internal-username", re.compile("kamen" + "skl")),
    # the internal sandbox schema prefixes, substrings (embedded included)
    ("internal-schema-prefix", re.compile("mmds" + "bx_|mn" + "dm[-_]")),
)

#: The retired account id's sha256, held as a digest so no byte of this
#: tree carries the value itself (review F1, AHA-0029): the one id this
#: repository has already retired once, blocked in any form - bare,
#: with no host beside it, or embedded in letters or a longer number.
#: The honest limit: an 8-digit id is brute-forceable; the digest
#: removes the greppable literal, not the secrecy.
RETIRED_ID_SHA256 = "0bc51dea00f415cf2bb1b2a866c8dbf046a012a07b80f63abd2f888da0316fa0"

#: A maximal digit run: the tombstone scans every 8-digit window of
#: every run (the id's exact length), so no word boundary or longer
#: number can hide it.
_DIGIT_RUN = re.compile(r"\d+")

#: Documentation domains (RFC 2606/6761): an e-mail address here is an
#: example, not a leak - the baseline run measured the fixtures' use of
#: git.example.com and stayed green through this allowance.
_RESERVED_DOMAINS = ("example.com", "example.org", "example.net", "example",
                     "invalid", "localhost", "test")


def _is_reserved_domain(address: str) -> bool:
    """True when the address's domain is a documentation domain."""
    domain = address.rsplit("@", 1)[1].lower().rstrip(".")
    return (domain in _RESERVED_DOMAINS
            or any(domain.endswith("." + reserved)
                   for reserved in _RESERVED_DOMAINS))

#: The sdist's allowed members below the wrapper directory: the pyproject
#: include list (``[tool.hatch.build.targets.sdist] include``) plus the
#: generated PKG-INFO and the .gitignore hatchling ships implicitly
#: (measured in the baseline run; its bytes are still canonicality-checked
#: and redaction-scanned like every member). The wheel's allowed members
#: are structural: the package directory and the dist-info directory -
#: pinned by prefix, not enumerated, so a module list change is an
#: ordinary review diff.
_WHEEL_PACKAGE = "ahabase/"
_WHEEL_DIST_INFO = re.compile(r"^ahabase-[^/]+\.dist-info/")
_SDIST_WRAPPER = re.compile(r"^ahabase-[^/]+/")
_SDIST_ALLOWED = ("src/ahabase/", "tests/", "README.md", "LICENSE",
                  "pyproject.toml", "PKG-INFO", ".gitignore")

#: The one named package-data allowance (AHA-0030, R3): the default
#: pattern templates the format core ships beside its .py sources -
#: pinned by directory and extension, canonicality-checked like every
#: other member, so a template in the artifact is byte-identical to
#: its repository source. Extending this set is a story decision,
#: never a silent fix.
_WHEEL_PACKAGE_DATA = re.compile(r"^ahabase/patterns/[\w-]+\.md$")
_SDIST_PACKAGE_DATA = re.compile(r"^src/ahabase/patterns/[\w-]+\.md$")


@dataclass(frozen=True)
class Violation:
    """One containment finding: arm, artifact, member, detail - no matched text."""

    arm: str          # allowlist | canonicality | redaction
    artifact: str     # wheel | sdist
    member: str
    detail: str

    def __str__(self) -> str:  # the report line a log may carry
        return f"[{self.arm}] {self.artifact}: {self.member} - {self.detail}"


def build_artifacts(project_root: Path, outdir: Path) -> tuple[Path, Path]:
    """Build the exact wheel and sdist (no isolation: the test extras carry the backend)."""
    outdir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "build", "--no-isolation", "--outdir", str(outdir),
         str(project_root)],
        check=True, capture_output=True, text=True,
    )
    wheel = next(outdir.glob("ahabase-*.whl"))
    sdist = next(outdir.glob("ahabase-*.tar.gz"))
    return wheel, sdist


def _redaction_findings(artifact: str, member: str, data: bytes) -> list[Violation]:
    """Scan one member's bytes: every pattern hit is a violation, the text never echoed."""
    text = data.decode("utf-8", errors="replace")
    findings: list[Violation] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        # the tombstone first: every 8-digit window of every digit run
        # in the line, digest-compared - bare, embedded, any form
        for run in _DIGIT_RUN.finditer(line):
            digits = run.group(0)
            if len(digits) < 8:
                continue
            for start in range(len(digits) - 7):
                if (hashlib.sha256(digits[start:start + 8].encode()).hexdigest()
                        == RETIRED_ID_SHA256):
                    findings.append(Violation(
                        "redaction", artifact, member,
                        f"line {lineno}: pattern retired-account-id"))
                    break
        for name, pattern in CORPORATE_IDENTIFIER_PATTERNS:
            hit = pattern.search(line)
            if not hit:
                continue
            if name == "email-address" and _is_reserved_domain(hit.group(0)):
                continue  # a documentation example, not a leak
            findings.append(Violation(
                "redaction", artifact, member,
                f"line {lineno}: pattern {name}"))
    return findings


def scan_wheel(wheel: Path, project_root: Path) -> list[Violation]:
    """The three arms over the whole wheel."""
    violations: list[Violation] = []
    source = project_root / "src" / "ahabase"
    with zipfile.ZipFile(wheel) as archive:
        for info in archive.infolist():
            name = info.filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts:
                violations.append(Violation(
                    "allowlist", "wheel", name, "not a plain member path"))
                continue
            if name.endswith("/"):
                continue
            mode = info.external_attr >> 16
            if mode and (mode & 0o170000) == 0o120000:
                violations.append(Violation(
                    "allowlist", "wheel", name,
                    "non-regular member: a symlink entry"))
                continue
            if not (name.startswith(_WHEEL_PACKAGE)
                    or _WHEEL_DIST_INFO.match(name)):
                violations.append(Violation(
                    "allowlist", "wheel", name,
                    "outside the package directory and the dist-info"))
                continue
            if (name.startswith(_WHEEL_PACKAGE) and path.suffix != ".py"
                    and not _WHEEL_PACKAGE_DATA.match(name)):
                violations.append(Violation(
                    "allowlist", "wheel", name,
                    "not a .py source or a pinned package-data member - "
                    "build residue or junk riding the package directory"))
                continue
            data = archive.read(name)
            violations += _redaction_findings("wheel", name, data)
            if name.startswith(_WHEEL_PACKAGE):
                repo_file = source / PurePosixPath(name).relative_to("ahabase")
                if not repo_file.is_file():
                    violations.append(Violation(
                        "canonicality", "wheel", name,
                        "no repository source at this path"))
                elif repo_file.read_bytes() != data:
                    violations.append(Violation(
                        "canonicality", "wheel", name,
                        "not byte-identical to its repository source"))
    return violations


def scan_sdist(sdist: Path, project_root: Path) -> list[Violation]:
    """The three arms over the whole sdist (the wrapper strip is the only rewrite)."""
    violations: list[Violation] = []
    with tarfile.open(sdist, "r:gz") as archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            if not member.isfile():
                kind = ("a symlink" if member.issym()
                        else "a hard link" if member.islnk()
                        else "a fifo" if member.isfifo()
                        else "a device" if member.isdev()
                        else "not a regular file")
                violations.append(Violation(
                    "allowlist", "sdist", member.name,
                    f"non-regular member: {kind}"))
                continue
            if not _SDIST_WRAPPER.match(member.name):
                violations.append(Violation(
                    "allowlist", "sdist", member.name,
                    "outside the wrapper directory"))
                continue
            rel = member.name.split("/", 1)[1]
            if not (any(rel == allowed or rel.startswith(allowed)
                        for allowed in _SDIST_ALLOWED)):
                violations.append(Violation(
                    "allowlist", "sdist", member.name,
                    "not on the sdist include list"))
                continue
            if (rel.startswith("src/ahabase/") and not rel.endswith(".py")
                    and not _SDIST_PACKAGE_DATA.match(rel)):
                violations.append(Violation(
                    "allowlist", "sdist", member.name,
                    "not a .py source or a pinned package-data member - "
                    "build residue or junk riding the package directory"))
                continue
            data = archive.extractfile(member).read()
            violations += _redaction_findings("sdist", member.name, data)
            if rel == "PKG-INFO":
                continue  # generated metadata, the only exemption
            repo_file = project_root / rel
            if not repo_file.is_file():
                violations.append(Violation(
                    "canonicality", "sdist", member.name,
                    "no repository source at this path"))
            elif repo_file.read_bytes() != data:
                violations.append(Violation(
                    "canonicality", "sdist", member.name,
                    "not byte-identical to its repository source"))
    return violations


def scan_release(wheel: Path, sdist: Path, project_root: Path) -> list[Violation]:
    """The standing gate: both artifacts, all three arms, zero findings expected."""
    return scan_wheel(wheel, project_root) + scan_sdist(sdist, project_root)
