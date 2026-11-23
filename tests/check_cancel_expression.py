"""AHA-0037 R2: evaluate the workflow's own cancel-in-progress expression.

Reads .github/workflows/tests.yml, translates the GitHub expression to
Python (the three operators it uses: ``!=``, ``&&``/``||``/``!`` and
``startsWith``), and evaluates it for a main ref, a tag ref and a feature
ref - the file's expression, not a restatement of it. Exit 0 when main
and tags are exempt and a feature branch cancels; 1 otherwise.
"""

import re
import sys

import yaml

CASES = (("refs/heads/main", False), ("refs/tags/v0.1.0", False),
         ("refs/heads/feature/x", True))


def to_python(expression: str) -> str:
    body = re.fullmatch(r"\s*\$\{\{(.*)\}\}\s*", str(expression), re.S)
    text = body.group(1) if body else str(expression)
    text = re.sub(r"startsWith\(\s*github\.ref\s*,\s*('[^']*')\s*\)",
                  r"ref.startswith(\1)", text)
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"!(?!=)", " not ", text)
    return text.replace("github.ref", "ref")


def main() -> int:
    workflow = yaml.safe_load(open(".github/workflows/tests.yml"))
    concurrency = workflow["concurrency"]
    if "github.ref" not in concurrency["group"]:
        print("the concurrency group is not keyed on the ref")
        return 1
    code = to_python(concurrency["cancel-in-progress"])
    failed = 0
    for ref, want in CASES:
        got = bool(eval(code, {"ref": ref}))  # the translated file expression
        print(f"{ref}: cancel-in-progress={got} (want {want})")
        failed += got != want
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
