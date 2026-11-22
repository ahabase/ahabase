"""The dependency is one way (AHA-0024): nothing under ahabase.llm imports a method."""

from __future__ import annotations

import ast
from pathlib import Path

LLM = Path(__file__).resolve().parents[2] / "src" / "ahabase" / "llm"
FORBIDDEN = ("knowledge_usage_cli", "evolucean")


def imported_names(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            yield ("." * node.level) + (node.module or "")


def test_no_module_imports_a_method_package():
    offenders = []
    for file in sorted(LLM.glob("*.py")):
        for name in imported_names(ast.parse(file.read_text(encoding="utf-8"))):
            if any(part in name for part in FORBIDDEN):
                offenders.append((file.name, name))
    assert not offenders, offenders


def test_relative_imports_stay_inside_the_package():
    for file in sorted(LLM.glob("*.py")):
        for name in imported_names(ast.parse(file.read_text(encoding="utf-8"))):
            if name.startswith(".."):
                assert name.split(".")[2] in ("config", "safe", ""), (file.name, name)


def test_the_source_names_no_method_or_instance():
    for file in sorted(LLM.glob("*.py")):
        text = file.read_text(encoding="utf-8").lower()
        for word in FORBIDDEN:
            assert word not in text, (file.name, word)
