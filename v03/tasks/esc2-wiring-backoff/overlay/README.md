<!-- SPDX-License-Identifier: MIT -->
# backoff

Function decoration for backoff and retry. See `docs/DESIGN-NOTES.md` for
decisions in flight.

## Wait generators

- `backoff.expo` - exponential growth, optionally capped.
- `backoff.fibo` - Fibonacci growth, optionally capped.
- `backoff.decay` - exponential decay with an optional floor.
- `backoff.constant` - a fixed interval, or an iterable of intervals.
- `backoff.runtime` - a wait computed from the return value or exception.

## Jitter functions

- `backoff.full_jitter` - a random value between 0 and the wait.
- `backoff.random_jitter` - the wait plus up to one second.
