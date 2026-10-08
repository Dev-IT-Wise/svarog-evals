# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory and the tree under test as cwd;
# $PY is the interpreter that has pytest (default python3), $T5_BASE_TREE
# the fixture's tree (BASE), never modified.
visible() { "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance, in this order:
#  1. the tree's own tests against BASE's decouple.py: at least one has to
#     fail, or no test the change adds or edits pins the bug (vacuous);
#  2. BASE's tests plus hidden/test_t5_*.py against the tree's decouple.py:
#     all pass, so the fix works and no existing assertion was loosened.
hidden() {
  local tmp rc=0
  [ -d "${T5_BASE_TREE:-}" ] || { echo "hidden: T5_BASE_TREE is not set"; return 2; }
  tmp=$(mktemp -d)
  cp -R . "$tmp/tree"
  cp "$T5_BASE_TREE/decouple.py" "$tmp/tree/decouple.py"
  (cd "$tmp/tree" && "${PY:-python3}" -m pytest -q -p no:cacheprovider) > "$tmp/on-base.log" 2>&1 || rc=$?
  tail -n 1 "$tmp/on-base.log" | sed 's/^/tests on BASE: /'
  rm -rf "$tmp"
  if [ "$rc" -eq 0 ]; then
    echo "vacuous: every test in the tree passes against BASE's decouple.py"
    return 1
  fi
  rm -rf tests && cp -R "$T5_BASE_TREE/tests" tests && cp "$task"/hidden/*.py tests/ &&
    "${PY:-python3}" -m pytest -q -p no:cacheprovider tests
}
