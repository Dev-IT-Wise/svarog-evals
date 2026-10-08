I'd like a way to make room in a cache before inserting a big value, so I
don't have to guess how many items to evict. Please add a `reserve(size)`
method to `cachetools.Cache` and its subclasses, with tests.
