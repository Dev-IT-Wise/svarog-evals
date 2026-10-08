# SPDX-License-Identifier: MIT
"""Planted facts of large-semver-npm that are about files, not behaviour.

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
for p in ("src/semver/version.py", "src/semver/_deprecated.py", "src/semver/_types.py"):
    if not Path(p).is_file() or not filecmp.cmp(base / p, p, shallow=False):
        bad.append(f"{p} changed")
for p in sorted(Path("src/semver").glob("*.py")):
    try:
        ast.parse(p.read_text(), feature_version=(3, 7))
    except SyntaxError as e:
        bad.append(f"{p} does not parse under Python 3.7: {e}")


def bitor_annotations(path):
    notes = []
    for n in ast.walk(ast.parse(path.read_text())):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            a = n.args
            notes += [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs if x.annotation] + [n.returns]
        elif isinstance(n, ast.AnnAssign):
            notes.append(n.annotation)
    notes = [ast.parse(x.value, mode="eval") if isinstance(x, ast.Constant) and isinstance(x.value, str) else x
             for x in notes if x is not None]
    return any(isinstance(m, ast.BinOp) and isinstance(m.op, ast.BitOr) for x in notes for m in ast.walk(x))


for p in ("src/semver/ranges.py", "src/semver/cli.py"):
    if Path(p).is_file() and bitor_annotations(Path(p)):
        bad.append(f"{p} uses an `X | Y` annotation")

init = Path("src/semver/__init__.py").read_text()
names = []
for n in ast.parse(init).body:
    if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "__all__" for t in n.targets):
        names = [e.value for e in n.value.elts if isinstance(e, ast.Constant)]
if names[-4:] != ["Range", "Comparator", "InvalidRangeError", "satisfies"]:
    bad.append(f"__all__ does not end with the four new names in order: {names[-4:]}")


def test_class(n):
    # A test class, not a helper subclass the tests need.
    return isinstance(n, ast.ClassDef) and (n.name.startswith("Test") or any(
        getattr(b, "id", getattr(b, "attr", "")).endswith("TestCase") for b in n.bases))


for p, needle in (("tests/test_ranges.py", None), ("tests/test_pysemver-cli.py", "satisfies")):
    t = Path(p)
    if not t.is_file():
        bad.append(f"no {p}")
        continue
    text = t.read_text()
    if any(test_class(n) for n in ast.walk(ast.parse(text))):
        bad.append(f"{p} has a test class; the suite uses plain functions")
    if needle and ("max-satisfying" not in text or needle not in text):
        bad.append(f"{p} does not test the satisfies and max-satisfying subcommands")

doc = Path("docs/usage/ranges.rst")
if not doc.is_file():
    bad.append("no docs/usage/ranges.rst")
else:
    text = doc.read_text()
    for needle in ("^", "~", " - ", "x", "pysemver satisfies", "pysemver max-satisfying", "--include-prerelease"):
        if needle not in text:
            bad.append(f"docs/usage/ranges.rst does not mention {needle!r}")

frags = sorted(p.name for p in Path("changelog.d").glob("*")) if Path("changelog.d").is_dir() else []
base_frags = sorted(p.name for p in (base / "changelog.d").glob("*")) if (base / "changelog.d").is_dir() else []
new = [f for f in frags if f not in base_frags]
if new != ["+npm-ranges.feature.rst"]:
    bad.append(f"changelog.d: expected exactly +npm-ranges.feature.rst, found {new}")

for line in bad:
    print(f"fact: {line}")
sys.exit(1 if bad else 0)
