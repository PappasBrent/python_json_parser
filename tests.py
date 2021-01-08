import unittest

from lexer import (Boolean, Literal, Number, ObjectKey, Tag, Token, TokenError,
                   lex)
from parser_ import parse


class LexerTest(unittest.TestCase):

    def test_lex_ints(self):
        s = "123 456 1"
        self.assertEqual(lex(s), [Number(123), Number(456), Number(1)])

    def test_lex_floats(self):
        s = "1.23 45.6 1.0"
        self.assertEqual(lex(s), [Number(1.23), Number(45.6), Number(1.0)])

    def test_lex_sci(self):
        s = "1e2 2.1e3 3e-4 1E+2 2.1E+3 3E-4"
        self.assertEqual(lex(s), [Number(100), Number(2100.0), Number(
            0.0003), Number(100), Number(2100.0), Number(0.0003)])

    def test_lex_negatives(self):
        s = "-123 -45.6 -3e-4"
        # this may just be a quirk of the way this works, but
        # the input s = "-123-45.6-3e-4" works too. hmm...
        # ah should be fine since this is just lexing
        # In fact, I think this is actually how this should work
        self.assertEqual(
            lex(s), [Number(-123), Number(-45.6), Number(-0.0003)])

    def test_fail_end_e(self):
        tests = ["-3e", "1e", "e", "1.0e", "-3E", "1E", "E", "1.0E"]
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_fail_end_minus(self):
        tests = ["-3e-", "-", "1-", "1.0-"]
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_lex_null(self):
        tests = [
            ("null", [Token(Tag.NULL)]),
            ("null null", [Token(Tag.NULL), Token(Tag.NULL)])
        ]
        for test, expected in tests:
            self.assertEqual(lex(test), expected)

    def test_lex_null_fail(self):
        tests = ["n", "nu", "nul", "nule", "llun"]
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_lex_bools(self):
        tests = [
            ("false", [Boolean(False)]),
            ("true", [Boolean(True)]),
            ("true false", [Boolean(True), Boolean(False)]),
        ]
        for test, expected in tests:
            self.assertEqual(lex(test), expected)

    def test_fail_lex_bool(self):
        tests = ["tru", "fal", "truee", "falsee"]
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_lex_comma(self):
        tests = [
            (",", [Token(Tag.COMMA)]),
            (", ,", [Token(Tag.COMMA), Token(Tag.COMMA)])
        ]
        for test, expected in tests:
            self.assertEqual(lex(test), expected)

    def test_lex_brackets(self):
        def l(): return Token(Tag.LEFT_BRACKET)
        def r(): return Token(Tag.RIGHT_BRACKET)
        s = "[][][[]]"
        self.assertEqual(lex(s), [l(), r(), l(), r(), l(), l(), r(), r()])

    def test_lex_braces(self):
        def l(): return Token(Tag.LEFT_BRACE)
        def r(): return Token(Tag.RIGHT_BRACE)
        s = "{}{}{{}}"
        self.assertEqual(lex(s), [l(), r(), l(), r(), l(), l(), r(), r()])

    def test_lex_literal(self):
        s = '''
        "a"
        "abc"
        "ab\\b"
        "\\t\\f\\n"
        "\\u1234"
        "ab\\b\\u0F9atest"
        '''
        return self.assertEqual(lex(s), [
            Literal("a"),
            Literal("abc"),
            Literal("ab\\b"),
            Literal("\\t\\f\\n"),
            Literal("\\u1234"),
            Literal("ab\\b\\u0F9atest")
        ])

    def test_fail_lex_literal(self):
        tests = ["\\", "\"", "\\u1", "\\x", "\\uGGGG"
                 '''
                    "this should not
                    work"
        ''']
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_lex_object_key(self):
        s = '''
        "a":
        "abc":
        "ab\\b"
        
        :
        
        "\\t\\f\\n"  :  
        "\\u1234"   :
        "ab\\b\\u0F9atest":
        '''
        return self.assertEqual(lex(s), [
            ObjectKey("a"),
            ObjectKey("abc"),
            ObjectKey("ab\\b"),
            ObjectKey("\\t\\f\\n"),
            ObjectKey("\\u1234"),
            ObjectKey("ab\\b\\u0F9atest")
        ])

    def test_fail_lex_object_key(self):
        tests = ["\\", "\"", "\\u1", "\\x", "\\uGGGG"
                 '''
                    "this should not
                    work":
        ''']
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_mixed(self):
        s = '''
        {
            "name": "Brent Pappas",
            "age": 22,
            "interests": ["juggling", "programming", "reading"]
        }

        '''
        self.assertEqual(lex(s),
                         [
            Token(Tag.LEFT_BRACE),
            ObjectKey("name"),
            Literal("Brent Pappas"),
            Token(Tag.COMMA),
            ObjectKey("age"),
            Number(22),
            Token(Tag.COMMA),
            ObjectKey("interests"),
            Token(Tag.LEFT_BRACKET),
            Literal("juggling"),
            Token(Tag.COMMA),
            Literal("programming"),
            Token(Tag.COMMA),
            Literal("reading"),
            Token(Tag.RIGHT_BRACKET),
            Token(Tag.RIGHT_BRACE)
        ])


class ParserTest(unittest.TestCase):

    def test_parse_none(self):
        self.assertEqual(parse(lex('')), None)

    def test_parse_array(self):
        for test, expected in [
            ('[]', []),
            ('["simple test"]', ["simple test"]),
            ('[null, null, null]', [None, None, None]),
            ('[[],[]]', [[], []]),
            ('[[null,[]],[]]', [[None, []], []]),
            ('''[
                    [
                        null,
                        []
                    ],
                    []
                ]''', [[None, []], []]),
            ('''
            [
                null,
                ["test",123,null],
                [],
                [[]]
            ]
            ''', [None, ["test", 123, None], [], [[]]]),
            ('''
            [
                null,
                [
                    "test"
                ]
            ]
            ''',
             [None, ["test"]]),
            ('''
            [
                null,
                [
                    "test",
                    {"key":"value"}
                ]
            ]
            ''',
             [None, ["test", {"key": "value"}]])
        ]:
            self.assertEqual(parse(lex(test)), expected)

    def test_parse_object(self):
        for test, expected in [
            ('{}', {}),
            ('{"name": "brent"}', {"name": "brent"}),
            ('{"name": "brent","age":22}', {"name": "brent", "age": 22}),
            ('{"name": "brent","age":22,"interests":["juggling","programming","reading"]}', {
             "name": "brent", "age": 22, "interests": ["juggling", "programming", "reading"]}),
            ('''{
                "name": "brent",
                "age":22,
                "interests":[
                    "juggling","programming","reading"
                    ],
                "key1":{"key2":"value"}}
            ''', {"name": "brent", "age": 22, "interests": ["juggling", "programming", "reading"], "key1": {"key2": "value"}}),
            ('''
            {
            "test"

            : {}
            }''', {"test": {}}),
            (
                '''
    {
        "first name":"Arthur",
        "last name": "Dent",
        "age":42,
        "interests": [
            "flying",
            "sandwich making"
        ]
    }
    ''', {
                    "first name": "Arthur",
                    "last name": "Dent",
                    "age": 42,
                    "interests": ["flying", "sandwich making"]
                }
            )
        ]:
            self.assertEqual(parse(lex(test)), expected)


if __name__ == '__main__':
    unittest.main()
