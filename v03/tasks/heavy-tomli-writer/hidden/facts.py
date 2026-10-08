# SPDX-License-Identifier: MIT
"""Planted facts of heavy-tomli-writer that are about files, not behaviour.

    facts.py <base-tree>      (cwd: the tree under test)

Prints one line per broken fact and exits 1 if there is any.
"""

import ast
import filecmp
import sys
from pathlib import Path

base = Path(sys.argv[1])
bad = []

if not Path("src/tomli/_writer.py").is_file():
    bad.append("no src/tomli/_writer.py")
for p in ("src/tomli/_parser.py", "src/tomli/_re.py", "src/tomli/_types.py", "pyproject.toml"):
    if not Path(p).is_file() or not filecmp.cmp(base / p, p, shallow=False):
        bad.append(f"{p} changed")
if '__version__ = "2.4.1"' not in Path("src/tomli/__init__.py").read_text():
    bad.append("__version__ changed")
for p in sorted(Path("src/tomli").glob("*.py")):
    try:
        ast.parse(p.read_text(), feature_version=(3, 8))
    except SyntaxError as e:
        bad.append(f"{p} does not parse under Python 3.8: {e}")

t = Path("tests/test_write.py")
if not t.is_file():
    bad.append("no tests/test_write.py")
else:
    tree = ast.parse(t.read_text())
    bases = {ast.unparse(b) for n in ast.walk(tree) if isinstance(n, ast.ClassDef) for b in n.bases}
    if not bases & {"unittest.TestCase", "TestCase"}:
        bad.append("tests/test_write.py has no unittest.TestCase class")
    if not any(isinstance(n, ast.ImportFrom) and n.level == 1 and n.module is None
               and any(a.name == "tomllib" for a in n.names) for n in ast.walk(tree)):
        bad.append("tests/test_write.py does not import `from . import tomllib`")

readme = Path("README.md").read_text()
if '### Write TOML<a name="write-toml"></a>' not in readme:
    bad.append("README.md has no Write TOML section")
elif readme.index("### Write TOML") < readme.index("### Parse a TOML file"):
    bad.append("README.md Write TOML section is not after Parse a TOML file")
if "The core library does not include write capability" in readme:
    bad.append("README.md FAQ still says there is no write capability")

for b in bad:
    print("fact:", b)
sys.exit(1 if bad else 0)
