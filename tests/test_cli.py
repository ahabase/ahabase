"""The installed console script (AHA-0001 R2)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import ahabase


def test_console_script_version_and_doctor():
    # the script of the environment running the tests, never one on PATH
    sibling = Path(sys.executable).parent / ("ahabase.exe" if sys.platform == "win32" else "ahabase")
    exe = sibling if sibling.exists() else shutil.which("ahabase")
    assert exe, "the ahabase console script is not installed in this environment"
    exe = str(exe)
    version = subprocess.run([exe, "--version"], capture_output=True, text=True)
    assert version.returncode == 0 and ahabase.__version__ in version.stdout
    doctor = subprocess.run([exe, "doctor"], capture_output=True, text=True)
    assert doctor.returncode == 0, doctor.stdout + doctor.stderr
    assert f"ahabase {ahabase.__version__}" in doctor.stdout
