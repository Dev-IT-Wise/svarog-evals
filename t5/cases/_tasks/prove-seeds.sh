#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Proves for every T5 task, without Claude:
#   upstream          visible passes
#   seeded            visible passes, hidden FAILS (the seed is present)
#   seeded+naive      visible passes, hidden FAILS (the hidden test catches
#                     the plausible wrong answer the visible suite lets by)
#   seeded+reference  visible passes, hidden passes (the task is solvable)
# Every expectation is checked; exits non-zero if any did not hold.
# Hidden checks get the seeded tree as BASE. Task names as arguments prove
# only those; the default is every task.
#   prove-seeds.sh [task...]
set -u
. "$(dirname "$0")/lib.sh"
fail=0
expect() { # <want pass|fail> <label> <task> <tree> <check> [base]
  if out=$(run_check "$3" "$4" "$5" "${6:-}"); then got=pass; else got=fail; fi
  if [ "$got" = "$1" ]; then mark=ok; else mark=WRONG; fail=1; fi
  printf '%-6s %-20s %-18s %-8s %s (%s)\n' "$mark" "$3" "$2" "$5" "$got" "$out"
}
for task in ${*:-$all_tasks}; do
  w=$(mktemp -d)
  cp -R "$tasks_dir/$task/upstream" "$w/upstream"
  build_seeded "$task" "$w/seeded"
  for v in naive reference; do
    cp -R "$w/seeded" "$w/$v"
    (cd "$w/$v" && git apply "$tasks_dir/$task/$v.patch")
  done
  expect pass upstream "$task" "$w/upstream" visible
  expect pass seeded "$task" "$w/seeded" visible
  expect fail seeded "$task" "$w/seeded" hidden "$w/seeded"
  expect pass seeded+naive "$task" "$w/naive" visible
  expect fail seeded+naive "$task" "$w/naive" hidden "$w/seeded"
  expect pass seeded+reference "$task" "$w/reference" visible
  expect pass seeded+reference "$task" "$w/reference" hidden "$w/seeded"
  rm -rf "$w"
done
exit $fail
