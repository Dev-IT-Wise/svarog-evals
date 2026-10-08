# SPDX-License-Identifier: MIT
"""Hidden acceptance for esc2-errors-decouple: docs/DESIGN-NOTES.md."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from decouple import AutoConfig, Config, UndefinedValueError

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def env():
    with patch.dict(os.environ):
        for k in [k for k in os.environ if k.startswith('ESC_')]:
            del os.environ[k]
        yield os.environ


def test_returns_cast_values_in_schema_order_and_exports_str(env):
    out = Config({'ESC_PORT': '8080', 'ESC_DEBUG': 'yes', 'ESC_RAW': 'r'}).export(
        {'ESC_PORT': {'cast': int}, 'ESC_DEBUG': {'cast': bool},
         'ESC_NAME': {'default': 'x'}, 'ESC_RAW': None})
    assert list(out) == ['ESC_PORT', 'ESC_DEBUG', 'ESC_NAME', 'ESC_RAW']
    assert out == {'ESC_PORT': 8080, 'ESC_DEBUG': True, 'ESC_NAME': 'x', 'ESC_RAW': 'r'}
    assert env['ESC_PORT'] == '8080'
    assert env['ESC_DEBUG'] == 'True'
    assert env['ESC_NAME'] == 'x'
    assert env['ESC_RAW'] == 'r'


def test_empty_schema(env):
    before = dict(os.environ)
    assert Config({}).export({}) == {}
    assert dict(os.environ) == before


def test_existing_environment_value_is_left_alone(env):
    env['ESC_FLAG'] = '1'
    assert Config({}).export({'ESC_FLAG': {'cast': bool}}) == {'ESC_FLAG': True}
    assert env['ESC_FLAG'] == '1'


def test_default_used_when_value_is_missing_everywhere(env):
    assert Config({}).export({'ESC_D': {'default': 5, 'cast': int}}) == {'ESC_D': 5}
    assert env['ESC_D'] == '5'


def test_missing_options_raise_one_undefined_value_error_naming_all_of_them(env):
    c = Config({'ESC_OK': '1'})
    before = dict(os.environ)
    with pytest.raises(UndefinedValueError) as ei:
        c.export({'ESC_OK': None, 'ESC_GONE_ONE': None, 'ESC_GONE_TWO': {'cast': int},
                  'ESC_DEF': {'default': 'd'}, 'ESC_GONE_THREE': None})
    msg = str(ei.value)
    for name in ('ESC_GONE_ONE', 'ESC_GONE_TWO', 'ESC_GONE_THREE'):
        assert name in msg
    assert 'ESC_OK' not in msg and 'ESC_DEF' not in msg
    assert dict(os.environ) == before
    assert 'ESC_OK' not in os.environ and 'ESC_DEF' not in os.environ


def test_single_missing_option(env):
    with pytest.raises(UndefinedValueError, match='ESC_ONLY'):
        Config({}).export({'ESC_ONLY': None})


def test_cast_exception_propagates_unchanged(env):
    with pytest.raises(ValueError, match='invalid literal'):
        Config({'ESC_N': 'abc'}).export({'ESC_N': {'cast': int}})

    def rt(v):
        raise RuntimeError('rt')

    with pytest.raises(RuntimeError, match='^rt$'):
        Config({'ESC_N': '1'}).export({'ESC_N': {'cast': rt}})


def test_existing_get_behaviour_unchanged(env):
    with pytest.raises(UndefinedValueError, match='ESC_NOPE not found'):
        Config({}).get('ESC_NOPE')
    assert Config({'ESC_X': '3'}).get('ESC_X', cast=int) == 3


def test_autoconfig_export(env, tmp_path):
    (tmp_path / '.env').write_text('ESC_PORT=9000\n')
    auto = AutoConfig(search_path=str(tmp_path))
    assert auto.export({'ESC_PORT': {'cast': int}, 'ESC_D': {'default': 'z'}}) == {
        'ESC_PORT': 9000, 'ESC_D': 'z'}
    assert env['ESC_PORT'] == '9000'
    before = dict(os.environ)
    with pytest.raises(UndefinedValueError) as ei:
        auto.export({'ESC_M1': None, 'ESC_M2': None})
    assert 'ESC_M1' in str(ei.value) and 'ESC_M2' in str(ei.value)
    assert dict(os.environ) == before


def test_autoconfig_export_finds_caller_dir(env, tmp_path):
    (tmp_path / '.env').write_text('ESC_Z=1\n')
    src = tmp_path / 'mod.py'
    src.write_text('from decouple import AutoConfig\nr = AutoConfig().export({"ESC_Z": {"cast": int}})\n')
    ns = {}
    exec(compile(src.read_text(), str(src), 'exec'), ns)
    assert ns['r'] == {'ESC_Z': 1}


def test_docstrings_and_no_new_public_names():
    assert (Config.export.__doc__ or '').strip()
    assert (AutoConfig.export.__doc__ or '').strip()
    public = {n for n in dir(Config) if not n.startswith('_')}
    assert public == {'get', 'export'}


def test_changelog_and_files():
    text = (ROOT / 'CHANGELOG.md').read_text()
    lines = text.splitlines()
    assert lines[0] == '# Changelog'
    assert '## Unreleased' in lines
    assert '- Add Config.export and AutoConfig.export.' in lines
    assert not [p for p in ROOT.glob('*.py') if p.name not in ('decouple.py', 'conftest.py')]
