# SPDX-License-Identifier: MIT
"""Planted facts of esc2-caller-semver that are about files, not behaviour.

    facts.py <base-tree>      (cwd: the tree under test)

Prints one line per broken fact and exits 1 if there is any.
"""

import ast
import filecmp
import inspect
import re
import sys
from pathlib import Path

base = Path(sys.argv[1])
bad = []

for p in ("src/semver/_deprecated.py", "src/semver/cli.py", "src/semver/_types.py", "src/semver/__init__.py"):
    if not Path(p).is_file() or not filecmp.cmp(base / p, p, shallow=False):
        bad.append(f"{p} changed")
for p in sorted(Path("src/semver").glob("*.py")):
    try:
        ast.parse(p.read_text(), feature_version=(3, 7))
    except SyntaxError as e:
        bad.append(f"{p} does not parse under Python 3.7: {e}")

sys.path.insert(0, "src")
from semver import Version  # noqa: E402

params = inspect.signature(Version.parse).parameters
if [(n, p.default) for n, p in params.items()] != [("version", inspect.Parameter.empty), ("optional_minor_and_patch", False)]:
    bad.append("Version.parse signature changed")

doc = Version.compare.__doc__ or ""
if not re.search(r">>>.*compare\(\s*b?[\"']\d+(\.\d+)?([-+][^\"']*)?[\"']\s*\)", doc):
    bad.append("Version.compare docstring has no doctest example with a short operand")

t = Path("tests/test_partial_operands.py")
if not t.is_file():
    bad.append("no tests/test_partial_operands.py")
else:
    tree = ast.parse(t.read_text())
    # A test class, not a helper subclass the tests need (the notes rule out
    # TestCase classes; a Version subclass is how an override gets tested).
    def test_class(n):
        return isinstance(n, ast.ClassDef) and (n.name.startswith("Test") or any(
            getattr(b, "id", getattr(b, "attr", "")).endswith("TestCase") for b in n.bases))
    if any(test_class(n) for n in tree.body):
        bad.append("tests/test_partial_operands.py has a class; the suite uses plain functions")
    if "pytest.mark.parametrize" not in t.read_text():
        bad.append("tests/test_partial_operands.py does not use pytest.mark.parametrize")

frag = Path("changelog.d/+partial-operands.feature.rst")
if not frag.is_file() or not frag.read_text().strip():
    bad.append("no changelog.d/+partial-operands.feature.rst")

for b in bad:
    print("fact:", b)
sys.exit(1 if bad else 0)
