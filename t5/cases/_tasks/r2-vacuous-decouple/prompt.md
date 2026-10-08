Bug report: since the last upgrade, `config('SECRET_KEY')` in my Django
`settings.py` (`from decouple import config`) raises
`UndefinedValueError: SECRET_KEY not found. Declare it as envvar or define a
default value.` The `.env` file is right next to `settings.py`, and
`AutoConfig(search_path=BASE_DIR)` works around it. Fix it, with a
regression test.

Tests: `.venv/bin/python -m pytest -q`
