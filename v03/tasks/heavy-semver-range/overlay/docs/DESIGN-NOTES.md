# Design notes: version ranges

The maintainers have decided that semver will support version ranges such
as `^1.2.3` or `>=1.0.0, <2.0.0`. These notes record every decision already
taken for that feature. They are binding: where they answer a question, the
answer is settled and does not need to be asked again.

## Public API

Two new public names, and no others:

- `semver.VersionRange`, a class.
- `semver.InvalidRangeError`, a subclass of `ValueError`.

Both live in a new module, `src/semver/ranges.py`, are imported in
`src/semver/__init__.py`, and are appended to the end of `__all__` in that
order: `"VersionRange", "InvalidRangeError"`.

`VersionRange`:

- `VersionRange(expression)`. `expression` must be a `str`; anything else
  raises `TypeError` with the message
  `range expression must be a str, not int` (the type's `__name__`). The
  expression is parsed in the constructor, so an invalid one fails there.
- `.expression`: the string exactly as given.
- `.contains(version, *, include_prerelease=False) -> bool`. `version` is a
  `Version` or a `str`; a `str` is parsed with `Version.parse`, and its
  `ValueError` for an invalid string propagates unchanged. Any other type
  raises `TypeError` with the message `expected Version or str, not int`.
- `version in rng` is `rng.contains(version)`.
- `.max_satisfying(versions, *, include_prerelease=False) -> Optional[Version]`:
  the highest of `versions` (an iterable of `Version` or `str`) that the
  range contains, returned as a `Version`, or `None` when none does.
- `repr(rng)` is `VersionRange('>=1.0.0, <2.0.0')`, that is
  `f"VersionRange({expression!r})"`. `str(rng)` is the expression.
- Every public method has a docstring, as `tests/test_docstrings.py` asks of
  the package's functions.

## Grammar

```
expression := group ( "||" group )*
group      := comparator ( "," comparator )*
comparator := [ operator ] version
operator   := "^" | "~" | ">=" | "<=" | ">" | "<" | "==" | "!="
```

- Whitespace around `||`, `,` and between an operator and its version is
  ignored.
- `version` is a full SemVer string as `Version.parse` accepts it, with
  optional prerelease and build parts. There are no partial versions
  (`1.2`), no wildcards (`1.x`, `*`) and no `v` prefix.
- A comparator without an operator means `==`.
- A version matches a range when it matches at least one group (`||` is
  OR), and it matches a group when it matches every comparator of the group
  (`,` is AND).

## Meaning of each operator

- `>=`, `<=`, `>`, `<`, `==`, `!=` compare with `Version`'s own ordering,
  which ignores build metadata.
- `^V` allows changes that do not modify the left-most non-zero part:
  - `^1.2.3` is `>=1.2.3, <2.0.0`;
  - `^0.2.3` is `>=0.2.3, <0.3.0`;
  - `^0.0.3` is `>=0.0.3, <0.0.4`.
- `~V` allows patch-level changes: `~1.2.3` is `>=1.2.3, <1.3.0`, and
  `~0.2.3` is `>=0.2.3, <0.3.0`.
- The upper bounds of `^` and `~` are exclusive and carry no prerelease.

## Prerelease versions

By default a version with a prerelease part, such as `1.2.3-alpha.7`, is
contained only when it satisfies every comparator of a group **and** that
same group has at least one comparator whose version has a prerelease part
and the same major, minor and patch as the candidate. So:

- `>=1.2.3-alpha.3` contains `1.2.3-alpha.7` but not `3.4.5-alpha.9`;
- `^1.2.3` contains neither `1.5.0-beta.1` nor `2.0.0-rc.1`;
- `>=1.0.0-rc.1, <2.0.0` contains `1.0.0-rc.2` but not `1.1.0-rc.1`.

With `include_prerelease=True` a prerelease version is treated like any
other version, and only the comparators decide.

## Errors

Every invalid expression raises `InvalidRangeError` with exactly one of
these messages, where `{expr}` is the whole expression in `repr()` form:

| Case | Message |
| --- | --- |
| the expression is empty or only whitespace | `empty range expression` |
| an empty group or comparator, such as `>=1.0.0,` or `1.0.0 \|\| ` | `empty comparator in range {expr}` |
| anything else that is not a comparator, such as `=>1.0.0`, `^1.2` or `1.x` | `invalid comparator {comparator} in range {expr}` |

`{comparator}` is the offending comparator, stripped of surrounding
whitespace, in `repr()` form. For example `VersionRange(">=1.0.0, ^1.2")`
raises `InvalidRangeError("invalid comparator '^1.2' in range '>=1.0.0, ^1.2'")`.

## Where the code goes

- `src/semver/ranges.py` holds all of it. It uses only `Version`'s public
  API.
- `version.py`, `_deprecated.py`, `cli.py` and `_types.py` are not modified.
- No new dependencies. Standard library only.

## Compatibility

The package supports Python 3.7 and newer. The new code must parse under
the 3.7 grammar: no `:=`, no positional-only `/` parameters, no `match`.
Annotate with `typing` (`Optional`, `Union`, `Iterable`, `List`), not with
`X | Y` or `list[...]`.

## Tests

- New tests go in `tests/test_ranges.py`, as plain pytest functions using
  `pytest.mark.parametrize` like the rest of the suite. No
  `unittest.TestCase` classes.
- The suite is run with `.venv/bin/python -m pytest -q` (`.pytest.ini` sets
  the paths), and it has to stay green.

## Changelog

Upstream collects changelog entries as towncrier fragments. Add one file,
`changelog.d/+version-range.feature.rst`, with a one-sentence description of
the feature.
