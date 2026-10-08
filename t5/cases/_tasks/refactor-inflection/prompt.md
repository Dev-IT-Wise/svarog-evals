`pluralize()` and `singularize()` in `inflection/__init__.py` duplicate the
same logic: skip uncountable words, then apply the first matching rule of a
list. Extract that logic into one private helper, `_inflect(word, rules)`,
and make both functions use it. This is a refactor: no change in behaviour.

Tests: `.venv/bin/python -m pytest -q`
