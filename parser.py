"""
Title: JSON Parser
Author: Brent Pappas
Date: 1-6-2021
"""

from typing import List
import unittest
from lexer import Tag, lex, Token


class ParseError(Exception):
    """ Class for parse errors """

    def __init__(self, token: 'Token', expected: List[Tag], message="Parse error") -> None:
        self.token = token
        self.expected = expected
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"Parse error: Unexpected token {self.token.tag.name}. Expected one of {[t.name for t in self.expected]}"


def parse(tokens: List['Token']):

    if tokens == []:
        return None

    def structure(tokens: List['Token']):
        t = tokens[-1]
        if t.tag not in [Tag.LEFT_BRACKET, Tag.LEFT_BRACE]:
            raise ParseError(t, [Tag.LEFT_BRACKET, Tag.LEFT_BRACE])
        elif t.tag == Tag.LEFT_BRACKET:
            return array(tokens)
        elif t.tag == Tag.LEFT_BRACE:
            return object_(tokens)

    def array(tokens: List['Token']):
        result = []
        t = tokens.pop()
        if t.tag != Tag.LEFT_BRACKET:
            raise ParseError(t, Tag.LEFT_BRACKET)

        t = tokens[-1]
        # check for empty array
        if t.tag == Tag.RIGHT_BRACKET:
            tokens.pop()
            return result

        while True:
            result.append(value(tokens))
            t = tokens.pop()
            if t.tag != Tag.COMMA:
                break

        if t.tag != Tag.RIGHT_BRACKET:
            raise ParseError(t, [Tag.RIGHT_BRACKET])

        return result

    def object_(tokens: List['Token']):
        result = {}
        t = tokens.pop()
        if t.tag != Tag.LEFT_BRACE:
            raise ParseError(t, Tag.LEFT_BRACE)

        t = tokens[-1]
        # check for empty array
        if t.tag == Tag.RIGHT_BRACE:
            tokens.pop()
            return result

        while True:
            t = tokens.pop()
            if t.tag != Tag.OBJECT_KEY:
                raise ParseError(t, [Tag.OBJECT_KEY])
            result[t.lexeme] = value(tokens)

            t = tokens.pop()
            if t.tag != Tag.COMMA:
                break

        if t.tag != Tag.RIGHT_BRACE:
            raise ParseError(t, [Tag.RIGHT_BRACE])

        return result

    def value(tokens: List['Token']):
        t = tokens.pop()
        if t.tag in [Tag.LEFT_BRACKET, Tag.LEFT_BRACE]:
            tokens.append(t)
            return structure(tokens)
        elif t.tag == Tag.LITERAL:
            return t.lexeme
        elif t.tag in [Tag.NUMBER, Tag.BOOLEAN]:
            return t.value
        elif t.tag == Tag.NULL:
            return None
        else:
            raise ParseError(t, [Tag.LEFT_BRACKET, Tag.LEFT_BRACE,
                                 Tag.LITERAL, Tag.NUMBER, Tag.BOOLEAN, Tag.NULL])

    # reverse tokens to support O(1) popping
    return structure(tokens[::-1])


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
            }''', {"test": {}})
        ]:
            self.assertEqual(parse(lex(test)), expected)


if __name__ == "__main__":
    unittest.main()
