Comparing against a short version fails: `Version.parse("1.2.3").match(">=1.2")`
raises `1.2 is not valid SemVer string`. Please make comparisons and `match`
accept short versions like `1.2` or `2`, missing parts as zero, with tests.
