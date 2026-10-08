backoff has an exponential wait generator but no linear one. Please add `linear`
(each wait grows by a fixed step), plus an `equal_jitter` jitter function, with
tests.
