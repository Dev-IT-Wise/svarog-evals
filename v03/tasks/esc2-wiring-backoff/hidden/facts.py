# SPDX-License-Identifier: MIT
"""File facts of esc2-wiring-backoff.

    facts.py <base-tree>      (cwd: the tree under test)
"""
import filecmp
import re
import sys
from pathlib import Path

base = Path(sys.argv[1])
bad = []

if not Path("backoff/_linear.py").is_file():
    bad.append("no backoff/_linear.py")
elif not Path("backoff/_linear.py").read_text().startswith("# coding:utf-8"):
    bad.append("backoff/_linear.py lacks the coding header")
if not filecmp.cmp(base / "backoff/_wait_gen.py", "backoff/_wait_gen.py", shallow=False):
    bad.append("backoff/_wait_gen.py changed")
if 'equal_jitter' not in Path("backoff/_jitter.py").read_text():
    bad.append("equal_jitter not in backoff/_jitter.py")
if '__version__ = "2.2.1"' not in Path("backoff/__init__.py").read_text():
    bad.append("__version__ changed")
if not Path("tests/test_linear.py").is_file():
    bad.append("no tests/test_linear.py")
for p in ("backoff/_linear.py", "backoff/_jitter.py"):
    if Path(p).is_file():
        for i, line in enumerate(Path(p).read_text().splitlines(), 1):
            if len(line) > 79:
                bad.append(f"{p}:{i} longer than 79 characters")

log = Path("CHANGELOG.md").read_text()
m = re.search(r"## Unreleased\n(.*?)(?=\n## )", log, re.S)
sec = m.group(1) if m else ""
if "### Added" not in sec:
    bad.append("CHANGELOG.md has no Added heading under Unreleased")
for name in ("linear", "equal_jitter"):
    if not re.search(r"^- `backoff\.%s` - \S" % name, sec, re.M):
        bad.append(f"CHANGELOG.md Unreleased lacks a line for {name}")

for b in bad:
    print("fact:", b)
sys.exit(1 if bad else 0)
