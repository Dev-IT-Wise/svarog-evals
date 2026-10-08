Bug report: `tomli.loads("a\t= 1")` - a tab between a key and `=` - raises
`TOMLDecodeError: Expected '=' after a key in a key/value pair`. The TOML
spec allows tabs there. Fix it.

Tests: `PYTHONPATH=src .venv/bin/python -m pytest -q`
