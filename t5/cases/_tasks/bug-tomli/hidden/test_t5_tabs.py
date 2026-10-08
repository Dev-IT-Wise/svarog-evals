# SPDX-License-Identifier: MIT
# T5 hidden acceptance test, bug-tomli. TOML whitespace is space or tab
# (toml.io/en/v1.0.0, "Spec"), wherever the grammar allows whitespace.
import unittest

import tomli


class TestTabIsWhitespace(unittest.TestCase):
    def check(self, doc, expected):
        self.assertEqual(tomli.loads(doc), expected, repr(doc))

    def test_reported_symptom(self):
        self.check("a\t= 1", {"a": 1})

    def test_after_equals(self):
        self.check("a =\t1", {"a": 1})

    def test_line_indent(self):
        self.check("\ta = 1", {"a": 1})

    def test_before_comment(self):
        self.check("a = 1\t# c", {"a": 1})

    def test_dotted_key(self):
        self.check("a\t.\tb = 1", {"a": {"b": 1}})

    def test_table_header(self):
        self.check("[\tt\t]\nx = 1", {"t": {"x": 1}})

    def test_array_of_tables_header(self):
        self.check("[[\tt\t]]\nx = 1", {"t": [{"x": 1}]})

    def test_inline_table(self):
        self.check("t = {\ta\t=\t1\t,\tb = 2\t}", {"t": {"a": 1, "b": 2}})

    def test_array(self):
        self.check("a = [\t1\t,\t2\t]", {"a": [1, 2]})

    def test_multiline_string_line_ending_backslash(self):
        self.check('s = """a \\\t\n\tb"""', {"s": "a b"})

    def test_tab_only_document(self):
        self.check("\t", {})

    def test_tab_still_invalid_inside_a_bare_key(self):
        with self.assertRaises(tomli.TOMLDecodeError):
            tomli.loads("a\tb = 1")
