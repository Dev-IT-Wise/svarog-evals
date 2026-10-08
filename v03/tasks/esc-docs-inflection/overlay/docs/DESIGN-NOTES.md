<!-- SPDX-License-Identifier: MIT -->
# Design notes: counted phrases

The maintainers have decided that inflection gets one helper that joins a
count and a noun into a phrase. These notes record every decision already
taken for it. They are binding: where they answer a question, the answer is
settled and does not need to be asked again.

## Public API

One new public function, and no others:

```python
def quantify(count: int, word: str, *, plural: typing.Optional[str] = None) -> str:
```

- **`count` comes first, then `word`.** This is deliberate and differs from
  every other function in the module, which takes the word first. Those
  functions transform a word. Here the count decides what happens to the
  word, and the result reads count-then-noun. Do not reorder the arguments
  to match `pluralize(word)`, `tableize(word)` and the rest.
- Both are ordinary positional-or-keyword parameters. `/` is not allowed:
  `setup.cfg` says `python_requires = >=3.5`.
- **`plural` is keyword-only**, unlike `separator` in `parameterize`, which
  is positional-or-keyword. `quantify(2, "goose", "geese")` hides what the
  third argument means; `quantify(2, "goose", plural="geese")` does not.
  Passing it positionally must raise `TypeError`.
- Returns `str`.

## Behaviour

`word` is the **singular** form.

- If `abs(count) == 1`, the word is used unchanged: `quantify(1, "people")`
  is `"1 people"`. It is never singularized.
- Any other count, `0` and negative numbers included, uses `plural` when it
  is given, verbatim, and `pluralize(word)` otherwise.
- The result is `str(count)`, one space, then the chosen noun. The count is
  written as plain decimal digits, with no thousands separator, and a
  negative count keeps its minus sign: `quantify(-1, "apple")` is
  `"-1 apple"`, `quantify(-2, "apple")` is `"-2 apples"`.
- An uncountable word is left alone by `pluralize`, so
  `quantify(2, "sheep")` is `"2 sheep"`.
- An empty `word` gives the count and nothing else, with no trailing space:
  `quantify(3, "")` is `"3"`.

## Where the code goes

- In `inflection/__init__.py`, between `pluralize` and `singularize`: the
  functions in that module are in alphabetical order.
- `__version__` is not changed. A release bumps it.
- No new dependencies and no new files in the package.

## Tests and docs

- New tests go in `test_inflection.py`, as plain `test_*` functions with type
  annotations, like the existing ones.
- The docstring has a `Examples::` block of doctests, as the other functions
  do. `tox.ini` runs the suite with `--doctest-modules`, so they run.
- The suite is run with `.venv/bin/python -m pytest -q`, and it has to stay
  green.
