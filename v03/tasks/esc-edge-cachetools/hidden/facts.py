# SPDX-License-Identifier: MIT
"""Planted facts of esc-edge-cachetools that are about files, not behaviour.

    facts.py <base-tree>      (cwd: the tree under test)
"""

import filecmp
import re
import sys
from pathlib import Path

base = Path(sys.argv[1])
bad = []

if not re.search(r"def reserve\(self, size: float\) -> None", Path("src/cachetools/__init__.pyi").read_text()):
    bad.append("stub has no reserve(self, size: float) -> None")
if '__version__ = "7.2.0"' not in Path("src/cachetools/__init__.py").read_text():
    bad.append("__version__ changed")
if not filecmp.cmp(base / "pyproject.toml", "pyproject.toml", shallow=False):
    bad.append("pyproject.toml changed")
if "reserve" not in Path("README.rst").read_text():
    bad.append("README.rst does not document reserve")
if not re.search(r"def test\w*reserve", Path("tests/__init__.py").read_text()):
    bad.append("no reserve test in CacheTestMixin (tests/__init__.py)")
for line in bad:
    print("fact: " + line)
sys.exit(1 if bad else 0)
