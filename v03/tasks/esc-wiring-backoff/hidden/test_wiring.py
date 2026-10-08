# SPDX-License-Identifier: MIT
"""Hidden acceptance for esc-wiring-backoff: the public path only."""
import asyncio
import math
import re
import unittest.mock as mock
from pathlib import Path

import backoff

OLD = {"on_predicate", "on_exception", "constant", "expo", "decay", "fibo",
       "runtime", "full_jitter", "random_jitter"}


def test_exports():
    assert hasattr(backoff, "linear") and hasattr(backoff, "equal_jitter")
    assert set(backoff.__all__) == OLD | {"linear", "equal_jitter"}
    assert len(backoff.__all__) == len(set(backoff.__all__))
    ns = {}
    exec("from backoff import *", ns)
    assert callable(ns["linear"]) and callable(ns["equal_jitter"])


def test_linear_values():
    gen = backoff.linear()
    gen.send(None)
    assert [next(gen) for _ in range(4)] == [1, 2, 3, 4]
    gen = backoff.linear(start=2, step=3)
    gen.send(None)
    assert [next(gen) for _ in range(4)] == [2, 5, 8, 11]


def test_linear_cap():
    gen = backoff.linear(start=1, step=2, max_value=6)
    gen.send(None)
    assert [next(gen) for _ in range(6)] == [1, 3, 5, 6, 6, 6]


def test_equal_jitter_range():
    vals = [backoff.equal_jitter(8) for _ in range(300)]
    assert all(4 <= v <= 8 for v in vals)
    assert len(set(vals)) > 1
    assert backoff.equal_jitter(0) == 0


def test_readme_lists():
    text = (Path(__file__).resolve().parent.parent / "README.md").read_text()
    for name in ("linear", "equal_jitter"):
        assert re.search(r"^- `backoff\.%s` - \S" % name, text, re.M), name


def test_sync_decorators():
    calls = []

    @backoff.on_exception(backoff.linear, ValueError, max_tries=3,
                          jitter=backoff.equal_jitter, start=2, step=2)
    def boom():
        calls.append(1)
        raise ValueError

    with mock.patch("time.sleep") as sleep:
        try:
            boom()
        except ValueError:
            pass
    assert len(calls) == 3
    waits = [c.args[0] for c in sleep.call_args_list]
    assert len(waits) == 2
    assert 1 <= waits[0] <= 2 and 2 <= waits[1] <= 4

    @backoff.on_predicate(backoff.linear, max_tries=3, jitter=None, step=5)
    def nope():
        return None

    with mock.patch("time.sleep") as sleep:
        nope()
    assert [c.args[0] for c in sleep.call_args_list] == [1, 6]


def test_async_decorators():
    async def fake_sleep(s):
        slept.append(s)

    slept = []

    @backoff.on_exception(backoff.linear, ValueError, max_tries=3,
                          jitter=backoff.equal_jitter, start=2, step=2)
    async def boom():
        raise ValueError

    async def run():
        try:
            await boom()
        except ValueError:
            pass

    with mock.patch("asyncio.sleep", fake_sleep):
        asyncio.run(run())
    assert len(slept) == 2
    assert 1 <= slept[0] <= 2 and 2 <= slept[1] <= 4
