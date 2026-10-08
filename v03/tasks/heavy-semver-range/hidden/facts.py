# SPDX-License-Identifier: MIT
"""Planted facts of heavy-semver-range that are about files, not behaviour.

    facts.py <base-tree>      (cwd: the tree under test)

Prints one line per broken fact and exits 1 if there is any.
"""

import ast
import filecmp
import sys
from pathlib import Path

base = Path(sys.argv[1])
bad = []

if not Path("src/semver/ranges.py").is_file():
    bad.append("no src/semver/ranges.py")
for p in ("src/semver/version.py", "src/semver/_deprecated.py", "src/semver/cli.py", "src/semver/_types.py"):
    if not Path(p).is_file() or not filecmp.cmp(base / p, p, shallow=False):
        bad.append(f"{p} changed")
for p in sorted(Path("src/semver").glob("*.py")):
    try:
        ast.parse(p.read_text(), feature_version=(3, 7))
    except SyntaxError as e:
        bad.append(f"{p} does not parse under Python 3.7: {e}")
if Path("src/semver/ranges.py").is_file():
    notes = []
    for n in ast.walk(ast.parse(Path("src/semver/ranges.py").read_text())):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            notes += [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs if x.annotation] + [n.returns]
        elif isinstance(n, ast.AnnAssign):
            notes.append(n.annotation)
    notes = [ast.parse(x.value, mode="eval") if isinstance(x, ast.Constant) and isinstance(x.value, str) else x
             for x in notes if x is not None]
    if any(isinstance(m, ast.BinOp) and isinstance(m.op, ast.BitOr) for x in notes for m in ast.walk(x)):
        bad.append("src/semver/ranges.py uses an `X | Y` annotation")

t = Path("tests/test_ranges.py")
if not t.is_file():
    bad.append("no tests/test_ranges.py")
else:
    tree = ast.parse(t.read_text())
    # A test class, not a helper subclass the tests need (the notes rule out
    # TestCase classes; a Version subclass is how an override gets tested).
    def test_class(n):
        return isinstance(n, ast.ClassDef) and (n.name.startswith("Test") or any(
            getattr(b, "id", getattr(b, "attr", "")).endswith("TestCase") for b in n.bases))
    if any(test_class(n) for n in ast.walk(tree)):
        bad.append("tests/test_ranges.py has a class; the suite uses plain functions")
    if "pytest.mark.parametrize" not in t.read_text():
        bad.append("tests/test_ranges.py does not use pytest.mark.parametrize")

frag = Path("changelog.d/+version-range.feature.rst")
if not frag.is_file() or not frag.read_text().strip():
    bad.append("no changelog.d/+version-range.feature.rst")

for b in bad:
    print("fact:", b)
sys.exit(1 if bad else 0)
