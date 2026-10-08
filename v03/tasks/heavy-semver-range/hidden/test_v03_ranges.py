# SPDX-License-Identifier: MIT
"""Hidden acceptance for heavy-semver-range: behaviour and the API facts that
docs/DESIGN-NOTES.md plants. Runs beside the snapshot's own tests."""

import importlib
import inspect

import pytest

import semver
from semver import Version


def test_exports():
    assert semver.__all__[-2:] == ["VersionRange", "InvalidRangeError"]
    ranges = importlib.import_module("semver.ranges")
    assert ranges.VersionRange is semver.VersionRange
    assert ranges.InvalidRangeError is semver.InvalidRangeError
    assert issubclass(semver.InvalidRangeError, ValueError)


def test_signatures_and_docstrings():
    R = semver.VersionRange
    for name in ("contains", "max_satisfying"):
        params = inspect.signature(getattr(R, name)).parameters
        kw = {n: p.default for n, p in params.items() if p.kind is p.KEYWORD_ONLY}
        assert kw == {"include_prerelease": False}, name
        assert getattr(R, name).__doc__, name


def test_attributes_repr_str():
    r = semver.VersionRange(" >=1.0.0, <2.0.0 ")
    assert r.expression == " >=1.0.0, <2.0.0 "
    assert repr(r) == "VersionRange(' >=1.0.0, <2.0.0 ')"
    assert str(r) == " >=1.0.0, <2.0.0 "


CASES = [
    # caret
    ("^1.2.3", "1.2.3", True), ("^1.2.3", "1.9.9", True), ("^1.2.3", "2.0.0", False),
    ("^1.2.3", "1.2.2", False), ("^0.2.3", "0.2.9", True), ("^0.2.3", "0.3.0", False),
    ("^0.0.3", "0.0.3", True), ("^0.0.3", "0.0.4", False), ("^0.0.3", "0.0.2", False),
    # tilde
    ("~1.2.3", "1.2.9", True), ("~1.2.3", "1.3.0", False), ("~0.2.3", "0.2.4", True),
    ("~0.2.3", "0.3.0", False), ("~1.2.3", "1.2.2", False),
    # plain operators, default ==
    ("1.2.3", "1.2.3", True), ("1.2.3", "1.2.4", False), ("==1.2.3", "1.2.3+build.5", True),
    ("!=1.2.3", "1.2.4", True), ("!=1.2.3", "1.2.3", False), (">1.2.3", "1.2.4", True),
    (">1.2.3", "1.2.3", False), ("<1.2.3", "1.2.2", True), ("<=1.2.3", "1.2.3", True),
    (">=1.2.3", "1.2.2", False),
    # AND, OR, whitespace
    (">=1.0.0, <2.0.0", "1.5.0", True), (">=1.0.0,<2.0.0", "2.0.0", False),
    (">= 1.0.0 , < 2.0.0", "1.0.0", True), ("^1.0.0 || ^3.0.0", "3.1.0", True),
    ("^1.0.0 || ^3.0.0", "2.1.0", False), ("1.0.0||2.0.0", "2.0.0", True),
    (">=1.0.0, !=1.5.0, <2.0.0", "1.5.0", False),
    # prerelease policy
    (">=1.2.3-alpha.3", "1.2.3-alpha.7", True), (">=1.2.3-alpha.3", "3.4.5-alpha.9", False),
    ("^1.2.3", "1.5.0-beta.1", False), ("^1.2.3", "2.0.0-rc.1", False),
    (">=1.0.0-rc.1, <2.0.0", "1.0.0-rc.2", True), (">=1.0.0-rc.1, <2.0.0", "1.1.0-rc.1", False),
    ("^1.2.3-beta.2", "1.2.3-beta.4", True), ("^1.2.3-beta.2", "1.2.4-beta.4", False),
    ("1.2.3-rc.1", "1.2.3-rc.1", True), (">=1.2.3-rc.1 || >=2.0.0", "2.0.0-rc.1", False),
    ("<2.0.0", "1.9.0-alpha", False),
]


@pytest.mark.parametrize("expression,version,expected", CASES)
def test_contains(expression, version, expected):
    r = semver.VersionRange(expression)
    assert r.contains(version) is expected
    assert r.contains(Version.parse(version)) is expected
    assert (version in r) is expected


@pytest.mark.parametrize(
    "expression,version,expected",
    [("^1.2.3", "1.5.0-beta.1", True), ("^1.2.3", "2.0.0-rc.1", True), ("<2.0.0", "1.9.0-alpha", True),
     (">=1.0.0-rc.1, <2.0.0", "1.1.0-rc.1", True), ("^1.2.3", "1.2.3-rc.1", False)],
)
def test_include_prerelease(expression, version, expected):
    assert semver.VersionRange(expression).contains(version, include_prerelease=True) is expected


def test_max_satisfying():
    r = semver.VersionRange("^1.0.0")
    best = r.max_satisfying(["1.0.0", Version(1, 4, 2), "1.10.0", "2.0.0", "1.11.0-rc.1"])
    assert isinstance(best, Version) and best == Version(1, 10, 0)
    assert r.max_satisfying(["0.9.0", "2.0.0"]) is None
    assert r.max_satisfying([]) is None
    assert r.max_satisfying(["1.0.0", "1.11.0-rc.1"], include_prerelease=True) == Version(1, 11, 0, "rc.1")
    assert isinstance(r.max_satisfying(["1.2.3"]), Version)


@pytest.mark.parametrize(
    "expression,message",
    [
        ("", "empty range expression"),
        ("   ", "empty range expression"),
        (">=1.0.0,", "empty comparator in range '>=1.0.0,'"),
        ("1.0.0 || ", "empty comparator in range '1.0.0 || '"),
        ("|| 1.0.0", "empty comparator in range '|| 1.0.0'"),
        ("=>1.0.0", "invalid comparator '=>1.0.0' in range '=>1.0.0'"),
        (">=1.0.0, ^1.2", "invalid comparator '^1.2' in range '>=1.0.0, ^1.2'"),
        ("1.x", "invalid comparator '1.x' in range '1.x'"),
        ("v1.2.3", "invalid comparator 'v1.2.3' in range 'v1.2.3'"),
        (">=", "invalid comparator '>=' in range '>='"),
        ("*", "invalid comparator '*' in range '*'"),
    ],
)
def test_errors(expression, message):
    with pytest.raises(semver.InvalidRangeError) as exc:
        semver.VersionRange(expression)
    assert str(exc.value) == message


def test_type_errors():
    with pytest.raises(TypeError) as exc:
        semver.VersionRange(5)
    assert str(exc.value) == "range expression must be a str, not int"
    with pytest.raises(TypeError) as exc:
        semver.VersionRange("^1.0.0").contains(1.5)
    assert str(exc.value) == "expected Version or str, not float"
    with pytest.raises(ValueError) as exc:
        semver.VersionRange("^1.0.0").contains("not-a-version")
    assert not isinstance(exc.value, semver.InvalidRangeError)
