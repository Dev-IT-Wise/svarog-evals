# SPDX-License-Identifier: MIT
# Sourced with $task set to this directory and the tree under test as cwd;
# $PY is the interpreter that has pytest (default python3).
visible() { "${PY:-python3}" -m pytest -q -p no:cacheprovider; }
# Hidden acceptance: upstream's own tests plus test_t5_refactor.py, which pins
# the behaviour of pluralize/singularize and checks both use _inflect.
hidden() {
  rm -f test_*.py && cp "$task/upstream/test_inflection.py" . && cp "$task"/hidden/*.py . &&
    "${PY:-python3}" -m pytest -q -p no:cacheprovider test_inflection.py test_t5_refactor.py
}
