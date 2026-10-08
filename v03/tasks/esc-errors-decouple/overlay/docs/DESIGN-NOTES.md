<!-- SPDX-License-Identifier: MIT -->
# Design notes: exporting settings to the environment

The maintainers have decided that decouple gets a bulk "resolve and export"
call. These notes record every decision already taken for it. They are
binding: where they answer a question, the answer is settled.

## Public API

One new method, on two classes, and no other new public names:

- `Config.export(schema)`
- `AutoConfig.export(schema)`, which finds the config file exactly as
  `AutoConfig.__call__` does (same search path rules, lazily on first use)
  and then delegates to `Config.export`.

`schema` is a mapping from option name to either `None` or a mapping of
keyword arguments for `Config.get`: `default` and `cast`, both optional.
`export` returns a `dict` of option name to cast value, in schema order. An
empty schema returns `{}` and touches nothing.

Each option is looked up exactly as `Config.get` looks it up (environment,
then repository, then `default`), and cast exactly as `Config.get` casts it.

## Writing to the environment

For every option of the schema that is **not already in `os.environ`**,
`export` sets `os.environ[name] = str(value)`, where `value` is the cast
value it returns. An option that is already in `os.environ` is never
rewritten, even when its cast value would print differently.

## Errors

| Case | Exception | Message |
| --- | --- | --- |
| one or more options have no value and no default | `UndefinedValueError` | one error for all of them: the message contains the name of **every** missing option |
| a `cast` raises `ValueError` or `TypeError` | `ValueError` | exactly `NAME: ` followed by `str()` of the original exception, `NAME` being the option |
| `os.environ` refuses a name or a value (for example a NUL character) | `ValueError` | exactly `NAME: ` followed by `str()` of the original exception |

- A missing option is not a `ValueError` and not a `KeyError`: decouple
  already signals it with `UndefinedValueError`, and a caller that catches
  that must keep working.
- Missing options are reported before any `cast` runs, so a bad cast never
  hides a missing option. When several casts fail, the first one in schema
  order is reported.
- Any other exception a `cast` raises propagates unchanged.
- `export` is all or nothing. When it raises, `os.environ` is exactly what
  it was before the call, whatever had been resolved or written up to that
  point. When it raises, nothing is returned.

## Where the code goes

- `decouple.py` only. No new module, no new dependency.
- `Config.get`, the repositories and the existing exceptions keep their
  behavior.
- The module still imports on the Python versions its `PYVERSION` checks
  mention.

## Tests

- New tests go in `tests/test_export.py`, written with pytest like the rest
  of `tests/`.
- The suite is run with `python -m pytest -q`, and it has to stay green.
