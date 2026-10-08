# SPDX-License-Identifier: MIT
import unittest

from cachetools import FIFOCache, LFUCache, LRUCache, RRCache, TLRUCache, TTLCache


class Timer:
    def __init__(self):
        self.time = 0

    def __call__(self):
        return self.time


def makers(maxsize, getsizeof=None):
    t = Timer()
    return [
        FIFOCache(maxsize, getsizeof=getsizeof),
        LFUCache(maxsize, getsizeof=getsizeof),
        LRUCache(maxsize, getsizeof=getsizeof),
        RRCache(maxsize, getsizeof=getsizeof),
        TTLCache(maxsize, ttl=10, timer=t, getsizeof=getsizeof),
        TLRUCache(maxsize, ttu=lambda k, v, now: now + 10, timer=t, getsizeof=getsizeof),
    ]


def fill(cache, n):
    for i in range(n):
        cache[i] = i
    return cache


class ReserveTest(unittest.TestCase):
    def test_makes_room_and_inserts_nothing(self):
        for cache in makers(4):
            fill(cache, 4)
            self.assertIsNone(cache.reserve(3), type(cache).__name__)
            self.assertLessEqual(cache.currsize, 1, type(cache).__name__)
            self.assertEqual(cache.currsize, len(cache))

    def test_room_already_there_evicts_nothing(self):
        for cache in makers(5):
            fill(cache, 3)
            cache.reserve(2)
            self.assertEqual({0, 1, 2}, set(cache), type(cache).__name__)

    def test_order_fifo_and_lru(self):
        c = fill(FIFOCache(3), 3)
        c.reserve(2)
        self.assertEqual({2}, set(c))
        c = fill(LRUCache(3), 3)
        c[0]
        c.reserve(1)
        self.assertEqual({2, 0}, set(c))

    def test_size_is_in_getsizeof_units(self):
        for cache in makers(10, getsizeof=len):
            cache["a"] = "xxxx"
            cache["b"] = "yyyy"
            cache.reserve(5)
            self.assertLessEqual(cache.currsize, 5, type(cache).__name__)
            self.assertGreaterEqual(len(cache), 1, type(cache).__name__)

    def test_too_large_raises_and_leaves_cache_untouched(self):
        for cache in makers(4):
            fill(cache, 3)
            with self.assertRaises(ValueError):
                cache.reserve(5)
            self.assertEqual({0, 1, 2}, set(cache), type(cache).__name__)
            self.assertEqual(3, cache.currsize)

    def test_too_large_on_empty_cache_is_value_error(self):
        for cache in makers(4):
            with self.assertRaises(ValueError):
                cache.reserve(5)

    def test_negative_raises_and_leaves_cache_untouched(self):
        for cache in makers(4):
            fill(cache, 4)
            with self.assertRaises(ValueError):
                cache.reserve(-1)
            self.assertEqual({0, 1, 2, 3}, set(cache), type(cache).__name__)

    def test_zero_never_evicts(self):
        for cache in makers(4):
            fill(cache, 4)
            cache.reserve(0)
            self.assertEqual(4, len(cache), type(cache).__name__)

    def test_size_equal_to_maxsize_empties_the_cache(self):
        for cache in makers(4):
            fill(cache, 4)
            cache.reserve(4)
            self.assertEqual(0, len(cache), type(cache).__name__)
            self.assertEqual(0, cache.currsize)

    def test_timed_caches_drop_expired_before_live_items(self):
        for cache in makers(4)[4:]:
            t = cache.timer
            cache[0] = 0
            cache[1] = 1
            t.time = 5
            cache[2] = 2
            cache[3] = 3
            t.time = 10
            cache.reserve(2)
            self.assertEqual({2, 3}, set(cache), type(cache).__name__)


if __name__ == "__main__":
    unittest.main()
