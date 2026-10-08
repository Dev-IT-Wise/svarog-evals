<!-- SPDX-License-Identifier: MIT -->
# Design notes: counted phrases

The maintainers have decided that inflection gets one helper that joins a
count and a noun into a phrase. These notes record every decision already
taken for it. They are binding: where they answer a question, the answer is
settled and does not need to be asked again.

## Name and placement

- The function is called `quantify`. It is the only new public name.
- It goes in `inflection/__init__.py`, between `pluralize` and `singularize`,
  because the functions in that module are in alphabetical order.
- No new files in the package and no new dependencies.

## Signature

```python
def quantify(count: int, word: str, *, plural: typing.Optional[str] = None) -> str:
```

`count` and `word` are ordinary parameters, so both can be passed by
keyword. `plural` can only be passed by keyword; passing it positionally
raises `TypeError`. `setup.cfg` says `python_requires = >=3.5`, so the
signature has no `/`.

## Behaviour

- `word` is the singular form.
- If `abs(count) == 1`, the word is used as given and is never
  singularized: `quantify(1, "people")` is `"1 people"`.
- For any other count, `0` and negative numbers included, the noun is
  `plural` when it is given, verbatim, and `pluralize(word)` otherwise.
- The result is `str(count)`, one space, then the noun. There is no
  thousands separator, and a negative count keeps its minus sign:
  `quantify(-2, "apple")` is `"-2 apples"`.
- An uncountable word stays as it is, because `pluralize` leaves it alone:
  `quantify(2, "sheep")` is `"2 sheep"`.
- An empty `word` gives the count alone, with no trailing space:
  `quantify(3, "")` is `"3"`.

## Version

`__version__` is not changed. A release bumps it.

## Tests

- New tests go in `test_inflection.py`, as plain `test_*` functions with type
  annotations, like the existing ones.
- Parametrize the table-style cases with `pytest.mark.parametrize`, as the
  existing tests do.

## Docs

- The docstring has an `Examples::` block of doctests, as the other
  functions have. `tox.ini` runs the suite with `--doctest-modules`, so they
  run.
- `README.rst` is not edited.

## Running

The suite is run with `.venv/bin/python -m pytest -q`, and it has to stay
green.
