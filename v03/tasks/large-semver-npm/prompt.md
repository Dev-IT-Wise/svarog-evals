I want npm-style version ranges in semver: `^1.2`, `~1.2.3`, `1.x`,
`1.2.3 - 2.0.0`, `>=1.0.0 <2.0.0 || 3.x` and so on. Checking a version
against a range, picking the newest or oldest version that fits, the
lowest version a range allows, whether two ranges overlap, and two new
`pysemver` subcommands for scripts. With tests and docs, please.
