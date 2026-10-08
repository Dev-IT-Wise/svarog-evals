# SPDX-License-Identifier: MIT
# T5 hidden acceptance test, r2-done-backoff. A give-up behaves the same
# whatever caused it: raise_on_giveup is honoured and on_giveup receives the
# same details keys, for on_exception and on_predicate, for plain functions
# and for coroutines.
import asyncio

import pytest

import backoff

EXHAUSTED = dict(interval=[0, 0])   # backoff.constant: two waits, then done
MAX_TRIES = dict(interval=0, max_tries=3)


def exception_target(is_async, how, **kw):
    seen = []
    if is_async:
        @backoff.on_exception(backoff.constant, ValueError, on_giveup=seen.append, **how, **kw)
        async def target():
            raise ValueError("boom")
    else:
        @backoff.on_exception(backoff.constant, ValueError, on_giveup=seen.append, **how, **kw)
        def target():
            raise ValueError("boom")
    return target, seen


def predicate_target(is_async, how):
    seen = []
    if is_async:
        @backoff.on_predicate(backoff.constant, on_giveup=seen.append, **how)
        async def target():
            return 0
    else:
        @backoff.on_predicate(backoff.constant, on_giveup=seen.append, **how)
        def target():
            return 0
    return target, seen


def call(target, is_async):
    return asyncio.run(target()) if is_async else target()


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_exhausted_generator_honours_raise_on_giveup_false(is_async):
    target, seen = exception_target(is_async, EXHAUSTED, raise_on_giveup=False)
    assert call(target, is_async) is None
    assert len(seen) == 1 and seen[0]["tries"] == 3


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_exhausted_generator_still_raises_by_default(is_async):
    target, seen = exception_target(is_async, EXHAUSTED)
    with pytest.raises(ValueError, match="boom"):
        call(target, is_async)
    assert len(seen) == 1 and seen[0]["tries"] == 3


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_exception_giveup_details_match_max_tries(is_async):
    t1, exhausted = exception_target(is_async, EXHAUSTED, raise_on_giveup=False)
    t2, max_tries = exception_target(is_async, MAX_TRIES, raise_on_giveup=False)
    call(t1, is_async)
    call(t2, is_async)
    assert set(exhausted[0]) == set(max_tries[0])
    assert isinstance(exhausted[0]["exception"], ValueError)


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_predicate_exhausted_generator_passes_value(is_async):
    target, seen = predicate_target(is_async, EXHAUSTED)
    assert call(target, is_async) == 0
    assert len(seen) == 1 and seen[0]["tries"] == 3
    assert seen[0]["value"] == 0


@pytest.mark.parametrize("is_async", [False, True], ids=["sync", "async"])
def test_predicate_giveup_details_match_max_tries(is_async):
    t1, exhausted = predicate_target(is_async, EXHAUSTED)
    t2, max_tries = predicate_target(is_async, MAX_TRIES)
    call(t1, is_async)
    call(t2, is_async)
    assert set(exhausted[0]) == set(max_tries[0])
