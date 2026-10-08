# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory and the tree under test as cwd;
# $PY is the interpreter that has pytest (default python3).
visible() { "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance: the snapshot's tests in full plus the give-up cases of
# test_t5_giveup.py, which cover coroutines as well as plain functions.
hidden() {
  rm -rf tests && cp -R "$task/upstream/tests" tests && cp "$task"/hidden/*.py tests/ &&
    "${PY:-python3}" -m pytest -q -p no:cacheprovider tests
}
