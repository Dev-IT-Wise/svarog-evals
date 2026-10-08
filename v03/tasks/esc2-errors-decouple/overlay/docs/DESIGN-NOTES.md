<!-- SPDX-License-Identifier: MIT -->
# Design notes: exporting settings to the environment

The maintainers have decided that decouple gets a bulk "resolve and export"
call. These notes record the decisions already taken for it. They are
binding: where they answer a question, the answer is settled.

## Public API

- `Config.export(schema)` and `AutoConfig.export(schema)` are the only new
  public names.
- `AutoConfig.export` finds the config file the way `AutoConfig.__call__`
  does, lazily on first use, and then delegates to `Config.export`.
- `schema` maps an option name to `None` or to a dict of keyword arguments
  for `Config.get` (`default`, `cast`).

## Behaviour

- Each option is resolved exactly as `Config.get` resolves it: environment,
  then repository, then `default`, then `cast`.
- `export` returns a `dict` of option name to cast value, in schema order.
  An empty schema returns `{}`.
- An option that is already in `os.environ` is left as it is.
- Any other option is set with `os.environ[name] = str(value)`, where
  `value` is the cast value.
- When options have no value and no default, `export` raises one
  `UndefinedValueError` whose message contains the name of every one of
  them, and `os.environ` is not modified.
- An exception raised by a `cast` propagates unchanged, as it does from
  `Config.get`.

## Where the code goes

- `decouple.py` only. No new module and no new dependency.
- `Config.get`, the repositories and the existing exceptions keep their
  behaviour.

## Documentation

- Both new methods have a docstring of one or two sentences, in the style of
  the existing ones.
- `CHANGELOG.md` is created at the repository root. It starts with the line
  `# Changelog`, followed by a `## Unreleased` section with the entry
  `- Add Config.export and AutoConfig.export.`

## Tests

- New tests go in `tests/test_export.py`, written with pytest like the rest
  of `tests/`.
- Each test that touches `os.environ` restores it afterwards.
- The suite is run with `python -m pytest -q` and has to stay green.
