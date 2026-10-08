# SPDX-License-Identifier: MIT
# T5 hidden acceptance test, r2-vacuous-decouple. AutoConfig looks for
# settings.ini or .env starting from the directory of the module that calls
# it, and then in its parents - whether that module calls the instance or
# its get() method.
import importlib.util
import uuid

import pytest

import decouple

SETTINGS = '''
from decouple import AutoConfig
VIA_CALL = AutoConfig()("T5_KEY", default="not found")
VIA_GET = AutoConfig().get("T5_KEY", default="not found")
'''

SINGLETON = '''
from decouple import config
VIA_SINGLETON = config("T5_KEY", default="not found")
'''


def load(path):
    spec = importlib.util.spec_from_file_location("t5_" + uuid.uuid4().hex, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def no_env(monkeypatch):
    monkeypatch.delenv("T5_KEY", raising=False)


def test_env_next_to_the_caller(tmp_path):
    (tmp_path / ".env").write_text("T5_KEY=from-env\n")
    (tmp_path / "settings.py").write_text(SETTINGS)
    mod = load(tmp_path / "settings.py")
    assert (mod.VIA_CALL, mod.VIA_GET) == ("from-env", "from-env")


def test_ini_next_to_the_caller(tmp_path):
    (tmp_path / "settings.ini").write_text("[settings]\nT5_KEY=from-ini\n")
    (tmp_path / "settings.py").write_text(SETTINGS)
    mod = load(tmp_path / "settings.py")
    assert (mod.VIA_CALL, mod.VIA_GET) == ("from-ini", "from-ini")


def test_env_in_a_parent_of_the_caller(tmp_path):
    (tmp_path / ".env").write_text("T5_KEY=from-parent\n")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "settings.py").write_text(SETTINGS)
    mod = load(tmp_path / "pkg" / "settings.py")
    assert (mod.VIA_CALL, mod.VIA_GET) == ("from-parent", "from-parent")


def test_the_module_level_config(tmp_path, monkeypatch):
    monkeypatch.setattr(decouple.config, "config", None)
    (tmp_path / ".env").write_text("T5_KEY=from-singleton\n")
    (tmp_path / "settings.py").write_text(SINGLETON)
    assert load(tmp_path / "settings.py").VIA_SINGLETON == "from-singleton"
