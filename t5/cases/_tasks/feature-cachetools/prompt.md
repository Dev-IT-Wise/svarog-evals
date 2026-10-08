Add a `resize(maxsize)` method to `cachetools.Cache`, so that every cache
class has it. After the call `cache.maxsize` is the new value. If
`currsize` is then above it, items are evicted the way that class evicts
on insert until `currsize <= maxsize`: FIFOCache drops the oldest item,
LRUCache the least recently used, LFUCache the least frequently used,
RRCache random items, and TTLCache and TLRUCache first drop expired items,
then follow their own order. Sizes come from `getsizeof`, as everywhere
else in the library. Growing never evicts. A negative `maxsize` raises
`ValueError`, as the constructor does, and leaves the cache unchanged.

Tests: `PYTHONPATH=src .venv/bin/python -m pytest -q`
