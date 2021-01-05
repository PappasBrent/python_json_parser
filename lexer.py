# resources
# https://cswr.github.io/JsonSchema/spec/grammar/
# https://notes.eatonphil.com/writing-a-simple-json-parser.html (if you get stuck)

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


def lex(text: str):
    n = len(text)
    line_number = 1
    token_list = []
    i = 0
    round_off_digit = 15
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

            if i >= n or text[i] not in [".", "e"]:
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
            if i >= n or text[i] != "e":
                token_list.append(Number(v * (-1 if v_is_negative else 1)))
                continue

            # scientific notation
            # {invariant: text[i] == "e"}
            i += 1
            if i >= n:
                raise TokenError(text[i-1], line_number)

            # check if exponent is negative
            e_is_negative = False
            if text[i] == '-':
                e_is_negative = True
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

        # TODO: check for string literal / object key

        # TODO: check for boolean

        # TODO: check for array '[' and ']'

        # TODO: check for object '{' and '}'

        # TODO: check for null
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
        s = "1e2 2.1e3 3e-4"
        self.assertEqual(lex(s), [Number(100), Number(2100.0), Number(0.0003)])

    def test_lex_negatives(self):
        s = "-123 -45.6 -3e-4"
        # this may just be a quirk of the way this works, but
        # the input s = "-123-45.6-3e-4" works too. hmm...
        # ah should be fine since this is just lexing
        self.assertEqual(
            lex(s), [Number(-123), Number(-45.6), Number(-0.0003)])

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

    # TODO: test that error messages are correct
    def test_end_e(self):
        # TODO: should I add the single character e to this list later?
        tests = ["-3e", "1e", "e", "1.0e"]
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)

    def test_end_minus(self):
        tests = ["-3e-", "-", "1-", "1.0-"]
        for test in tests:
            with self.assertRaises(TokenError):
                lex(test)


if __name__ == "__main__":
    unittest.main()
