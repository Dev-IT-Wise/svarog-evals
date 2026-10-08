# SPDX-License-Identifier: MIT
# Shared by the case scaffolds and prove-seeds.sh.
tasks_dir=$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)
# Round 1 (t5-report.md), then round 2: one task per failure mode - a false
# "done", a vacuous test, a scope overrun.
all_tasks="bug-tomli feature-cachetools refactor-inflection r2-done-backoff r2-vacuous-decouple r2-scope-semver"

# build_seeded <task> <dest>: the pinned upstream snapshot of <task> with its
# seed applied, as a plain directory tree (no .git).
build_seeded() {
  mkdir -p "$2"
  cp -R "$tasks_dir/$1/upstream/." "$2/"
  if [ -f "$tasks_dir/$1/seed.patch" ]; then
    (cd "$2" && git apply "$tasks_dir/$1/seed.patch")
  fi
}

# run_check <task> <tree> visible|hidden [base]: runs that check on a copy
# of <tree>, so a hidden run never alters the tree. <base> is the fixture's
# tree, which round 2's hidden checks compare against (T5_BASE_TREE); it is
# read, never written. Prints the check's last line.
run_check() {
  local tmp rc out
  tmp=$(mktemp -d)
  cp -R "$2/." "$tmp/"
  rc=0
  out=$(cd "$tmp" && task="$tasks_dir/$1" && export T5_BASE_TREE="${4:-}" &&
    . "$task/task.sh" && "$3" 2>&1) || rc=$?
  printf '%s\n' "$out" | tail -n 1
  rm -rf "$tmp"
  return $rc
}

# scaffold_run <task>: called by every case's scaffold.sh, with the run
# directory as cwd and the sandbox home as HOME. Identical for all arms.
scaffold_run() {
  # svarog keeps hook state under <root>/config/plugins/data, which the Bash
  # sandbox cannot see; link it into <root>/tmp. Inert for the other arms.
  root=$(cd "$HOME/.." && pwd)
  data="$root/tmp/svarog-plugin-data"
  mkdir -p "$data/svarog-inline" "$HOME/.claude/plugins" "$root/config/plugins/data"
  ln -s "$data" "$HOME/.claude/plugins/data"
  ln -s "$data/svarog-inline" "$root/config/plugins/data/svarog-inline"

  export GIT_AUTHOR_NAME=Fixture GIT_AUTHOR_EMAIL=fixture@example.invalid
  export GIT_COMMITTER_NAME=Fixture GIT_COMMITTER_EMAIL=fixture@example.invalid
  export GIT_AUTHOR_DATE='2026-01-01T00:00:00+0000' GIT_COMMITTER_DATE='2026-01-01T00:00:00+0000'
  git init -q -b main .
  printf '.eval-evidence/\n.venv/\n__pycache__/\n.pytest_cache/\n' >> .git/info/exclude
  # pytest for the run, without network: a venv over the system packages
  # plus the pytest that stage.sh copied to <stage>/pytest-site.
  python3 -m venv --without-pip --system-site-packages .venv
  cp -R "$tasks_dir/../../pytest-site/." .venv/lib/python3*/site-packages/
  # Claude Code's Bash sandbox mounts placeholders for these names in every
  # directory a session works in, worktrees included, and the eval harness
  # adds .eval-artifacts; untracked, they make any clean-tree check fail.
  # The sandbox's protected files and directories, plus that one.
  printf '%s\n' .eval-artifacts .vscode/ .idea/ .husky/ .cargo/ .devcontainer/ .yarn/ .mvn/ \
    .vscode .idea .claude/ .mcp.json .claude.json .bashrc .bash_profile .bash_login \
    .bash_aliases .bash_logout .profile .zshrc .zprofile .zshenv .zlogin .zlogout \
    .gitconfig .gitmodules .envrc .ripgreprc .npmrc .yarnrc .yarnrc.yml \
    .pre-commit-config.yaml .devcontainer.json pyrightconfig.json >> .git/info/exclude
  build_seeded "$1" .
  cp "$tasks_dir/answers.toml" .
  # svarog's documented setup (CONTRACT.md): a `Verify:` line in CLAUDE.md,
  # which only a human may write. Absolute, so it also runs in a worktree, which has no
  # .venv of its own. Inert for the other arms.
  py="$PWD/.venv/bin/python"
  if [ -d src ]; then
    printf 'Verify: `env PYTHONPATH=src "%s" -m pytest -q`\n' "$py" >> CLAUDE.md
  else
    printf 'Verify: `"%s" -m pytest -q`\n' "$py" >> CLAUDE.md
  fi
  git add -A
  git commit -q -m "$1: pinned upstream snapshot"
  echo "$1" > .git/t5-task
  git rev-parse HEAD > .git/t5-base
  # The seed is present in this very run: the hidden check fails here.
  if PY="$PWD/.venv/bin/python" run_check "$1" . hidden "$PWD" > /dev/null; then
    echo "seed check failed: hidden acceptance passes on the scaffold of $1" >&2
    exit 1
  fi
}
