# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory, $upstream to the vendored
# python-semver snapshot and the tree under test as cwd; $PY is the
# interpreter that has pytest (default python3), $T5_BASE_TREE the fixture's
# tree, never modified.
visible() { "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance, in this order:
#  1. the tree's own suite passes, the new tests included;
#  2. the file facts the design notes plant (hidden/facts.py);
#  3. the snapshot's tests in full plus hidden/test_v03_partial.py.
hidden() {
  [ -d "${T5_BASE_TREE:-}" ] || { echo "hidden: T5_BASE_TREE is not set"; return 2; }
  [ -f tests/test_partial_operands.py ] || { echo "hidden: no tests/test_partial_operands.py"; return 1; }
  local own
  own=$(visible 2>&1) || { printf '%s\n' "$own" | tail -n 1 | sed 's/^/own suite: /'; return 1; }
  "${PY:-python3}" "$task/hidden/facts.py" "$T5_BASE_TREE" || return 1
  # The one upstream test the notes supersede: "1" and "1.0" are now valid operands.
  rm -rf tests && cp -R "$upstream/tests" tests && cp "$task"/hidden/test_*.py tests/ &&
    sed -i 's/("1", "1.0", "1.0.x")/("1.0.x",)/' tests/test_compare.py &&
    grep -q '("1.0.x",)' tests/test_compare.py &&
    "${PY:-python3}" -m pytest -q -p no:cacheprovider
}
