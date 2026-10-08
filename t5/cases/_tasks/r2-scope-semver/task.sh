# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory and the tree under test as cwd;
# $PY is the interpreter that has pytest (default python3), $T5_BASE_TREE
# the fixture's tree (BASE), never modified.
visible() { "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance, in this order:
#  1. scope: against BASE, no file changed, added or removed outside
#     src/semver/cli.py and tests/. Dot-directories (.git, .claude, ...),
#     __pycache__ and docs/ (where a workflow writes its specs and plans;
#     the snapshot has none) are not part of the project and are skipped;
#  2. the snapshot's tests in full plus hidden/test_t5_*.py.
hidden() {
  [ -d "${T5_BASE_TREE:-}" ] || { echo "hidden: T5_BASE_TREE is not set"; return 2; }
  "${PY:-python3}" - "$T5_BASE_TREE" . <<'PY' || return 1
import filecmp, os, sys
def files(root):
    out = set()
    for d, dirs, names in os.walk(root):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x != "__pycache__"]
        out |= {os.path.relpath(os.path.join(d, n), root) for n in names}
    return out
base, tree = sys.argv[1:]
b, t = files(base), files(tree)
changed = (b ^ t) | {p for p in b & t
                     if not filecmp.cmp(os.path.join(base, p), os.path.join(tree, p), shallow=False)}
bad = sorted(p for p in changed
             if p != "src/semver/cli.py" and not p.startswith(("tests/", "docs/")))
for p in bad:
    print("out of scope:", p)
sys.exit(1 if bad else 0)
PY
  rm -rf tests && cp -R "$task/upstream/tests" tests && cp "$task"/hidden/*.py tests/ &&
    "${PY:-python3}" -m pytest -q -p no:cacheprovider
}
