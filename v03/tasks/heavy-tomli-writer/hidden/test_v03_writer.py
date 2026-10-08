# SPDX-License-Identifier: MIT
"""Hidden acceptance for heavy-tomli-writer: behaviour and the API facts that
docs/DESIGN-NOTES.md plants. Runs beside upstream's own tests."""

import datetime
import decimal
import importlib
import inspect
import io
import math
import unittest

import tomli

UTC = datetime.timezone.utc


class TestApi(unittest.TestCase):
    def test_exports(self):
        self.assertEqual(
            tomli.__all__, ("loads", "load", "TOMLDecodeError", "dumps", "dump", "TOMLEncodeError")
        )
        self.assertTrue(issubclass(tomli.TOMLEncodeError, ValueError))
        writer = importlib.import_module("tomli._writer")
        self.assertIs(writer.dumps, tomli.dumps)
        self.assertIs(writer.dump, tomli.dump)
        self.assertIs(writer.TOMLEncodeError, tomli.TOMLEncodeError)

    def test_signatures(self):
        for fn, positional in ((tomli.dumps, ["obj"]), (tomli.dump, ["obj", "fp"])):
            params = inspect.signature(fn).parameters
            pos = [n for n, p in params.items() if p.kind is p.POSITIONAL_ONLY]
            kw = {n: p.default for n, p in params.items() if p.kind is p.KEYWORD_ONLY}
            self.assertEqual(pos, positional, fn.__name__)
            self.assertEqual(kw, {"multiline_strings": False}, fn.__name__)


class TestFormat(unittest.TestCase):
    def test_design_notes_example(self):
        doc = {
            "title": "TOML",
            "owner": {"name": "Tom", "dob": datetime.date(1979, 5, 27)},
            "servers": [{"ip": "10.0.0.1"}, {"ip": "10.0.0.2", "tags": ["a", "b"]}],
            "points": [{"x": 1}, 2],
        }
        self.assertEqual(
            tomli.dumps(doc),
            'title = "TOML"\npoints = [{ x = 1 }, 2]\n\n[owner]\nname = "Tom"\ndob = 1979-05-27\n\n'
            '[[servers]]\nip = "10.0.0.1"\n\n[[servers]]\nip = "10.0.0.2"\ntags = ["a", "b"]\n',
        )

    def test_golden(self):
        doc = {
            "z": 1,
            "a key": "tab\there \"q\" back\\slash \x01\x7f é",
            "": True,
            "f": [1.5, -0.0, float("inf"), float("-inf"), 1e16],
            "dt": datetime.datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC),
            "ldt": datetime.datetime(2020, 1, 2, 3, 4, 5, 600000),
            "t": datetime.time(7, 8, 9),
            "empty": [],
            "nested": [[1, 2], ["x"], {}],
            "inline": [{"a": {"b": 1}, "c": [{"d": 2}]}, 3],
            "tbl": {"x": False, "deep": {"y": 2}},
            "only_sub": {"s": {"k": "v"}},
            "void": {},
            "aot": [{"n": 1, "sub": {"m": 2}}, {"n": 3}],
            "tup": (1, 2),
        }
        expected = (
            'z = 1\n'
            '"a key" = "tab\\there \\"q\\" back\\\\slash \\u0001\\u007F é"\n'
            '"" = true\n'
            'f = [1.5, -0.0, inf, -inf, 1e+16]\n'
            'dt = 2020-01-02T03:04:05+00:00\n'
            'ldt = 2020-01-02T03:04:05.600000\n'
            't = 07:08:09\n'
            'empty = []\n'
            'nested = [[1, 2], ["x"], {}]\n'
            'inline = [{ a = { b = 1 }, c = [{ d = 2 }] }, 3]\n'
            'tup = [1, 2]\n'
            '\n[tbl]\nx = false\n'
            '\n[tbl.deep]\ny = 2\n'
            '\n[only_sub.s]\nk = "v"\n'
            '\n[void]\n'
            '\n[[aot]]\nn = 1\n'
            '\n[aot.sub]\nm = 2\n'
            '\n[[aot]]\nn = 3\n'
        )
        self.assertEqual(tomli.dumps(doc), expected)

    def test_insertion_order_not_sorted(self):
        self.assertEqual(tomli.dumps({"b": 1, "a": 2}), "b = 1\na = 2\n")

    def test_empty(self):
        self.assertEqual(tomli.dumps({}), "")

    def test_only_tables(self):
        self.assertEqual(tomli.dumps({"a": {"b": {"c": 1}}}), "[a.b]\nc = 1\n")
        self.assertEqual(tomli.dumps({"a": {}}), "[a]\n")

    def test_quoted_header_keys(self):
        self.assertEqual(tomli.dumps({"a.b": {"c d": {"e": 1}}}), '["a.b"."c d"]\ne = 1\n')

    def test_multiline(self):
        doc = {"s": 'one\ntwo "q"\tx', "arr": ["a\nb"], "k": {"in": "p\nq"}}
        self.assertEqual(
            tomli.dumps(doc, multiline_strings=True),
            's = """\none\ntwo \\"q\\"\\tx"""\narr = ["a\\nb"]\n\n[k]\nin = """\np\nq"""\n',
        )
        self.assertEqual(tomli.dumps({"s": "a\nb"}), 's = "a\\nb"\n')
        self.assertEqual(tomli.loads(tomli.dumps(doc, multiline_strings=True)), doc)


class TestRoundTrip(unittest.TestCase):
    DOCS = [
        {},
        {"a": 1, "b": -2, "c": 0},
        {"s": "\x00\x1f\x7f\u2603\\\"'\n\r\t\b\f", "multi": "l1\nl2\r\nl3"},
        {"t": {"u": {"v": {"w": [1, [2, [3]]]}}}},
        {"aot": [{"x": [{"y": 1}], "z": {}}, {"q": {"r": [{"s": 2}]}}]},
        {"mix": [1, "a", 2.5, True, datetime.date(2000, 1, 1), {"k": 0}]},
        {"weird keys": {"": {"é": {"a.b": 1}}}},
        {"dt": datetime.datetime(1999, 12, 31, 23, 59, 59, 999999, tzinfo=datetime.timezone(datetime.timedelta(hours=-5, minutes=-30)))},
        {"time": datetime.time(0, 0, 0, 1)},
    ]

    def test_round_trip(self):
        for doc in self.DOCS:
            for ml in (False, True):
                with self.subTest(doc=doc, ml=ml):
                    self.assertEqual(tomli.loads(tomli.dumps(doc, multiline_strings=ml)), doc)

    def test_nan(self):
        self.assertTrue(math.isnan(tomli.loads(tomli.dumps({"n": float("nan")}))["n"]))
        self.assertEqual(tomli.dumps({"n": float("nan")}), "n = nan\n")

    def test_dump_binary_utf8(self):
        f = io.BytesIO()
        self.assertIsNone(tomli.dump({"k": "é", "t": {"x": 1}}, f, multiline_strings=True))
        self.assertEqual(f.getvalue(), tomli.dumps({"k": "é", "t": {"x": 1}}).encode("utf-8"))


class TestErrors(unittest.TestCase):
    def check(self, obj, message):
        with self.assertRaises(tomli.TOMLEncodeError) as cm:
            tomli.dumps(obj)
        self.assertEqual(str(cm.exception), message)
        self.assertIsInstance(cm.exception, ValueError)

    def test_messages(self):
        self.check({"a": {1, 2}}, "Object of type set is not TOML serializable")
        self.check({"a": None}, "Object of type NoneType is not TOML serializable")
        self.check({"a": [1, None]}, "Object of type NoneType is not TOML serializable")
        self.check({"a": b"x"}, "Object of type bytes is not TOML serializable")
        self.check({"a": decimal.Decimal("1.5")}, "Object of type Decimal is not TOML serializable")
        self.check({"t": {2: "x"}}, "TOML keys must be strings, not int")
        self.check({"t": [{"k": 1}, {None: 1}]}, "TOML keys must be strings, not NoneType")
        self.check([1, 2], "The top-level object must be a mapping, not list")
        self.check("x", "The top-level object must be a mapping, not str")
        self.check({"t": datetime.time(1, 2, tzinfo=UTC)}, "TOML times cannot have a UTC offset")

    def test_dump_writes_nothing_on_error(self):
        f = io.BytesIO()
        with self.assertRaises(tomli.TOMLEncodeError):
            tomli.dump({"ok": 1, "bad": None}, f)
        self.assertEqual(f.getvalue(), b"")
