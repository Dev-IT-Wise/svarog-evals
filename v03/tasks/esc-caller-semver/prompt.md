Version comparison only takes full versions: `Version.parse("1.2.3").match(">=1.2")`
fails with `1.2 is not valid SemVer string`. I'd like comparisons and `match`
to accept short versions like `1.2` or `2` on the other side, with the missing
parts taken as zero. Please add that, with tests.
