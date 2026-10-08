# SPDX-License-Identifier: MIT
"""Hidden acceptance for esc-docs-inflection: behaviour that
docs/DESIGN-NOTES.md pins. Runs beside upstream's own tests."""

import pytest

import inflection


@pytest.mark.parametrize(
    ("count", "word", "expected"),
    [
        (1, "apple", "1 apple"),
        (2, "apple", "2 apples"),
        (0, "apple", "0 apples"),
        (-1, "apple", "-1 apple"),
        (-2, "apple", "-2 apples"),
        (1, "people", "1 people"),
        (2, "person", "2 people"),
        (3, "category", "3 categories"),
        (2, "sheep", "2 sheep"),
        (1000000, "box", "1000000 boxes"),
        (3, "", "3"),
        (1, "", "1"),
    ],
)
def test_quantify(count: int, word: str, expected: str) -> None:
    assert inflection.quantify(count, word) == expected


def test_quantify_keyword_arguments() -> None:
    assert inflection.quantify(word="apple", count=2) == "2 apples"


def test_quantify_plural_override() -> None:
    assert inflection.quantify(2, "goose", plural="geese") == "2 geese"
    assert inflection.quantify(0, "goose", plural="geese") == "0 geese"
    assert inflection.quantify(1, "goose", plural="geese") == "1 goose"


def test_quantify_plural_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        inflection.quantify(2, "goose", "geese")  # type: ignore[misc]


def test_quantify_returns_str() -> None:
    assert type(inflection.quantify(2, "apple")) is str
