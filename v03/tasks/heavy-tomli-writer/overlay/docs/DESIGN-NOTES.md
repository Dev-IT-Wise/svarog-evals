# Design notes: writing TOML

The maintainers have decided that tomli will write TOML as well as read it.
These notes record every decision already taken for that feature. They are
binding: where they answer a question, the answer is settled and does not
need to be asked again.

## Public API

Three new public names, and no others:

- `tomli.dumps(obj, /, *, multiline_strings=False) -> str`
- `tomli.dump(obj, fp, /, *, multiline_strings=False) -> None`
- `tomli.TOMLEncodeError`, a subclass of `ValueError`

`dump` takes a **binary** file opened for writing (`open(path, "wb")`), the
mirror image of `tomli.load`, which takes a binary file. It writes the UTF-8
encoding of what `dumps` returns for the same arguments, and nothing else.
It builds the whole text before writing, so a value that cannot be encoded
leaves the file untouched.

All three are exported from `tomli/__init__.py` and appended to `__all__`,
which becomes, in this order:

```python
__all__ = ("loads", "load", "TOMLDecodeError", "dumps", "dump", "TOMLEncodeError")
```

## Where the code goes

- The writer lives in a new module, `src/tomli/_writer.py`.
- `_parser.py`, `_re.py` and `_types.py` are not modified.
- `__version__` and the version in `pyproject.toml` are not changed. A
  release bumps them with bump2version.

## Dependencies and compatibility

- No new dependencies, runtime or test. Standard library only, and
  `pyproject.toml` is not edited.
- Python 3.8 or newer, as `requires-python` says. The new code must parse
  under the 3.8 grammar: no `match` statement and no parenthesized context
  managers. Use `from __future__ import annotations`, as `_parser.py` does,
  for annotations such as `dict[str, Any]`.

## Supported values

| Python value | TOML |
| --- | --- |
| `str` | basic string |
| `bool` | `true` or `false` |
| `int` | decimal integer |
| `float` | float: `repr(x)`, and `inf`, `-inf`, `nan` for the special values |
| `datetime.datetime` | offset or local date-time: `x.isoformat()` |
| `datetime.date` | local date: `x.isoformat()` |
| `datetime.time` | local time: `x.isoformat()` |
| `list` or `tuple` | array (a tuple comes back from `loads` as a list) |
| any `collections.abc.Mapping` | table |

`bool` is checked before `int`, and `datetime.datetime` before
`datetime.date`, because each is a subclass of the other. Anything else,
`None`, `set`, `bytes` and `decimal.Decimal` included, is an error. `None` is
never skipped silently.

## Errors

Every error is a `TOMLEncodeError` with exactly one of these messages:

| Case | Message |
| --- | --- |
| a value of an unsupported type | `Object of type set is not TOML serializable` (the type's `__name__`, so `NoneType` for `None`) |
| a key that is not a `str` | `TOML keys must be strings, not int` (the key type's `__name__`) |
| the top-level object is not a mapping | `The top-level object must be a mapping, not list` (its type's `__name__`) |
| a `datetime.time` with `tzinfo` set | `TOML times cannot have a UTC offset` |

## Output format

The output is fully determined; the tests compare it character for
character.

**Order.** Keys keep their insertion order. Nothing is sorted.

**Tables.** Within one table:

1. First every key whose value is neither a table nor an array of tables,
   as `key = value` lines, in insertion order.
2. Then every sub-table and every array of tables, in insertion order, each
   as its own section.

A value is an *array of tables* when it is a non-empty list or tuple whose
items are all mappings, and it is the value of a key in a table. The same
value nested inside an array or an inline table is written as an array of
inline tables instead.

**Sections.** A sub-table gets a `[a.b]` header with its full dotted path.
Each item of an array of tables gets a `[[a.b]]` header followed by that
item's own lines and sections. A table's header is written only when the
table has at least one `key = value` line of its own, or has no keys at all.
So `{"a": {"b": {"c": 1}}}` is written as `[a.b]` alone, and `{"a": {}}` as
`[a]`.

**Blank lines.** The output is a sequence of blocks: the top-level
`key = value` lines (when there are any), then one block per section header
written, in depth-first order. Blocks are separated by exactly one blank
line. The text ends with exactly one newline, and an empty mapping gives
the empty string `""`.

**Keys.** A key matching `[A-Za-z0-9_-]+` is written bare. Any other key,
the empty key included, is written as a basic string, escaped like a value.

**Strings.** Basic strings in double quotes. Escapes: `\\` for a backslash,
`\"` for a double quote, `\b`, `\t`, `\n`, `\f`, `\r` for those five
characters, and `\uXXXX` with upper-case hex for every other character in
U+0000 to U+001F and for U+007F. Everything else, non-ASCII included, is
written as it is.

**`multiline_strings=True`.** A string that contains `\n` and is the value of
a `key = value` line is written as a multi-line basic string: `"""`, a
newline, the content, then `"""`. In the content every `\n` is a real line
break, and every other character is escaped exactly as in a basic string,
`"` included. Strings inside arrays and inline tables, and keys, are always
single-line. With the default `False`, every string is single-line.

**Arrays** are always written on one line: `[1, 2, 3]`, items separated by
`, `, and `[]` when empty. Mixed types are allowed.

**Inline tables** are written as `{ a = 1, b = "x" }`, pairs separated by
`, `, and `{}` when empty. Nested mappings inside an inline table are nested
inline tables.

**Round trip.** For every supported value `d`, `tomli.loads(tomli.dumps(d))
== d`, with tuples read back as lists.

## Example

```python
tomli.dumps({
    "title": "TOML",
    "owner": {"name": "Tom", "dob": datetime.date(1979, 5, 27)},
    "servers": [{"ip": "10.0.0.1"}, {"ip": "10.0.0.2", "tags": ["a", "b"]}],
    "points": [{"x": 1}, 2],
})
```

returns

```toml
title = "TOML"
points = [{ x = 1 }, 2]

[owner]
name = "Tom"
dob = 1979-05-27

[[servers]]
ip = "10.0.0.1"

[[servers]]
ip = "10.0.0.2"
tags = ["a", "b"]
```

## Tests

- New tests go in `tests/test_write.py`, as `unittest.TestCase` classes like
  the rest of the suite, importing the package as `from . import tomllib`
  (see `tests/__init__.py`).
- The suite is run with `PYTHONPATH=src .venv/bin/python -m pytest -q`, and
  it has to stay green.

## Documentation

- `README.md` gets a `### Write TOML<a name="write-toml"></a>` section in
  Usage, after "Parse a TOML file", showing `tomli.dumps` and `tomli.dump`.
- The FAQ entry "Is there a `dumps`, `write` or `encode` function?" is
  rewritten to say yes and point to that section.
