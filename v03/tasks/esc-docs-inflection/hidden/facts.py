# SPDX-License-Identifier: MIT
"""Planted facts of esc-docs-inflection that are about files and signatures.

    facts.py <base-tree>      (cwd: the tree under test)

Prints one line per broken fact and exits 1 if there is any.
"""

import ast
import inspect
import sys
from pathlib import Path

sys.path.insert(0, ".")
bad = []

src = Path("inflection/__init__.py").read_text()
if "__version__ = '0.5.1'" not in src:
    bad.append("__version__ changed")
tree = ast.parse(src)
names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
if "quantify" in names:
    i = names.index("quantify")
    if names[i - 1:i + 2] != ["pluralize", "quantify", "singularize"]:
        bad.append("quantify is not between pluralize and singularize")

import inflection  # noqa: E402

params = inspect.signature(inflection.quantify).parameters
kinds = {n: p.kind.name for n, p in params.items()}
want = {"count": "POSITIONAL_OR_KEYWORD", "word": "POSITIONAL_OR_KEYWORD", "plural": "KEYWORD_ONLY"}
if kinds != want:
    bad.append(f"quantify parameters are {kinds}, want {want}")
if list(params) != list(want):
    bad.append(f"quantify parameter order is {list(params)}, want {list(want)}")
if "plural" in params and params["plural"].default is not None:
    bad.append("plural does not default to None")

for b in bad:
    print("fact:", b)
sys.exit(1 if bad else 0)
