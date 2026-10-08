Feature request: the `pysemver` command line rejects the `v` prefix that
git tags carry. `pysemver bump patch v1.2.3` fails with
`ERROR v1.2.3 is not valid SemVer string`. Make every subcommand accept a
version with a leading `v` or `V`:

- `bump` and `nextver` print the result with the same prefix
  (`pysemver bump patch v1.2.3` prints `v1.2.4`);
- `compare` accepts it on either argument;
- `check` accepts it.

This is a small change to the command line only: keep it to
`src/semver/cli.py` and its tests.

Tests: `.venv/bin/python -m pytest -q`
