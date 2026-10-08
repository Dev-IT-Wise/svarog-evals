# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory and the tree under test as cwd;
# $PY is the interpreter that has pytest (default python3).
visible() { PYTHONPATH=src "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance: upstream's own tests in full, including the tab data
# files the seed removed, plus the tab cases of test_t5_tabs.py.
hidden() {
  rm -rf tests && cp -R "$task/upstream/tests" tests && cp "$task"/hidden/*.py tests/ &&
    PYTHONPATH=src "${PY:-python3}" -m pytest -q -p no:cacheprovider tests
}
