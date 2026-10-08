# SPDX-License-Identifier: MIT
# T5 hidden acceptance test, feature-cachetools: Cache.resize(maxsize).
import unittest

import cachetools


class Timer:
    def __init__(self):
        self.time = 0

    def __call__(self):
        return self.time


def caches(maxsize, getsizeof=None):
    t = Timer()
    return [
        cachetools.Cache(maxsize, getsizeof=getsizeof),
        cachetools.FIFOCache(maxsize, getsizeof=getsizeof),
        cachetools.LFUCache(maxsize, getsizeof=getsizeof),
        cachetools.LRUCache(maxsize, getsizeof=getsizeof),
        cachetools.RRCache(maxsize, getsizeof=getsizeof),
        cachetools.TTLCache(maxsize, ttl=100, timer=t, getsizeof=getsizeof),
        cachetools.TLRUCache(maxsize, ttu=lambda k, v, now: now + 100, timer=t,
                             getsizeof=getsizeof),
    ]


class TestResize(unittest.TestCase):
    def test_every_class_has_resize_and_reports_maxsize(self):
        for c in caches(3):
            with self.subTest(type(c).__name__):
                c.resize(5)
                self.assertEqual(5, c.maxsize)

    def test_growing_never_evicts(self):
        for c in caches(3):
            with self.subTest(type(c).__name__):
                c.update({1: 1, 2: 2, 3: 3})
                c.resize(10)
                self.assertEqual({1, 2, 3}, set(c))
                c[4] = 4
                self.assertEqual(4, len(c))

    def test_shrinking_fits_currsize(self):
        for c in caches(5):
            with self.subTest(type(c).__name__):
                c.update({k: k for k in range(5)})
                c.resize(2)
                self.assertEqual(2, c.maxsize)
                self.assertLessEqual(c.currsize, 2)
                self.assertEqual(2, len(c))

    def test_shrinking_honours_getsizeof(self):
        for c in caches(10, getsizeof=lambda v: v):
            with self.subTest(type(c).__name__):
                c.update({"a": 3, "b": 3, "c": 3})
                c.resize(4)
                self.assertLessEqual(c.currsize, 4)
                self.assertEqual(1, len(c))

    def test_fifo_drops_oldest(self):
        c = cachetools.FIFOCache(3)
        c.update({1: 1, 2: 2, 3: 3})
        c[1]
        c.resize(1)
        self.assertEqual([3], list(c))

    def test_lru_drops_least_recently_used(self):
        c = cachetools.LRUCache(3)
        c.update({1: 1, 2: 2, 3: 3})
        c[1]
        c.resize(2)
        self.assertEqual({1, 3}, set(c))

    def test_lfu_drops_least_frequently_used(self):
        c = cachetools.LFUCache(3)
        c.update({1: 1, 2: 2, 3: 3})
        c[1], c[1], c[3]
        c.resize(2)
        self.assertEqual({1, 3}, set(c))

    def test_ttl_drops_expired_before_live(self):
        # 1 expires at 10, 2 at 15. Using 1 at 6 makes 2 the least recently
        # used, so an LRU-first eviction would drop the live item.
        t = Timer()
        c = cachetools.TTLCache(2, ttl=10, timer=t)
        c[1] = 1
        t.time = 5
        c[2] = 2
        t.time = 6
        c[1]
        t.time = 11
        c.resize(1)
        self.assertEqual([2], list(c))

    def test_tlru_drops_expired_before_live(self):
        t = Timer()
        c = cachetools.TLRUCache(2, ttu=lambda k, v, now: now + 10, timer=t)
        c[1] = 1
        t.time = 5
        c[2] = 2
        t.time = 6
        c[1]
        t.time = 11
        c.resize(1)
        self.assertEqual([2], list(c))

    def test_inserts_after_shrinking_respect_the_new_size(self):
        for c in caches(5):
            with self.subTest(type(c).__name__):
                c.resize(2)
                c.update({k: k for k in range(5)})
                self.assertEqual(2, len(c))

    def test_negative_maxsize_raises_value_error_and_keeps_the_cache(self):
        for c in caches(3):
            with self.subTest(type(c).__name__):
                c.update({1: 1, 2: 2})
                with self.assertRaises(ValueError):
                    c.resize(-1)
                self.assertEqual(3, c.maxsize)
                self.assertEqual({1, 2}, set(c))
