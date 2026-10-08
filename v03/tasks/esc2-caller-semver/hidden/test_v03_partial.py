# SPDX-License-Identifier: MIT
"""Hidden acceptance for esc2-caller-semver: the behaviour docs/DESIGN-NOTES.md
pins. Runs beside the snapshot's tests."""

import operator

import pytest

from semver import Version

from semverwithvprefix import SemVerWithVPrefix


@pytest.mark.parametrize(
    "left,right,expected",
    [
        ("1.2.0", "1.2", 0), ("1.0.0", "1", 0), ("1.2.3", "1.2", 1), ("1.1.9", "1.2", -1),
        ("0.0.0", "0", 0), ("10.0.0", "9", 1), ("1.2.0-rc.1", "1.2", -1),
        ("1.2.0-rc.1", "1.2-rc.1", 0), ("1.2.0+b.1", "1.2+b.2", 0), ("2.0.0", "1.99", 1),
    ],
)
def test_short_operand_compare(left, right, expected):
    assert Version.parse(left).compare(right) == expected
    assert Version.parse(left).compare(right.encode()) == expected


@pytest.mark.parametrize("op", [operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge])
@pytest.mark.parametrize("other", ["1.2", "1", "1.3", "0.9"])
def test_short_operand_operators_both_sides(op, other):
    full = Version.parse(other + ".0" * (3 - len(other.split("."))))
    v = Version.parse("1.2.0")
    assert op(v, other) == op(v, full)
    assert op(other, v) == op(full, v)


@pytest.mark.parametrize(
    "version,expr,expected",
    [
        ("1.2.3", ">=1.2", True), ("1.2.3", ">1.2", True), ("1.2.0", ">1.2", False),
        ("1.2.3", "<2", True), ("1.2.3", "<1.2", False), ("1.2.0", "<=1.2", True),
        ("1.2.0", "1.2", True), ("1.2.3", "1.2", False), ("1.2.3", "!=2", True),
        ("2.0.0", "==2", True), ("2.0.1", "<=2", False), ("1.2.0-rc.1", "<1.2", True),
    ],
)
def test_short_operand_match(version, expr, expected):
    assert Version.parse(version).match(expr) is expected


@pytest.mark.parametrize("operand", ["", "garbage", "1.", "1.2.3.4", "01.2.3", "1.2.x", "v1.2", "1..2"])
def test_invalid_operand_still_value_error_with_same_message(operand):
    with pytest.raises(ValueError) as exc:
        Version.parse("1.2.3").compare(operand)
    assert str(exc.value) == f"{operand} is not valid SemVer string"
    with pytest.raises(ValueError):
        Version.parse("1.2.3").match(">=" + operand)


def test_parse_and_is_valid_stay_strict():
    for s in ("1", "1.2", "1.2-rc.1"):
        with pytest.raises(ValueError):
            Version.parse(s)
        assert not Version.is_valid(s)
        assert Version.parse(s, optional_minor_and_patch=True)


def test_collection_operands_unchanged():
    v = Version.parse("1.2.0")
    assert v == (1, 2, 0)
    assert v == {"major": 1, "minor": 2, "patch": 0}
    assert (v == (1, 2)) is True  # Version(1, 2) is a full version


def test_subclass_without_override_gets_the_feature():
    class Sub(Version):
        pass

    assert Sub.parse("1.2.0").compare("1.2") == 0
    assert Sub.parse("1.2.3").match(">=1.2")


def test_one_parameter_parse_override_keeps_working():
    # The documented subclassing pattern (tests/test_subclass.py): parse(cls, version).
    class Tagged(Version):
        @classmethod
        def parse(cls, version):
            if not version[0] in ("v", "V"):
                raise ValueError("%r: must start with v" % version)
            return super().parse(version[1:])

    v = Tagged.parse("v1.2.3")
    assert v.compare("v1.2.4") == -1
    assert v.compare("V1.2.3") == 0
    assert v == "v1.2.3" and v < "v2.0.0" and v != "v1.2.4"
    assert v.match(">=v1.0.0") and not v.match("<v1.0.0")
    assert v.match("==v1.2.3")
    for operand in ("1.2.3", "1.2", "garbage"):
        with pytest.raises(ValueError):
            v.compare(operand)
        with pytest.raises(ValueError):
            v.match(">=" + operand)


def test_keyword_blind_override_never_gets_new_keywords():
    seen = []

    class Spy(Version):
        @classmethod
        def parse(cls, version):
            seen.append(version)
            return super().parse(version)

    v = Spy.parse("1.2.3")
    assert v.compare("1.2.3") == 0
    with pytest.raises(ValueError):
        v.compare("nope")
    assert seen[0] == "1.2.3" and seen[1] == "1.2.3" and seen[2] == "nope"


def test_shipped_v_prefix_subclass_still_compares():
    v = SemVerWithVPrefix.parse("v1.2.0")
    assert v.compare("v1.2") == 0
    assert v.compare("v1.3.0") == -1
    assert v == "v1.2.0"
    assert v.match(">=v1.0.0") and v.match("<v2")
    with pytest.raises(ValueError):
        v.compare("1.2.0")
