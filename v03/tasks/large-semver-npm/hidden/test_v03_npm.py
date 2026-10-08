# SPDX-License-Identifier: MIT
"""Hidden acceptance for large-semver-npm: the public API, expansion table,
prerelease rule and error messages that docs/DESIGN-NOTES.md pins."""

import importlib

import pytest

import semver
from semver import Comparator, InvalidRangeError, Range, Version, satisfies


def V(text):
    return Version.parse(text)


def C(op, text):
    return Comparator(op, V(text) if text is not None else None)


# ---------------------------------------------------------------- public API


def test_exports_order():
    assert semver.__all__[-4:] == ["Range", "Comparator", "InvalidRangeError", "satisfies"]


def test_exports_come_from_ranges_module():
    ranges = importlib.import_module("semver.ranges")
    assert ranges.Range is semver.Range
    assert ranges.Comparator is semver.Comparator
    assert ranges.InvalidRangeError is semver.InvalidRangeError
    assert ranges.satisfies is semver.satisfies
    assert isinstance(semver.Range, type)
    assert isinstance(semver.Comparator, type)
    assert issubclass(semver.InvalidRangeError, ValueError)
    assert callable(semver.satisfies)


# ---------------------------------------------------------------- Comparator


@pytest.mark.parametrize("op", ["<", "<=", ">", ">=", "=", ""])
def test_comparator_attributes(op):
    version = None if op == "" else V("1.2.3")
    c = Comparator(op, version)
    assert c.operator == op
    assert c.version == version
    if op == "":
        assert c.version is None


@pytest.mark.parametrize("op", ["==", "!=", "=>", "=<", "~", "^", " ", "x"])
def test_comparator_unknown_operator(op):
    with pytest.raises(ValueError) as exc:
        Comparator(op, V("1.2.3"))
    assert str(exc.value) == "unknown operator %r" % op


@pytest.mark.parametrize(
    "op,text,expected",
    [
        (">=", "1.2.0", ">=1.2.0"),
        (">", "1.2.0", ">1.2.0"),
        ("<", "2.0.0-0", "<2.0.0-0"),
        ("<=", "2.3.4", "<=2.3.4"),
        ("=", "1.2.3", "1.2.3"),
        ("=", "1.2.3-beta.2", "1.2.3-beta.2"),
        ("", None, "*"),
    ],
)
def test_comparator_str(op, text, expected):
    assert str(C(op, text)) == expected


@pytest.mark.parametrize(
    "op,bound,candidate,expected",
    [
        ("<", "1.2.3", "1.2.2", True),
        ("<", "1.2.3", "1.2.3", False),
        ("<=", "1.2.3", "1.2.3", True),
        ("<=", "1.2.3", "1.2.4", False),
        (">", "1.2.3", "1.2.4", True),
        (">", "1.2.3", "1.2.3", False),
        (">=", "1.2.3", "1.2.3", True),
        (">=", "1.2.3", "1.2.2", False),
        ("=", "1.2.3", "1.2.3", True),
        ("=", "1.2.3", "1.2.4", False),
        ("=", "1.2.3", "1.2.3+build.9", True),
        (">=", "1.2.3+a", "1.2.3+b", True),
        # no prerelease rules at the comparator level, only Version ordering
        ("<", "3.0.0", "3.0.0-rc.1", True),
        (">=", "1.0.0", "2.0.0-rc.1", True),
        (">", "1.2.3-alpha.3", "3.4.5-alpha.9", True),
        ("<", "1.2.3", "1.2.3-alpha", True),
    ],
)
def test_comparator_test(op, bound, candidate, expected):
    assert C(op, bound).test(V(candidate)) is expected


@pytest.mark.parametrize("candidate", ["0.0.0", "1.2.3", "9.9.9-rc.1", "1.0.0+b"])
def test_comparator_any_version(candidate):
    assert C("", None).test(V(candidate)) is True


def test_comparator_equality_and_hash():
    a = C(">=", "1.2.0")
    b = C(">=", "1.2.0")
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1
    assert a != C(">", "1.2.0")
    assert a != C(">=", "1.2.1")
    assert C("=", "1.2.3") != C(">=", "1.2.3")
    assert C("", None) == C("", None)
    assert hash(C("", None)) == hash(C("", None))
    assert len({C("", None), C("", None), a, b}) == 2


# --------------------------------------------------------------------- Range


@pytest.mark.parametrize("bad,name", [(5, "int"), (None, "NoneType"), (1.5, "float"), (b"1", "bytes")])
def test_range_type_error(bad, name):
    with pytest.raises(TypeError) as exc:
        Range(bad)
    assert str(exc.value) == "range expression must be a str, not %s" % name


@pytest.mark.parametrize("expression", ["^1.2", "  >=1.0.0   <2.0.0 ", "", "  ", "1.0.0||2.0.0", "v1.2.3"])
def test_range_expression_as_given(expression):
    assert Range(expression).expression == expression


def test_invalid_range_error_is_value_error():
    with pytest.raises(ValueError):
        Range("=>1.0.0")
    with pytest.raises(InvalidRangeError):
        Range("=>1.0.0")


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("*", ((C("", None),),)),
        ("", ((C("", None),),)),
        ("   ", ((C("", None),),)),
        ("1.2.3", ((C("=", "1.2.3"),),)),
        ("^1.2", ((C(">=", "1.2.0"), C("<", "2.0.0-0")),)),
        ("1.0.0 || >=2.0.0 <3.0.0", ((C("=", "1.0.0"),), (C(">=", "2.0.0"), C("<", "3.0.0")))),
        ("1.2.3 || ", ((C("=", "1.2.3"),), (C("", None),))),
        ("1.2.3 - 2.3", ((C(">=", "1.2.3"), C("<", "2.4.0-0")),)),
        (">*", ((C("<", "0.0.0-0"),),)),
        (">=*", ((C("", None),),)),
        ("~1.2.3-beta.2", ((C(">=", "1.2.3-beta.2"), C("<", "1.3.0-0")),)),
        ("  >=  1.0.0    <2.0.0 ", ((C(">=", "1.0.0"), C("<", "2.0.0")),)),
        ("v1.2.3", ((C("=", "1.2.3"),),)),
        ("=1.2.3", ((C("=", "1.2.3"),),)),
    ],
)
def test_range_sets(expression, expected):
    sets = Range(expression).sets
    assert isinstance(sets, tuple)
    assert all(isinstance(s, tuple) for s in sets)
    assert sets == expected


EXPANSION = [
    ("*", "*"),
    ("x", "*"),
    ("X", "*"),
    ("", "*"),
    ("1", ">=1.0.0 <2.0.0-0"),
    ("1.x", ">=1.0.0 <2.0.0-0"),
    ("1.x.x", ">=1.0.0 <2.0.0-0"),
    ("1.*", ">=1.0.0 <2.0.0-0"),
    ("1.X.X", ">=1.0.0 <2.0.0-0"),
    ("1.2", ">=1.2.0 <1.3.0-0"),
    ("1.2.x", ">=1.2.0 <1.3.0-0"),
    ("1.2.*", ">=1.2.0 <1.3.0-0"),
    ("1.2.3", "1.2.3"),
    ("1.2.3 - 2.3.4", ">=1.2.3 <=2.3.4"),
    ("1.2 - 2.3.4", ">=1.2.0 <=2.3.4"),
    ("1.2.3 - 2.3", ">=1.2.3 <2.4.0-0"),
    ("1.2.3 - 2", ">=1.2.3 <3.0.0-0"),
    ("~1.2.3", ">=1.2.3 <1.3.0-0"),
    ("~1.2", ">=1.2.0 <1.3.0-0"),
    ("~1", ">=1.0.0 <2.0.0-0"),
    ("~0.2.3", ">=0.2.3 <0.3.0-0"),
    ("^1.2.3", ">=1.2.3 <2.0.0-0"),
    ("^0.2.3", ">=0.2.3 <0.3.0-0"),
    ("^0.0.3", ">=0.0.3 <0.0.4-0"),
    ("^1.2.x", ">=1.2.0 <2.0.0-0"),
    ("^0.0.x", ">=0.0.0 <0.1.0-0"),
    ("^0.0", ">=0.0.0 <0.1.0-0"),
    ("^1.x", ">=1.0.0 <2.0.0-0"),
    ("^0.x", ">=0.0.0 <1.0.0-0"),
    (">1", ">=2.0.0"),
    (">1.2", ">=1.3.0"),
    (">=1.2", ">=1.2.0"),
    ("<1.2", "<1.2.0-0"),
    ("<=1.2", "<1.3.0-0"),
    (">*", "<0.0.0-0"),
    ("<*", "<0.0.0-0"),
    (">=*", "*"),
    ("<=*", "*"),
    ("~1.2.3-beta.2", ">=1.2.3-beta.2 <1.3.0-0"),
    ("^1.2.3-beta.2", ">=1.2.3-beta.2 <2.0.0-0"),
    # full-version primitives, build metadata dropped, prerelease kept on the lower end
    (">1.2.3", ">1.2.3"),
    ("<=1.2.3", "<=1.2.3"),
    (">=1.2.3-beta.1", ">=1.2.3-beta.1"),
    ("1.2.3+build.5", "1.2.3"),
    ("^1.2.3+build.5", ">=1.2.3 <2.0.0-0"),
    # whitespace, v and = prefixes
    ("  ^1.2  ", ">=1.2.0 <2.0.0-0"),
    (">= 1.2.3", ">=1.2.3"),
    ("^ 1.2", ">=1.2.0 <2.0.0-0"),
    ("v1.2.3", "1.2.3"),
    ("=1.2.3", "1.2.3"),
    ("^v1.2.3", ">=1.2.3 <2.0.0-0"),
    (">=v1.2.3", ">=1.2.3"),
    # AND, OR, empty set
    (">=1.0.0 <2.0.0-0", ">=1.0.0 <2.0.0-0"),
    ("  >=1.0.0    <2.0.0  ", ">=1.0.0 <2.0.0"),
    ("1.x || >=2.5.0", ">=1.0.0 <2.0.0-0 || >=2.5.0"),
    ("1.0.0||2.0.0", "1.0.0 || 2.0.0"),
    ("1.0.0   ||   2.0.0", "1.0.0 || 2.0.0"),
    ("^1.2 || >=3.0.0 <4.0.0", ">=1.2.0 <2.0.0-0 || >=3.0.0 <4.0.0"),
    ("1.2.3 || ", "1.2.3 || *"),
]


@pytest.mark.parametrize("expression,expected", EXPANSION)
def test_expansion_str(expression, expected):
    assert str(Range(expression)) == expected


# ------------------------------------------------------------------ contains

CONTAINS = [
    ("*", "0.0.0", True),
    ("*", "1.2.3", True),
    ("", "5.0.0", True),
    ("1.x", "1.9.9", True),
    ("1.x", "2.0.0", False),
    ("1.x", "0.9.9", False),
    ("1.2", "1.2.9", True),
    ("1.2", "1.3.0", False),
    ("1.2.3", "1.2.3", True),
    ("1.2.3", "1.2.4", False),
    ("1.2.3", "1.2.3+build.5", True),
    ("^1.2.3", "1.2.3", True),
    ("^1.2.3", "1.9.9", True),
    ("^1.2.3", "2.0.0", False),
    ("^1.2.3", "1.2.2", False),
    ("^0.2.3", "0.2.9", True),
    ("^0.2.3", "0.3.0", False),
    ("^0.0.3", "0.0.3", True),
    ("^0.0.3", "0.0.4", False),
    ("~1.2.3", "1.2.9", True),
    ("~1.2.3", "1.3.0", False),
    ("~1.2.3", "1.2.2", False),
    ("1.2.3 - 2.3.4", "1.2.3", True),
    ("1.2.3 - 2.3.4", "2.3.4", True),
    ("1.2.3 - 2.3.4", "2.3.5", False),
    ("1.2.3 - 2.3.4", "1.2.2", False),
    ("1.2.3 - 2.3", "2.3.9", True),
    ("1.2.3 - 2.3", "2.4.0", False),
    ("1.2.3 - 2", "2.9.9", True),
    ("1.2.3 - 2", "3.0.0", False),
    (">1", "1.9.9", False),
    (">1", "2.0.0", True),
    (">1.2", "1.2.9", False),
    (">1.2", "1.3.0", True),
    (">=1.2", "1.2.0", True),
    ("<1.2", "1.1.9", True),
    ("<1.2", "1.2.0", False),
    ("<=1.2", "1.2.9", True),
    ("<=1.2", "1.3.0", False),
    (">1.2.3", "1.2.3", False),
    (">1.2.3", "1.2.4", True),
    ("<=1.2.3", "1.2.3", True),
    (">*", "1.0.0", False),
    (">*", "0.0.0", False),
    ("<*", "0.0.0", False),
    (">=*", "3.0.0", True),
    ("<=*", "3.0.0", True),
    (">=1.0.0 <2.0.0-0", "1.9.0", True),
    (">=1.0.0 <2.0.0-0", "2.0.0", False),
    (">=1.0.0 <2.0.0", "2.0.0", False),
    (">2.0.0 <1.0.0", "1.5.0", False),
    ("1.x || >=2.5.0", "1.3.0", True),
    ("1.x || >=2.5.0", "2.4.0", False),
    ("1.x || >=2.5.0", "2.5.0", True),
    ("1.x || >=2.5.0", "3.0.0", True),
    ("1.0.0 || 3.0.0", "3.0.0", True),
    ("1.0.0 || 3.0.0", "2.0.0", False),
    ("1.2.3 || ", "9.9.9", True),
    ("v1.2.3", "1.2.3", True),
    ("=1.2.3", "1.2.3", True),
    # prerelease rule, the three examples of the notes
    (">1.2.3-alpha.3", "1.2.3-alpha.7", True),
    (">1.2.3-alpha.3", "3.4.5-alpha.9", False),
    ("^1.2.3", "1.5.0-beta.1", False),
    ("^1.2.3", "2.0.0-rc.1", False),
    ("1.x", "1.5.0-beta.1", False),
    ("1.x", "2.0.0-0", False),
    # prerelease rule, further consequences
    (">1.2.3-alpha.3", "1.2.4-alpha.1", False),
    (">=1.2.3-alpha.3", "1.2.3-alpha.1", False),
    (">=1.2.3-alpha.3", "1.2.3", True),
    (">=1.2.3-alpha.3", "2.0.0", True),
    (">=1.2.3-alpha.3 <2.0.0", "1.2.3-alpha.7", True),
    (">=1.2.3-alpha.3 <2.0.0", "1.2.4-alpha.1", False),
    ("<2.0.0 || >=1.2.3-alpha.3", "1.2.3-alpha.7", True),
    ("^2.0.0 || >=1.2.3-alpha.3", "1.2.3-alpha.7", True),
    ("^1.2.3-beta.2", "1.2.3-beta.4", True),
    ("^1.2.3-beta.2", "1.2.4-beta.4", False),
    ("~1.2.3-beta.2", "1.2.3-beta.9", True),
    ("1.2.3-rc.1", "1.2.3-rc.1", True),
    (">=1.2.3-rc.1 <1.2.3-rc.5", "1.2.3-rc.3", True),
    ("*", "1.0.0-alpha", False),
    ("<2.0.0", "1.9.0-alpha", False),
    ("<1.2", "1.1.0-alpha", False),
]


@pytest.mark.parametrize("expression,version,expected", CONTAINS)
def test_contains(expression, version, expected):
    rng = Range(expression)
    assert rng.contains(version) is expected
    assert rng.contains(V(version)) is expected


@pytest.mark.parametrize("expression,version,expected", CONTAINS)
def test_in_operator(expression, version, expected):
    rng = Range(expression)
    assert (version in rng) is expected
    assert (V(version) in rng) is expected


@pytest.mark.parametrize(
    "expression,version,expected",
    [
        ("^1.2.3", "1.5.0-beta.1", True),
        ("^1.2.3", "2.0.0-rc.1", False),
        ("^1.2.3", "1.2.3-rc.1", False),
        ("1.x", "1.5.0-beta.1", True),
        ("1.x", "2.0.0-0", False),
        ("*", "1.0.0-alpha", True),
        ("<2.0.0", "1.9.0-alpha", True),
        ("<1.2", "1.1.0-alpha", True),
        ("<1.2", "1.2.0-alpha", False),
        (">1.2.3-alpha.3", "3.4.5-alpha.9", True),
        (">=1.2.3-alpha.3", "1.2.4-alpha.1", True),
        (">=1.2.3-alpha.3", "1.2.3-alpha.1", False),
        ("1.2.3", "1.2.3-rc.1", False),
    ],
)
def test_include_prerelease(expression, version, expected):
    rng = Range(expression)
    assert rng.contains(version, include_prerelease=True) is expected
    assert rng.contains(V(version), include_prerelease=True) is expected


def test_contains_include_prerelease_is_keyword_only():
    with pytest.raises(TypeError):
        Range("^1.2.3").contains("1.5.0", True)


@pytest.mark.parametrize("bad,name", [(1, "int"), (1.5, "float"), (None, "NoneType"), (b"1.0.0", "bytes")])
def test_contains_type_error(bad, name):
    with pytest.raises(TypeError) as exc:
        Range("^1.0.0").contains(bad)
    assert str(exc.value) == "expected Version or str, not %s" % name


def test_in_operator_type_error():
    with pytest.raises(TypeError) as exc:
        1 in Range("^1.0.0")
    assert str(exc.value) == "expected Version or str, not int"


@pytest.mark.parametrize("text", ["not-a-version", "1.2", "1.2.3.4", ""])
def test_contains_invalid_version_string_propagates(text):
    with pytest.raises(ValueError) as expected:
        Version.parse(text)
    with pytest.raises(ValueError) as exc:
        Range("^1.0.0").contains(text)
    assert not isinstance(exc.value, InvalidRangeError)
    assert str(exc.value) == str(expected.value)


# -------------------------------------------- max / min satisfying and filter


def test_max_satisfying():
    rng = Range("^1.0.0")
    best = rng.max_satisfying(["1.0.0", V("1.4.2"), "1.10.0", "2.0.0", "1.11.0-rc.1", "0.9.0"])
    assert isinstance(best, Version)
    assert best == V("1.10.0")
    assert rng.max_satisfying(["0.9.0", "2.0.0"]) is None
    assert rng.max_satisfying([]) is None
    assert rng.max_satisfying(iter(["1.2.0", "1.3.0"])) == V("1.3.0")
    assert isinstance(rng.max_satisfying(["1.2.3"]), Version)
    assert isinstance(rng.max_satisfying([V("1.2.3")]), Version)


def test_max_satisfying_include_prerelease():
    rng = Range("^1.0.0")
    versions = ["1.0.0", "1.11.0-rc.1", "1.2.0"]
    assert rng.max_satisfying(versions) == V("1.2.0")
    assert rng.max_satisfying(versions, include_prerelease=True) == V("1.11.0-rc.1")


def test_min_satisfying():
    rng = Range("^1.0.0")
    best = rng.min_satisfying(["1.4.2", V("1.0.1"), "1.10.0", "2.0.0", "0.9.0", "1.0.1-rc.1"])
    assert isinstance(best, Version)
    assert best == V("1.0.1")
    assert rng.min_satisfying(["0.9.0", "2.0.0"]) is None
    assert rng.min_satisfying([]) is None
    assert isinstance(rng.min_satisfying(["1.2.3"]), Version)


def test_min_satisfying_include_prerelease():
    rng = Range("^1.0.0")
    versions = ["1.2.0", "1.1.0-rc.1", "1.3.0"]
    assert rng.min_satisfying(versions) == V("1.2.0")
    assert rng.min_satisfying(versions, include_prerelease=True) == V("1.1.0-rc.1")


def test_filter_keeps_order_and_duplicates():
    rng = Range("^1.0.0")
    result = rng.filter(["1.4.0", "2.0.0", V("1.0.0"), "1.4.0", "1.5.0-beta.1", "0.9.0"])
    assert isinstance(result, list)
    assert all(isinstance(v, Version) for v in result)
    assert result == [V("1.4.0"), V("1.0.0"), V("1.4.0")]


def test_filter_include_prerelease_and_empty():
    rng = Range("^1.0.0")
    versions = ["1.4.0", "1.5.0-beta.1", "2.0.0", "1.4.0"]
    assert rng.filter(versions, include_prerelease=True) == [V("1.4.0"), V("1.5.0-beta.1"), V("1.4.0")]
    assert rng.filter([]) == []
    assert rng.filter(["2.0.0", "0.1.0"]) == []


# --------------------------------------------------------------- min_version


@pytest.mark.parametrize(
    "expression,expected",
    [
        (">=1.2.3", "1.2.3"),
        (">1.2.3", "1.2.4"),
        ("*", "0.0.0"),
        ("<2.0.0", "0.0.0"),
        # 0.0.0
        ("^0.0.0", "0.0.0"),
        ("1.2.3 || <1.0.0", "0.0.0"),
        # a comparator's own version
        ("1.2.3 - 2.3.4", "1.2.3"),
        ("^1.2.3", "1.2.3"),
        (">=1.0.0 <2.0.0-0 || >5.0.0", "1.0.0"),
        (">=1.2.3-beta.1", "1.2.3-beta.1"),
        ("~1.2.3-beta.2", "1.2.3-beta.2"),
        # the version right after a >V comparator, V without and with prerelease
        (">1.2.3 <1.2.5", "1.2.4"),
        (">1.2.3-beta", "1.2.3-beta.0"),
        (">1.2.3-beta.2", "1.2.3-beta.2.0"),
    ],
)
def test_min_version(expression, expected):
    result = Range(expression).min_version()
    assert isinstance(result, Version)
    assert result == V(expected)


@pytest.mark.parametrize("expression", [">2.0.0 <1.0.0", ">*", "<*", ">=2.0.0 <1.0.0"])
def test_min_version_none(expression):
    assert Range(expression).min_version() is None


# ---------------------------------------------------------------- intersects


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("^1.2", ">=1.5.0 <3.0.0", True),
        ("^1.0.0", "^2.0.0", False),
        ("1.x", "1.5.0", True),
        ("<1.0.0", ">=1.0.0", False),
        ("^1.0.0 || ^3.0.0", "^3.5.0", True),
        ("^1.0.0 || ^3.0.0", "^2.0.0", False),
        ("*", "1.2.3", True),
        ("1.2.3", "1.2.4", False),
        ("1.2.3", "1.2.3", True),
        (">=1.0.0", "<=1.0.0", True),
        (">1.0.0", "<=1.0.0", False),
        ("^1.2.3", "^1.0.0", True),
        ("1.2.3 - 2.3.4", "2.3.4 - 3.0.0", True),
        ("1.2.3 - 2.3.4", "2.3.5 - 3.0.0", False),
        (">=1.0.0-alpha <1.0.0", "<1.0.0-beta", True),
        (">*", "*", False),
        (">2.0.0 <1.0.0", "*", False),
    ],
)
def test_intersects(a, b, expected):
    assert Range(a).intersects(Range(b)) is expected
    assert Range(b).intersects(Range(a)) is expected
    assert Range(a).intersects(b) is expected
    assert Range(b).intersects(a) is expected


@pytest.mark.parametrize("bad,name", [(1, "int"), (None, "NoneType"), (1.5, "float")])
def test_intersects_type_error(bad, name):
    with pytest.raises(TypeError) as exc:
        Range("^1.0.0").intersects(bad)
    assert str(exc.value) == "expected Range or str, not %s" % name


# ---------------------------------------------- repr, str, equality and hash


@pytest.mark.parametrize("expression", [">=1.0.0 <2.0.0", "  ^1.2 ", "1.x || 3.x", ""])
def test_repr(expression):
    assert repr(Range(expression)) == "Range(%r)" % expression
    assert repr(Range(">=1.0.0 <2.0.0")) == "Range('>=1.0.0 <2.0.0')"


def test_str_normalised():
    assert str(Range("^1.2")) == ">=1.2.0 <2.0.0-0"


def test_range_equality_and_hash():
    a = Range("^1.2")
    b = Range(">=1.2.0 <2.0.0-0")
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1
    assert Range("1.0.0||2.0.0") == Range("1.0.0 || 2.0.0")
    assert hash(Range("1.0.0||2.0.0")) == hash(Range("1.0.0 || 2.0.0"))
    assert Range("") == Range("*")
    assert Range("^1.2") != Range("^1.3")
    assert Range("1.0.0 || 2.0.0") != Range("1.0.0")
    assert len({Range("^1.2"), Range("^1.3"), Range("~1.2")}) == 3


# ----------------------------------------------------------------- satisfies


@pytest.mark.parametrize(
    "version,expression,expected",
    [
        ("1.2.3", "^1.0.0", True),
        ("2.0.0", "^1.0.0", False),
        ("1.5.0", "1.x || >=2.5.0", True),
        ("2.4.0", "1.x || >=2.5.0", False),
        ("1.2.3", "", True),
        ("1.5.0-beta.1", "^1.2.3", False),
        ("1.2.3-alpha.7", ">1.2.3-alpha.3", True),
    ],
)
def test_satisfies(version, expression, expected):
    assert satisfies(version, expression) is expected
    assert satisfies(V(version), expression) is expected
    assert satisfies(version, Range(expression)) is expected
    assert satisfies(V(version), Range(expression)) is expected


@pytest.mark.parametrize(
    "version,expression,expected",
    [("1.5.0-beta.1", "^1.2.3", True), ("2.0.0-rc.1", "^1.2.3", False), ("1.9.0-alpha", "<2.0.0", True)],
)
def test_satisfies_include_prerelease(version, expression, expected):
    assert satisfies(version, expression, include_prerelease=True) is expected
    assert satisfies(version, Range(expression), include_prerelease=True) is expected


def test_satisfies_include_prerelease_is_keyword_only():
    with pytest.raises(TypeError):
        satisfies("1.5.0", "^1.0.0", True)


def test_satisfies_errors():
    with pytest.raises(InvalidRangeError):
        satisfies("1.2.3", "=>1.0.0")
    with pytest.raises(TypeError) as exc:
        satisfies(1, "^1.0.0")
    assert str(exc.value) == "expected Version or str, not int"
    with pytest.raises(TypeError) as exc:
        satisfies("1.2.3", 5)
    assert str(exc.value) == "range expression must be a str, not int"


# -------------------------------------------------------------------- errors


@pytest.mark.parametrize(
    "expression,message",
    [
        ("=>1.0.0", "invalid comparator '=>1.0.0' in range '=>1.0.0'"),
        ("1.2.3.4", "invalid comparator '1.2.3.4' in range '1.2.3.4'"),
        ("01.2.3", "invalid comparator '01.2.3' in range '01.2.3'"),
        ("1.x.3", "invalid comparator '1.x.3' in range '1.x.3'"),
        ("^", "invalid comparator '^' in range '^'"),
        ("abc", "invalid comparator 'abc' in range 'abc'"),
        (">=1.0.0 =>2.0.0", "invalid comparator '=>2.0.0' in range '>=1.0.0 =>2.0.0'"),
        ("1.0.0 || 1.2.3.4", "invalid comparator '1.2.3.4' in range '1.0.0 || 1.2.3.4'"),
        ("1.2-beta", "prerelease on a partial version in range '1.2-beta'"),
        ("^1.2-beta", "prerelease on a partial version in range '^1.2-beta'"),
        (">=1.2-beta.1 <2.0.0", "prerelease on a partial version in range '>=1.2-beta.1 <2.0.0'"),
        ("1.2.3 -", "incomplete hyphen range in range '1.2.3 -'"),
        ("- 2.0.0", "incomplete hyphen range in range '- 2.0.0'"),
        ("^1.0.0 || 1.2.3 -", "incomplete hyphen range in range '^1.0.0 || 1.2.3 -'"),
    ],
)
def test_errors(expression, message):
    with pytest.raises(InvalidRangeError) as exc:
        Range(expression)
    assert str(exc.value) == message


def test_errors_through_satisfies_same_message():
    with pytest.raises(InvalidRangeError) as exc:
        satisfies("1.2.3", "1.2-beta")
    assert str(exc.value) == "prerelease on a partial version in range '1.2-beta'"
