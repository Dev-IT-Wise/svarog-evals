# SPDX-License-Identifier: MIT
"""Hidden acceptance for large-semver-npm: the two new pysemver subcommands."""

import pytest

from semver import Version
from semver.cli import main


def run(capsys, *args):
    rc = main(list(args))
    captured = capsys.readouterr()
    return rc, captured.out, captured.err


@pytest.mark.parametrize(
    "version,expression",
    [
        ("1.2.3", "^1.0.0"),
        ("1.5.0", "1.x || >=2.5.0"),
        ("2.5.0", "1.x || >=2.5.0"),
        ("2.3.4", "1.2.3 - 2.3.4"),
        ("1.2.3", ">=1.0.0 <2.0.0-0"),
        ("1.2.3", "*"),
        ("1.2.3", ""),
        ("1.2.3-alpha.7", ">1.2.3-alpha.3"),
    ],
)
def test_satisfies_contained(capsys, version, expression):
    rc, out, err = run(capsys, "satisfies", version, expression)
    assert rc == 0
    assert out == version + "\n"
    assert err == ""


@pytest.mark.parametrize(
    "version,expression",
    [
        ("2.0.0", "^1.0.0"),
        ("2.4.0", "1.x || >=2.5.0"),
        ("2.3.5", "1.2.3 - 2.3.4"),
        ("1.5.0-beta.1", "^1.2.3"),
        ("1.2.3", ">*"),
    ],
)
def test_satisfies_not_contained(capsys, version, expression):
    rc, out, err = run(capsys, "satisfies", version, expression)
    assert rc == 1
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(
    "version,expression,expected_rc",
    [("1.5.0-beta.1", "^1.2.3", 0), ("2.0.0-rc.1", "^1.2.3", 1), ("1.9.0-alpha", "<2.0.0", 0)],
)
def test_satisfies_include_prerelease(capsys, version, expression, expected_rc):
    rc, out, err = run(capsys, "satisfies", "--include-prerelease", version, expression)
    assert rc == expected_rc
    assert out == (version + "\n" if expected_rc == 0 else "")
    assert err == ""
    # without the flag the same prerelease is not contained
    if expected_rc == 0:
        rc, out, _ = run(capsys, "satisfies", version, expression)
        assert rc == 1
        assert out == ""


@pytest.mark.parametrize(
    "expression,versions,expected",
    [
        ("^1.0.0", ["1.0.0", "1.4.2", "2.0.0", "1.10.0", "0.9.0"], "1.10.0"),
        ("^1.0.0", ["1.4.2"], "1.4.2"),
        ("1.x || >=2.5.0", ["1.9.0", "2.4.0", "3.1.0", "2.5.0"], "3.1.0"),
        ("<2.0.0", ["1.5.0", "1.5.0-rc.1", "3.0.0"], "1.5.0"),
        ("^1.0.0", ["1.11.0-rc.1", "1.2.0"], "1.2.0"),
    ],
)
def test_max_satisfying(capsys, expression, versions, expected):
    rc, out, err = run(capsys, "max-satisfying", expression, *versions)
    assert rc == 0
    assert out == expected + "\n"
    assert err == ""


@pytest.mark.parametrize(
    "expression,versions",
    [("^1.0.0", ["0.9.0", "2.0.0"]), ("^1.0.0", ["1.5.0-beta.1"]), (">*", ["1.0.0", "2.0.0"])],
)
def test_max_satisfying_none(capsys, expression, versions):
    rc, out, err = run(capsys, "max-satisfying", expression, *versions)
    assert rc == 1
    assert out == ""
    assert err == ""


def test_max_satisfying_include_prerelease(capsys):
    args = ["^1.0.0", "1.0.0", "1.11.0-rc.1", "1.2.0"]
    rc, out, err = run(capsys, "max-satisfying", "--include-prerelease", *args)
    assert rc == 0
    assert out == "1.11.0-rc.1\n"
    assert err == ""
    rc, out, _ = run(capsys, "max-satisfying", *args)
    assert rc == 0
    assert out == "1.2.0\n"
    rc, out, err = run(capsys, "max-satisfying", "--include-prerelease", "^1.0.0", "1.5.0-beta.1")
    assert rc == 0
    assert out == "1.5.0-beta.1\n"


@pytest.mark.parametrize(
    "expression,message",
    [
        ("=>1.0.0", "invalid comparator '=>1.0.0' in range '=>1.0.0'"),
        ("1.2-beta", "prerelease on a partial version in range '1.2-beta'"),
        ("1.2.3 -", "incomplete hyphen range in range '1.2.3 -'"),
    ],
)
def test_invalid_range(capsys, expression, message):
    rc, out, err = run(capsys, "satisfies", "1.2.3", expression)
    assert (rc, out, err) == (2, "", "ERROR " + message + "\n")
    rc, out, err = run(capsys, "max-satisfying", expression, "1.2.3")
    assert (rc, out, err) == (2, "", "ERROR " + message + "\n")


def test_invalid_version(capsys):
    with pytest.raises(ValueError) as expected:
        Version.parse("not-a-version")
    line = "ERROR " + str(expected.value) + "\n"
    rc, out, err = run(capsys, "satisfies", "not-a-version", "^1.0.0")
    assert (rc, out, err) == (2, "", line)
    rc, out, err = run(capsys, "max-satisfying", "^1.0.0", "1.2.0", "not-a-version", "1.3.0")
    assert (rc, out, err) == (2, "", line)
