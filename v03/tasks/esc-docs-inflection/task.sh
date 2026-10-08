# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory, $upstream to the vendored
# inflection snapshot and the tree under test as cwd; $PY is the interpreter
# that has pytest (default python3), $T5_BASE_TREE the fixture's tree, never
# modified.
visible() { "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance, in this order:
#  1. the tree's own suite passes, the new tests and doctests included;
#  2. the file facts the design notes plant (hidden/facts.py);
#  3. upstream's tests in full plus hidden/test_v03_quantify.py.
hidden() {
  [ -d "${T5_BASE_TREE:-}" ] || { echo "hidden: T5_BASE_TREE is not set"; return 2; }
  grep -q '^def quantify' inflection/__init__.py || { echo "hidden: no quantify in inflection/__init__.py"; return 1; }
  local own
  own=$(visible 2>&1) || { printf '%s\n' "$own" | tail -n 1 | sed 's/^/own suite: /'; return 1; }
  "${PY:-python3}" "$task/hidden/facts.py" "$T5_BASE_TREE" || return 1
  cp "$upstream/test_inflection.py" test_inflection.py && cp "$task"/hidden/test_*.py . &&
    "${PY:-python3}" -m pytest -q -p no:cacheprovider test_inflection.py test_v03_quantify.py
}
