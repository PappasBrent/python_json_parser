"""
Title: JSON Lexer
Author: Brent Pappas
Date: 1-5-2021
"""

# resources
# https://www.json.org/json-en.html (visual, very nice)
# https://cswr.github.io/JsonSchema/spec/grammar/
# https://notes.eatonphil.com/writing-a-simple-json-parser.html (if you get stuck)

import unicodedata
import unittest
from enum import Enum


class TokenError(Exception):
    """ Class for token errors """

    def __init__(self, character, line_number, message="Token error") -> None:
        self.character = character
        self.line_number = line_number
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}: Unexpected token '{self.character}' at line {self.line_number}"


class Tag(Enum):
    """
    Enum for token tags
    """
    NUMBER = 1
    LITERAL = 2
    NULL = 3
    COMMA = 4
    OBJECT_KEY = 5
    LEFT_BRACE = 6
    RIGHT_BRACE = 7
    LEFT_BRACKET = 8
    RIGHT_BRACKET = 9
    BOOLEAN = 10


class Token(object):
    def __init__(self, tag) -> None:
        self.tag = tag

    def __repr__(self) -> str:
        return f"({self.tag})"

    def __eq__(self, o: 'Token') -> bool:
        return self.tag == o.tag


class Number(Token):
    def __init__(self, value) -> None:
        super().__init__(Tag.NUMBER)
        self.value = value

    def __repr__(self) -> str:
        return f"({self.tag}, {self.value})"

    def __eq__(self, o: 'Number') -> bool:
        return self.tag == o.tag and self.value == o.value


class Literal(Token):
    def __init__(self, lexeme) -> None:
        super().__init__(Tag.LITERAL)
        self.lexeme = lexeme

    def __repr__(self) -> str:
        return f"({self.tag}, {self.lexeme})"

    def __eq__(self, o: 'Literal') -> bool:
        return self.tag == o.tag and self.lexeme == o.lexeme


class ObjectKey(Literal):
    def __init__(self, lexeme) -> None:
        super().__init__(lexeme)
        self.tag = Tag.OBJECT_KEY


class Boolean(Token):
    def __init__(self, value) -> None:
        super().__init__(Tag.BOOLEAN)
        self.value = value

    def __repr__(self) -> str:
        return f"({self.tag}, {self.value})"

    def __eq__(self, o: 'Boolean') -> bool:
        return self.tag == o.tag and self.value == o.value


def lex(text: str):
    n = len(text)
    line_number = 1
    token_list = []
    i = 0
    round_off_digit = 15

    def is_unicode(c):
        # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
        return unicodedata.category(c)[0] == "C"

    while i < n:

        # skip whitespace
        if text[i].isspace():
            if text[i] == "\n":
                line_number += 1
            i += 1
            continue

        v_is_negative = False
        # check if number is negative first
        if text[i] == "-":
            v_is_negative = True
            i += 1
            if i >= n:
                raise TokenError(text[i-1], line_number)

        # check for number
        if text[i].isnumeric():
            v = 0

            # integer
            while i < n and text[i].isnumeric():
                v *= 10
                v += int(text[i])
                i += 1

            if i >= n or text[i].lower() not in [".", "e"]:
                token_list.append(Number(v * (-1 if v_is_negative else 1)))
                continue

            # float
            if text[i] == ".":
                i += 1
                mantissa = 0
                e = -1
                while i < n and text[i].isnumeric():
                    mantissa += int(text[i]) * 10**e
                    e -= 1
                    i += 1
                v += mantissa
            if i >= n or text[i].lower() != "e":
                token_list.append(Number(v * (-1 if v_is_negative else 1)))
                continue

            # scientific notation
            # {invariant: text[i].lower() == "e"}
            i += 1
            if i >= n:
                raise TokenError(text[i-1], line_number)

            # check if exponent is negative
            e_is_negative = False
            if text[i] == '-':
                e_is_negative = True
                i += 1
            elif text[i] == "+":
                i += 1
            else:
                if not text[i].isnumeric():
                    raise TokenError(text[i], line_number)
            if i >= n:
                raise TokenError(text[i-1], line_number)

            e = 0
            # e will always be an integer
            while i < n and text[i].isnumeric():
                e *= 10
                e += int(text[i])
                i += 1
            if e_is_negative:
                e *= -1

            v *= 10**e

            if e != 0:
                v = round(v, round_off_digit)

            token_list.append(Number(v * (-1 if v_is_negative else 1)))
            i += 1
            continue

        # check for true
        if text[i] == "t":
            if i + 3 >= n:
                raise TokenError(text[i], line_number)
            if text[i:i+4] == "true":
                token_list.append(Boolean(True))
                i += 4
                continue

        # check for false
        if text[i] == "f":
            if i + 4 >= n:
                raise TokenError(text[i], line_number)
            elif text[i:i+5] == "false":
                token_list.append(Boolean(False))
                i += 5
                continue

        # check for comma
        if text[i] == ",":
            token_list.append(Token(Tag.COMMA))
            i += 1
            continue

        # check for brackets
        if text[i] in ["[", "]"]:
            token_list.append(
                Token(Tag.LEFT_BRACKET if text[i] == "[" else Tag.RIGHT_BRACKET))
            i += 1
            continue

        # check for braces
        if text[i] in ["{", "}"]:
            token_list.append(
                Token(Tag.LEFT_BRACE if text[i] == "{" else Tag.RIGHT_BRACE))
            i += 1
            continue

        # check for string literal / object key
        if text[i] == '"':
            buffer = ""
            while True:
                i += 1

                if i >= n:
                    raise TokenError(text[i-1], line_number)

                if text[i] == '"':
                    # check whether object key or literal
                    if i + 1 < n and text[i+1] == ":":
                        token_list.append(ObjectKey(buffer))
                        i += 2  # we add 2 here and not just 1 since we break out of the inner loop
                    else:
                        token_list.append(Literal(buffer))
                        i += 1
                    break

                if text[i] == "\\":
                    if i + 1 >= n:
                        raise TokenError(text[i], line_number)
                    if text[i + 1] not in ['"', "\\", "/", "b", "f", "n", "r", "t", "u"]:
                        raise TokenError(text[i + 1], line_number)
                    if text[i + 1] != "u":
                        buffer += text[i:i + 2]
                        i += 1
                        continue
                    # handle \u followed by 4 hex digits
                    if i + 5 >= n:
                        raise TokenError(text[i], line_number)
                    buffer += text[i]
                    buffer += "u"
                    i += 1
                    for _ in range(4):
                        i += 1
                        if not (text[i].isnumeric() or text[i] in 'abcdefABCDEF'):
                            raise TokenError(text[i], line_number)
                        buffer += text[i]
                    continue

                if is_unicode(text[i]):
                    raise TokenError(text[i], line_number)

                buffer += text[i]
            continue

        # check for null
        if text[i] == "n":
            if i + 3 >= n:
                raise TokenError(text[i], line_number)
            if text[i:i+4] != "null":
                raise TokenError(text[i], line_number)
            token_list.append(Token(Tag.NULL))
            i += 4
            continue

        # this assumes that a valid match will end in a continue statement,
        # so if we reach this point then an invalid token was encountered
        raise TokenError(text[i-1], line_number)

    return token_list


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

    # TODO: test that error messages are correct

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
        "ab\\b":
        "\\t\\f\\n":
        "\\u1234":
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


if __name__ == "__main__":
    unittest.main()
