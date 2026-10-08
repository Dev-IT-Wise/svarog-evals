Bug report: giving up because the wait generator ran out does not behave
like any other give-up. With a finite generator, for example
`backoff.constant` with `interval=[1, 2]`:

1. `@backoff.on_exception(..., raise_on_giveup=False)` re-raises the
   exception instead of returning `None`.
2. `@backoff.on_predicate` calls its `on_giveup` handlers with a `details`
   dict that has no `"value"`, so a handler that reads `details["value"]`
   raises `KeyError`.

A give-up has to behave the same whatever caused it - `max_tries`,
`max_time`, `giveup` or an exhausted generator - for both decorators, and
for coroutines as well as plain functions.

Tests: `.venv/bin/python -m pytest -q`
