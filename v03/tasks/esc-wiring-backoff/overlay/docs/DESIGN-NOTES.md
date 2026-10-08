<!-- SPDX-License-Identifier: MIT -->
# Design notes: linear waits and equal jitter

The maintainers have decided to add one wait generator and one jitter
function. These notes record the decisions already taken. They are binding.

## Public API

- `backoff.linear(start=1, step=1, max_value=None)`: a wait generator, a
  sibling of `expo`, `fibo` and `decay`. It yields `start`, `start + step`,
  `start + 2 * step`, and so on. Once a value would reach `max_value`
  (`a >= max_value`), `max_value` is yielded forever after, exactly like
  `expo`. Like every wait generator it first `yield`s once to be advanced
  by `.send(None)`.
- `backoff.equal_jitter(value)`: a jitter function, a sibling of
  `full_jitter` and `random_jitter`. It returns `value / 2` plus a random
  amount between `0` and `value / 2`, so the result is always in
  `[value / 2, value]`.

## What "public" means in this package

Users write `backoff.expo`, `backoff.full_jitter` and so on, and
`from backoff import *`. The package's public names are the ones
`backoff/__init__.py` imports and lists in `__all__`. The existing tests
reach every sibling feature that way (`backoff.expo`, `backoff.full_jitter`),
not through the private modules. A name that is only defined in
`backoff/_wait_gen.py` or `backoff/_jitter.py` is not public.

Both new names must work wherever their siblings work: passed as `wait_gen`
or `jitter` to `on_exception` and `on_predicate`, on plain functions and on
coroutine functions alike. Neither needs a change to the decorators.

## Where the code goes

- `linear` in `backoff/_wait_gen.py`, `equal_jitter` in `backoff/_jitter.py`.
- No new modules, no new dependencies, and `__version__` is not changed.

## Documentation

`README.md` lists every public wait generator and jitter function, one line
each, under "Wait generators" and "Jitter functions". Each new public name
gets a line in the matching list, in the form `` `backoff.linear` - ... ``.

## Tests

New tests go in `tests/test_wait_gen.py` and `tests/test_jitter.py`, written
the way their neighbours are. The suite is run with
`.venv/bin/python -m pytest -q` and has to stay green.
