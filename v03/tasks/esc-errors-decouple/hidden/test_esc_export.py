# SPDX-License-Identifier: MIT
"""Hidden acceptance for esc-errors-decouple: the error contract of
docs/DESIGN-NOTES.md."""
import os
from unittest.mock import patch

import pytest
from decouple import AutoConfig, Config, UndefinedValueError


def cfg(**repo):
    return Config(repo)


def boom(value):
    raise ValueError('boom')


def type_boom(value):
    raise TypeError('tboom')


@pytest.fixture
def env():
    with patch.dict(os.environ, {}, clear=False):
        for k in [k for k in os.environ if k.startswith('ESC_')]:
            del os.environ[k]
        yield os.environ


def snapshot():
    return dict(os.environ)


def test_success_returns_cast_values_in_order_and_exports(env):
    c = cfg(ESC_PORT='8080', ESC_DEBUG='yes')
    schema = {'ESC_PORT': {'cast': int}, 'ESC_DEBUG': {'cast': bool},
              'ESC_NAME': {'default': 'x'}}
    out = c.export(schema)
    assert list(out) == ['ESC_PORT', 'ESC_DEBUG', 'ESC_NAME']
    assert out == {'ESC_PORT': 8080, 'ESC_DEBUG': True, 'ESC_NAME': 'x'}
    assert env['ESC_PORT'] == '8080'
    assert env['ESC_DEBUG'] == 'True'
    assert env['ESC_NAME'] == 'x'


def test_none_entry_and_empty_schema(env):
    before = snapshot()
    assert cfg().export({}) == {}
    assert snapshot() == before
    assert cfg(ESC_A='1').export({'ESC_A': None}) == {'ESC_A': '1'}


def test_existing_environment_value_is_not_rewritten(env):
    env['ESC_FLAG'] = '1'
    out = cfg().export({'ESC_FLAG': {'cast': bool}})
    assert out == {'ESC_FLAG': True}
    assert env['ESC_FLAG'] == '1'


def test_missing_raises_undefined_value_error_naming_every_missing_option(env):
    c = cfg(ESC_OK='1')
    before = snapshot()
    with pytest.raises(UndefinedValueError) as ei:
        c.export({'ESC_OK': None, 'ESC_MISS_ONE': None, 'ESC_MISS_TWO': {'cast': int},
                  'ESC_DEF': {'default': 'd'}})
    msg = str(ei.value)
    assert 'ESC_MISS_ONE' in msg and 'ESC_MISS_TWO' in msg
    assert 'ESC_OK' not in msg and 'ESC_DEF' not in msg
    assert not isinstance(ei.value, (ValueError, KeyError))
    assert snapshot() == before


def test_single_missing_option_is_still_undefined_value_error(env):
    with pytest.raises(UndefinedValueError, match='ESC_ONLY'):
        cfg().export({'ESC_ONLY': None})


@pytest.mark.parametrize('bad', [boom, type_boom])
def test_cast_failure_is_value_error_naming_the_option(env, bad):
    c = cfg(ESC_FIRST='1', ESC_BAD='x')
    before = snapshot()
    with pytest.raises(ValueError) as ei:
        c.export({'ESC_FIRST': {'cast': int}, 'ESC_BAD': {'cast': bad}})
    assert str(ei.value) == 'ESC_BAD: ' + ('boom' if bad is boom else 'tboom')
    assert 'ESC_FIRST' not in os.environ
    assert snapshot() == before


def test_bool_and_int_cast_failures_name_the_option(env):
    with pytest.raises(ValueError) as ei:
        cfg(ESC_N='abc').export({'ESC_N': {'cast': int}})
    assert str(ei.value).startswith('ESC_N: ')
    assert "abc" in str(ei.value)
    with pytest.raises(ValueError) as ei:
        cfg(ESC_B='maybe').export({'ESC_B': {'cast': bool}})
    assert str(ei.value).startswith('ESC_B: ')


def test_first_failing_cast_in_schema_order_is_reported(env):
    c = cfg(ESC_A='x', ESC_B='y')

    def second(v):
        raise ValueError('second')

    with pytest.raises(ValueError) as ei:
        c.export({'ESC_A': {'cast': boom}, 'ESC_B': {'cast': second}})
    assert str(ei.value) == 'ESC_A: boom'


def test_missing_is_reported_before_a_bad_cast(env):
    c = cfg(ESC_BAD='x')
    with pytest.raises(UndefinedValueError, match='ESC_GONE'):
        c.export({'ESC_BAD': {'cast': boom}, 'ESC_GONE': None})


def test_other_cast_exceptions_propagate_unchanged(env):
    def rt(v):
        raise RuntimeError('rt')

    before = snapshot()
    with pytest.raises(RuntimeError, match='rt'):
        cfg(ESC_A='1', ESC_B='2').export({'ESC_A': None, 'ESC_B': {'cast': rt}})
    assert snapshot() == before


def test_environment_refusing_a_value_rolls_everything_back(env):
    env['ESC_KEEP'] = 'orig'
    c = cfg(ESC_A='1', ESC_B='2', ESC_NUL='a\0b', ESC_LATE='3')
    before = snapshot()
    with pytest.raises(ValueError) as ei:
        c.export({'ESC_A': None, 'ESC_B': None, 'ESC_NUL': None, 'ESC_LATE': None})
    assert str(ei.value).startswith('ESC_NUL: ')
    assert snapshot() == before
    assert 'ESC_A' not in os.environ and 'ESC_B' not in os.environ


def test_failure_returns_nothing_and_a_retry_after_fixing_works(env):
    repo = {'ESC_A': '1'}
    c = Config(repo)
    with pytest.raises(UndefinedValueError):
        c.export({'ESC_A': None, 'ESC_B': None})
    assert 'ESC_A' not in os.environ
    repo['ESC_B'] = '2'
    assert c.export({'ESC_A': None, 'ESC_B': None}) == {'ESC_A': '1', 'ESC_B': '2'}
    assert env['ESC_A'] == '1' and env['ESC_B'] == '2'


def test_existing_get_behaviour_unchanged(env):
    with pytest.raises(UndefinedValueError, match='ESC_NOPE not found'):
        cfg().get('ESC_NOPE')
    assert cfg(ESC_X='3').get('ESC_X', cast=int) == 3


def test_autoconfig_export_uses_the_search_path_and_same_errors(env, tmp_path):
    (tmp_path / '.env').write_text('ESC_PORT=9000\n')
    auto = AutoConfig(search_path=str(tmp_path))
    out = auto.export({'ESC_PORT': {'cast': int}, 'ESC_D': {'default': 'z'}})
    assert out == {'ESC_PORT': 9000, 'ESC_D': 'z'}
    assert env['ESC_PORT'] == '9000'
    before = snapshot()
    with pytest.raises(UndefinedValueError, match='ESC_M1.*ESC_M2|ESC_M2.*ESC_M1'):
        auto.export({'ESC_M1': None, 'ESC_M2': None})
    assert snapshot() == before


def test_autoconfig_export_without_search_path_finds_caller_dir(env, tmp_path):
    (tmp_path / '.env').write_text('ESC_Z=1\n')
    src = tmp_path / 'mod.py'
    src.write_text('from decouple import AutoConfig\nr = AutoConfig().export({"ESC_Z": {"cast": int}})\n')
    ns = {}
    exec(compile(src.read_text(), str(src), 'exec'), ns)
    assert ns['r'] == {'ESC_Z': 1}
