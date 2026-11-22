"""The frozen surface exists (AHA-0024 R2): every function the contract names is importable.

The contract is the section "Seam contract (frozen)" of the implementation
blueprint. Each backticked ``ahabase.llm.<module>`` surface item is imported by
name, and the parameters the contract names are checked against the signature.
The document is not part of the source distribution, so the test is skipped
there.
"""

from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path

import pytest

BLUEPRINT = (Path(__file__).resolve().parents[2] / "_grid4d" / "subepic" / "ahabase-llm" /
             "implementation" / "implementation-ahabase-llm-blueprint.md")

pytestmark = pytest.mark.skipif(not BLUEPRINT.exists(), reason="the Epic's knowledge is not part of the sdist")


def frozen_section() -> str:
    text = BLUEPRINT.read_text(encoding="utf-8")
    start = text.index("## Seam contract (frozen)")
    rest = text[start + 1:]
    end = rest.find("\n## ")
    return rest[:end] if end != -1 else rest


def surface_items():
    """(module, function name, parameter names written in the contract, whether it has an ellipsis)."""
    items = []
    module = None
    for line in frozen_section().splitlines():
        match = re.match(r"\s*- `(ahabase\.llm\.\w+)`:", line)
        if match:
            module = match.group(1)
            body = line[match.end():]
        elif module and line.startswith("  - ") is False and not line.startswith("    "):
            body = ""
        else:
            body = ""
        if module and body:
            for name, args in re.findall(r"`(\w+)\(([^`]*)\)`", body):
                if name in ("resolve_compact_window",):
                    continue
                params = [p.strip().split("=")[0].lstrip("*").strip() for p in args.split(",")
                          if p.strip() and p.strip() not in ("...", "*")]
                items.append((module, name, [p for p in params if p.isidentifier()], "..." in args))
    return items


def test_the_contract_names_the_expected_modules_and_enough_functions():
    modules = {module for module, _, _, _ in surface_items()}
    assert modules == {"ahabase.llm.paths", "ahabase.llm.discovery", "ahabase.llm.verify",
                       "ahabase.llm.switch", "ahabase.llm.session"}
    assert len(surface_items()) >= 29


@pytest.mark.parametrize("module,name,params,elided", surface_items())
def test_every_surface_function_exists_with_the_parameters_the_contract_names(module, name, params, elided):
    function = getattr(importlib.import_module(module), name)
    assert callable(function)
    signature = inspect.signature(function).parameters
    for param in params:
        assert param in signature, f"{module}.{name} lacks the parameter {param!r} the contract names"
    if not elided:
        # a function the contract writes without an ellipsis may gain only keyword-only parameters
        extra = [n for n, p in signature.items() if n not in params
                 and p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)]
        assert not extra, f"{module}.{name} has positional parameters the contract does not name: {extra}"


def test_the_door_commands_the_contract_lists_are_registered():
    from ahabase.cli import build_cli
    names = set(build_cli().commands["llm"].commands)
    for command in re.findall(r"`(?:ahabase llm )?([a-z-]+)(?: PATH_ID)?`", frozen_section().split("Door commands")[1].split("\n")[0]):
        assert command in names, command
