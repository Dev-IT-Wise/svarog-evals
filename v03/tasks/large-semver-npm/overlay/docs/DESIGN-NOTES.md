# Design notes: npm-style version ranges

The maintainers have decided that semver will support version ranges with
the grammar and meaning npm uses, for example `^1.2`, `1.x || >=2.5.0`,
`1.2.3 - 2.3.4` or `>=1.0.0 <2.0.0-0`. These notes record every decision
already taken for that feature. They are binding: where they answer a
question, the answer is settled and does not need to be asked again.

## Public API

New public names, and no others:

- `semver.Range`, a class.
- `semver.Comparator`, a class.
- `semver.InvalidRangeError`, a subclass of `ValueError`.
- `semver.satisfies(version, range_expr, *, include_prerelease=False) -> bool`,
  a function.

All four live in a new module, `src/semver/ranges.py`, are imported in
`src/semver/__init__.py`, and are appended to the end of `__all__` in this
order: `"Range", "Comparator", "InvalidRangeError", "satisfies"`.

### `Comparator`

One primitive comparison, after every shorthand has been expanded.

- `Comparator(operator, version)`. `operator` is one of `"<"`, `"<="`,
  `">"`, `">="`, `"="`, or `""`, where `""` means "any version" and
  `version` is then `None`. Any other operator raises `ValueError` with the
  message `unknown operator {operator!r}`. `version` is a `Version`.
- `.operator`, `.version`: as given.
- `.test(version) -> bool`: whether `version` (a `Version`) passes this one
  comparison, by `Version`'s own ordering, which ignores build metadata.
  `test` knows nothing about prerelease rules; those belong to `Range`.
- `str(c)` is the operator followed by the version, `>=1.2.0`; `"="` is
  written as the bare version, `1.2.3`; `""` is written `*`.
- Two comparators are equal when operator and version are equal; they are
  hashable.

### `Range`

- `Range(expression)`. `expression` must be a `str`; anything else raises
  `TypeError` with the message `range expression must be a str, not int`
  (the type's `__name__`). The expression is parsed in the constructor, so
  an invalid one fails there.
- `.expression`: the string exactly as given.
- `.sets`: the parsed form, a `tuple` of `tuple`s of `Comparator`, one inner
  tuple per `||` alternative, in source order, every shorthand expanded
  (see "Expansion").
- `.contains(version, *, include_prerelease=False) -> bool`. `version` is a
  `Version` or a `str`; a `str` is parsed with `Version.parse`, and its
  `ValueError` for an invalid string propagates unchanged. Any other type
  raises `TypeError` with the message `expected Version or str, not int`.
- `version in rng` is `rng.contains(version)`.
- `.max_satisfying(versions, *, include_prerelease=False) -> Optional[Version]`
  and `.min_satisfying(...)`: the highest or lowest of `versions` (an
  iterable of `Version` or `str`) that the range contains, as a `Version`,
  or `None` when none does.
- `.filter(versions, *, include_prerelease=False) -> List[Version]`: the
  contained versions, as `Version`s, in input order, duplicates kept.
- `.min_version() -> Optional[Version]`: the lowest of these candidates
  that `contains(candidate, include_prerelease=True)` accepts: `0.0.0`;
  every comparator's version; and for every `>V` comparator the version
  right after `V` (`V` with patch + 1 when `V` has no prerelease, otherwise
  `V` with `.0` appended to its prerelease). `None` when no candidate is
  contained, for example for `>2.0.0 <1.0.0`. So `>=1.2.3` gives `1.2.3`,
  `>1.2.3` gives `1.2.4`, and `*` and `<2.0.0` give `0.0.0`.
- `.intersects(other) -> bool`: whether some version `v` exists with
  `self.contains(v, include_prerelease=True)` and
  `other.contains(v, include_prerelease=True)` both true. `other` is a `Range` or a `str`; anything else
  raises `TypeError` with the message `expected Range or str, not int`.
- `repr(rng)` is `Range('>=1.0.0 <2.0.0')`, that is
  `f"Range({expression!r})"`. `str(rng)` is the normalised form: the
  comparators of each set joined by one space, the sets joined by ` || `,
  so `str(Range("^1.2"))` is `>=1.2.0 <2.0.0-0`.
- Two ranges are equal when their `.sets` are equal; they are hashable.

### `satisfies`

`satisfies(version, range_expr, *, include_prerelease=False)` is
`Range(range_expr).contains(version, include_prerelease=include_prerelease)`.
`range_expr` may also be a `Range`.

Every public function, method and class has a docstring, as
`tests/test_docstrings.py` asks of the package's functions.

## Grammar

```
range      := set ( "||" set )*
set        := hyphen | simple ( " "+ simple )* | ""
hyphen     := partial " - " partial
simple     := primitive | tilde | caret | partial
primitive  := ( "<" | ">" | ">=" | "<=" | "=" ) partial
tilde      := "~" partial
caret      := "^" partial
partial    := xr ( "." xr ( "." xr qualifier? )? )?
xr         := "x" | "X" | "*" | nr
nr         := "0" | [1-9][0-9]*
qualifier  := ( "-" prerelease )? ( "+" build )?
```

- Spaces separate the comparators of a set (AND); `||` separates sets (OR).
  Leading and trailing whitespace of the expression and of each set is
  ignored, as are spaces between an operator and its version.
- An empty set, as in `1.2.3 || `, means `*`. An empty or whitespace-only
  expression also means `*`.
- A leading `v` or `=` on a version (`v1.2.3`, `=1.2.3`) is accepted and
  dropped.
- `prerelease` and `build` are as SemVer defines them; a qualifier is only
  allowed on a full `major.minor.patch`.

## Expansion

Each shorthand becomes primitive comparators. `X` stands for any of `x`,
`X`, `*` or a missing part. The `-0` on an upper bound is the lowest
possible prerelease, so the bound excludes that version's prereleases too.

| Input | Expands to |
| --- | --- |
| `*`, `x`, `` (empty) | `*` (operator `""`) |
| `1` or `1.x` or `1.x.x` | `>=1.0.0 <2.0.0-0` |
| `1.2` or `1.2.x` | `>=1.2.0 <1.3.0-0` |
| `1.2.3` | `1.2.3` (operator `"="`) |
| `1.2.3 - 2.3.4` | `>=1.2.3 <=2.3.4` |
| `1.2 - 2.3.4` | `>=1.2.0 <=2.3.4` |
| `1.2.3 - 2.3` | `>=1.2.3 <2.4.0-0` |
| `1.2.3 - 2` | `>=1.2.3 <3.0.0-0` |
| `~1.2.3` | `>=1.2.3 <1.3.0-0` |
| `~1.2` | `>=1.2.0 <1.3.0-0` |
| `~1` | `>=1.0.0 <2.0.0-0` |
| `~0.2.3` | `>=0.2.3 <0.3.0-0` |
| `^1.2.3` | `>=1.2.3 <2.0.0-0` |
| `^0.2.3` | `>=0.2.3 <0.3.0-0` |
| `^0.0.3` | `>=0.0.3 <0.0.4-0` |
| `^1.2.x` | `>=1.2.0 <2.0.0-0` |
| `^0.0.x` | `>=0.0.0 <0.1.0-0` |
| `^0.0` | `>=0.0.0 <0.1.0-0` |
| `^1.x` | `>=1.0.0 <2.0.0-0` |
| `^0.x` | `>=0.0.0 <1.0.0-0` |
| `>1` | `>=2.0.0` |
| `>1.2` | `>=1.3.0` |
| `>=1.2` | `>=1.2.0` |
| `<1.2` | `<1.2.0-0` |
| `<=1.2` | `<1.3.0-0` |
| `>*` or `<*` | a set that contains nothing: `<0.0.0-0` |
| `>=*` or `<=*` | `*` |
| `~1.2.3-beta.2` | `>=1.2.3-beta.2 <1.3.0-0` |
| `^1.2.3-beta.2` | `>=1.2.3-beta.2 <2.0.0-0` |

A prerelease on the lower end is kept as written; build metadata is
dropped everywhere.

## Prerelease versions

By default a version with a prerelease part, such as `1.2.3-alpha.7`, is
contained only when it satisfies every comparator of a set **and** that set
has at least one comparator whose version has a prerelease part and the
same major, minor and patch as the candidate. The `-0` that expansion adds
to an upper bound does not count for this. So:

- `>1.2.3-alpha.3` contains `1.2.3-alpha.7` but not `3.4.5-alpha.9`;
- `^1.2.3` contains neither `1.5.0-beta.1` nor `2.0.0-rc.1`;
- `1.x` contains neither `1.5.0-beta.1` nor `2.0.0-0`.

With `include_prerelease=True` a prerelease version is treated like any
other version, and only the comparators decide.

## Errors

Every invalid expression raises `InvalidRangeError` with exactly one of
these messages, where `{expr}` is the whole expression in `repr()` form:

| Case | Message |
| --- | --- |
| a comparator that is not one, such as `=>1.0.0`, `1.2.3.4`, `01.2.3`, `1.x.3` or `^` | `invalid comparator {comparator} in range {expr}` |
| a qualifier on a partial version, such as `1.2-beta` | `prerelease on a partial version in range {expr}` |
| a hyphen range with a missing end, such as `1.2.3 -` or `- 2.0.0` | `incomplete hyphen range in range {expr}` |

`{comparator}` is the offending token in `repr()` form.

## Command line

`cli.py` gains two subcommands. Nothing else in it changes, apart from
`main`, which may change only as far as these need.

- `pysemver satisfies VERSION RANGE`: prints `VERSION` and exits 0 when the
  range contains it; prints nothing and exits 1 when it does not.
- `pysemver max-satisfying RANGE VERSION [VERSION ...]`: prints the highest
  contained version and exits 0; prints nothing and exits 1 when none is.
- Both take `--include-prerelease`. An invalid range or version prints
  `ERROR <message>` on stderr and exits 2, as the existing subcommands do.

## Where the code goes

- `src/semver/ranges.py` holds the range code. It uses only `Version`'s
  public API.
- `version.py`, `_deprecated.py` and `_types.py` are not modified.
- No new dependencies. Standard library only.

## Compatibility

The package supports Python 3.7 and newer. The new code must parse under
the 3.7 grammar: no `:=`, no positional-only `/` parameters, no `match`.
Annotate with `typing` (`Optional`, `Union`, `Iterable`, `List`, `Tuple`),
not with `X | Y` or `list[...]`.

## Tests

- New tests go in `tests/test_ranges.py` and, for the command line, in
  `tests/test_pysemver-cli.py`, as plain pytest functions using
  `pytest.mark.parametrize` like the rest of the suite. No
  `unittest.TestCase` classes.
- The suite is run with `.venv/bin/python -m pytest -q` (`.pytest.ini` sets
  the paths), and it has to stay green.

## Documentation

- `README.rst` does not exist in this snapshot; the user documentation is a
  new file, `docs/usage/ranges.rst`, with a title, one example per row of
  the expansion table's shorthand families (x-ranges, hyphen, tilde, caret,
  primitives), the prerelease rule, and both CLI subcommands.
- Upstream collects changelog entries as towncrier fragments. Add one file,
  `changelog.d/+npm-ranges.feature.rst`, with a one-sentence description of
  the feature.
