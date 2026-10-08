<!-- SPDX-License-Identifier: MIT -->
# Design notes: linear waits and equal jitter

The maintainers have decided to add one wait generator and one jitter
function. These notes record the decisions already taken. They are binding.

## Names and signatures

- `backoff.linear(start=1, step=1, max_value=None)`, a wait generator. It
  yields `start`, `start + step`, `start + 2 * step`, and so on.
- `backoff.equal_jitter(value)`, a jitter function. It returns `value / 2`
  plus a random amount between `0` and `value / 2`.

## Behaviour

- Like every wait generator, `linear` first `yield`s once so that it can be
  advanced with `.send(None)`.
- Once the next value would reach `max_value` (`a >= max_value`),
  `max_value` is yielded forever after.
- `equal_jitter(value)` is always in `[value / 2, value]`, and
  `equal_jitter(0)` is `0`.
- Both names work as `wait_gen` or `jitter` for `on_exception` and
  `on_predicate`, on plain and on coroutine functions. The decorators are not
  changed.

## Where the code goes

- `linear` goes in a new module, `backoff/_linear.py`. `_wait_gen.py` is not
  modified.
- `equal_jitter` goes in `backoff/_jitter.py`.
- No new dependencies, and `__version__` is not changed.

## Package surface

- `backoff/__init__.py` imports both names and lists both in `__all__`,
  after their siblings.

## Documentation

- `README.md` gets one line per name in the matching list, in the form
  `` `backoff.linear` - ... ``.
- `CHANGELOG.md` gets an `### Added` heading under "Unreleased" with one
  line per name, in the same form.

## Formatting

- Lines are at most 79 characters. New modules start with
  `# coding:utf-8` and annotate their signatures like `_wait_gen.py` does.

## Tests

- `linear` is tested in a new file, `tests/test_linear.py`.
  `equal_jitter` is tested in `tests/test_jitter.py`.
- The suite is run with `.venv/bin/python -m pytest -q` and has to stay
  green.
