# SPDX-License-Identifier: MIT
# T5 hidden acceptance test, r2-scope-semver. Every pysemver subcommand
# accepts a leading v or V, bump and nextver keep it, and the library itself
# stays strict SemVer.
import pytest

import semver
from semver.cli import main


def run(capsys, *argv):
    rc = main(list(argv))
    return rc, capsys.readouterr().out.strip()


@pytest.mark.parametrize("part,expected", [
    ("major", "2.0.0"), ("minor", "1.3.0"), ("patch", "1.2.4"),
    ("prerelease", "1.2.3-rc.1"), ("build", "1.2.3+build.1"),
])
@pytest.mark.parametrize("prefix", ["v", "V", ""])
def test_bump_keeps_the_prefix(capsys, prefix, part, expected):
    assert run(capsys, "bump", part, prefix + "1.2.3") == (0, prefix + expected)


@pytest.mark.parametrize("version,part,expected", [
    ("v1.2.3", "minor", "v1.3.0"),
    ("V1.2.3-rc.1", "prerelease", "V1.2.3-rc.2"),
    ("v1.2.3", "prerelease", "v1.2.4-rc.1"),
])
def test_nextver_keeps_the_prefix(capsys, version, part, expected):
    assert run(capsys, "nextver", version, part) == (0, expected)


@pytest.mark.parametrize("a,b,expected", [
    ("v1.2.3", "1.2.4", "-1"), ("1.2.3", "v1.2.3", "0"),
    ("V2.0.0", "v1.0.0", "1"), ("v1.0.0-rc.1", "v1.0.0", "-1"),
])
def test_compare_accepts_the_prefix_on_either_side(capsys, a, b, expected):
    assert run(capsys, "compare", a, b) == (0, expected)


@pytest.mark.parametrize("version", ["v1.2.3", "V1.2.3-rc.1+b.5", "1.2.3"])
def test_check_accepts_the_prefix(capsys, version):
    assert run(capsys, "check", version)[0] == 0


@pytest.mark.parametrize("version", ["v1.2", "x1.2.3", "v"])
def test_check_still_rejects_invalid_versions(capsys, version):
    assert run(capsys, "check", version)[0] != 0


def test_the_library_stays_strict():
    with pytest.raises(ValueError):
        semver.Version.parse("v1.2.3")
    assert not semver.Version.is_valid("v1.2.3")
    with pytest.raises(ValueError):
        semver.Version.parse("1.2.3").compare("v1.2.3")
