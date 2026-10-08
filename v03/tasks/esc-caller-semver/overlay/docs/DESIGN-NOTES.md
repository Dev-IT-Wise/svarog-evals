<!-- SPDX-License-Identifier: MIT -->
# Design notes: short versions as comparison operands

The maintainers have decided that the comparison API accepts short versions
such as `1.2` or `2` as the other operand. These notes record every decision
already taken for that feature. They are binding: where they answer a
question, the answer is settled and does not need to be asked again.

## Behaviour

A *short version* is a string that `Version.parse(s, optional_minor_and_patch=True)`
accepts and `Version.parse(s)` rejects: `2`, `1.2`, `1.2-rc.1`, `1+build.5`.
Missing minor and patch parts are zero.

A short version is accepted wherever a version string is already accepted as
the **other** operand of a comparison:

- `Version.compare(other)`;
- `==`, `!=`, `<`, `<=`, `>`, `>=` with a `str` or `bytes` on either side;
- the version of the expression in `Version.match(expr)`, for every operator
  and for the bare form: `match(">=1.2")`, `match("!=2")`, `match("1.2")`
  (which means `==1.2`).

So `Version.parse("1.2.0") == "1.2"` is true, `Version.parse("1.2.3") > "1.2"`
is true, and `Version.parse("1.2.3").match("<2")` is true.

One existing test contradicts this and is superseded:
`test_should_not_allow_to_compare_invalid_versionstring` in
`tests/test_compare.py` lists `"1"` and `"1.0"` as invalid operands. Those two
are now valid; keep `"1.0.x"`, which stays invalid.

## What does not change

- `Version.parse(s)` stays strict. It still rejects `1.2`, its signature
  stays `parse(cls, version, optional_minor_and_patch=False)`, and so does
  `Version.is_valid`: `is_valid("1.2")` is `False`.
- The left operand of the module functions in `_deprecated.py`
  (`semver.compare`, `semver.match`, `semver.max_ver`, ...) and the
  `pysemver` command line stay as they are. `_deprecated.py`, `cli.py`,
  `_types.py` and `__init__.py` are not modified, and there is no new public
  name.
- An operand that is neither a full nor a short version, such as `""`,
  `garbage`, `1.`, `1.2.3.4` or `01.2.3`, raises `ValueError` with the same
  message as today: `<operand> is not valid SemVer string`.
- `dict`, `tuple` and `list` operands behave as they do now.

## Subclasses

`Version` is meant to be subclassed, and the usual reason is to change how a
string is parsed: `tests/semverwithvprefix.py` and `tests/test_subclass.py`
show the pattern. A subclass overrides the classmethod `parse` with the
one-parameter signature `parse(cls, version)` and does its own handling,
for example requiring a `v` prefix. Comparison operands that are strings go
through `cls.parse`, so the subclass's rules apply to them.

That override pattern is public API and must keep working:

- the library must not rely on a `parse` override accepting
  `optional_minor_and_patch` or any other keyword it does not already pass;
- for every operand that compared fine before, the result is the same for a
  subclass, and an operand the subclass's `parse` rejects still raises
  `ValueError`, never `TypeError`.

## Where the code goes

- The change lives in `src/semver/version.py`. Keep it small.
- No new dependencies. Standard library only.

## Compatibility

The package supports Python 3.7 and newer. The new code must parse under the
3.7 grammar: no `:=`, no positional-only `/` parameters, no `match`
statement. Annotate with `typing`, not with `X | Y` or `list[...]`.

## Tests

- New tests go in `tests/test_partial_operands.py`, as plain pytest
  functions using `pytest.mark.parametrize` like the rest of the suite. No
  `unittest.TestCase` classes.
- The suite is run with `.venv/bin/python -m pytest -q` (`.pytest.ini` sets
  the paths), and it has to stay green.

## Changelog

Upstream collects changelog entries as towncrier fragments. Add one file,
`changelog.d/+partial-operands.feature.rst`, with a one-sentence description
of the feature.
