<!-- SPDX-License-Identifier: MIT -->
# Design notes: Cache.reserve

The maintainers have decided to add `reserve`. These notes record every
decision already taken for it. They are binding: where they answer a
question, the answer is settled and does not need to be asked again.

## API

- `Cache.reserve(size) -> None`, a public method on `Cache`, inherited by
  every cache class. Subclasses do not override it; it works through
  `popitem()`, so each class evicts in its own order.
- `size` is a size in the same unit as `getsizeof` results and `maxsize`
  (one per item by default), not a number of items.
- After a successful call, `maxsize - currsize >= size`: a value of that
  size can be inserted without evicting anything more. Nothing is inserted.
- `reserve` evicts only what it has to. If there is room already it does
  nothing.

## Boundaries

- `size` larger than `maxsize` can never fit. `reserve` raises
  `ValueError("value too large")`, the same error `__setitem__` raises, and
  it does so **before evicting anything**: the cache is left exactly as it
  was, not emptied.
- A negative `size` raises `ValueError("value size must be non-negative")`,
  as `__setitem__` does for a negative `getsizeof` result, and leaves the
  cache unchanged. It is never treated as "nothing to do".
- `reserve(0)` never evicts, including on a full cache.
- `size == maxsize` is valid: it evicts everything, leaving an empty cache.
- On `TTLCache` and `TLRUCache`, expired items are dropped first (this is
  what `currsize` already does), and live items are evicted only if that
  was not enough.

## Where the code goes

- The method lives on `Cache` in `src/cachetools/__init__.py`.
- The stub `src/cachetools/__init__.pyi` gets the signature
  `def reserve(self, size: float) -> None: ...` on `Cache`.
- `__version__` and `pyproject.toml` are not changed.

## Tests and documentation

- Tests go in `tests/__init__.py`'s `CacheTestMixin`, so that every cache
  class runs them, plus class-specific cases where the order matters.
- `README.rst` documents `reserve`: a short paragraph and a code example
  after the paragraph on how a full cache discards items.
- The suite is run with `PYTHONPATH=src .venv/bin/python -m pytest -q`.
