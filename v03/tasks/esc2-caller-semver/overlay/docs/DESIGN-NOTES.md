<!-- SPDX-License-Identifier: MIT -->
# Design notes: short versions as comparison operands

The maintainers have decided that the comparison API accepts short versions
such as `1.2` or `2` as the other operand. These notes record every decision
already taken for that feature. They are binding: where they answer a
question, the answer is settled and does not need to be asked again.

## Behaviour

A short version is a version with the minor part, or the minor and patch
parts, left out: `2`, `1.2`, `1.2-rc.1`, `1+build.5`. Missing parts are zero.

A short version is accepted wherever a version string is already accepted as
the other operand of a comparison:

- `Version.compare(other)`;
- `==`, `!=`, `<`, `<=`, `>`, `>=` with a `str` or `bytes` on either side;
- the version of the expression in `Version.match(expr)`, for every operator
  and for the bare form: `match(">=1.2")`, `match("!=2")`, `match("1.2")`
  (which means `==1.2`).

So `Version.parse("1.2.0") == "1.2"` is true, `Version.parse("1.2.3") > "1.2"`
is true, and `Version.parse("1.2.3").match("<2")` is true.

## Scope

- `Version.parse(s)` and `Version.is_valid(s)` are strict as today:
  `is_valid("1.2")` is `False`, and the signature of `parse` is not changed.
- The module functions in `_deprecated.py` and the `pysemver` command line
  are as they are. `_deprecated.py`, `cli.py`, `_types.py` and `__init__.py`
  are not modified, and there is no new public name.
- `dict`, `tuple` and `list` operands behave as they do now.

## Parsing

String and bytes operands are parsed with `cls.parse(operand)`, called with
the operand as its only argument. An operand that is not a full or a short
version, such as `""`, `garbage`, `1.`, `1.2.3.4` or `01.2.3`, raises
`ValueError` with the message it has today: `<operand> is not valid SemVer
string`.

## Existing tests

`test_should_not_allow_to_compare_invalid_versionstring` in
`tests/test_compare.py` lists `"1"` and `"1.0"` as invalid operands. Those two
are now valid; the test keeps `"1.0.x"`.

## Where the code goes

- The change lives in `src/semver/version.py`. Keep it small.
- No new dependencies. Standard library only.

## Compatibility

The package supports Python 3.7 and newer. The new code must parse under the
3.7 grammar: no `:=`, no positional-only `/` parameters, no `match`
statement. Annotate with `typing`, not with `X | Y` or `list[...]`.

## Documentation

The docstring of `Version.compare` gets one doctest example with a short
operand. There is no separate documentation tree in this snapshot.

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
