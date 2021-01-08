"""
Title: JSON Parser
Author: Brent Pappas
"""

from typing import Dict, List, Union

from .lexer import Tag, Token


class ParseError(Exception):
    """ Class for parse errors """

    def __init__(self, token: 'Token', expected: List[Tag], message="Parse error") -> None:
        self.token = token
        self.expected = expected
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"Parse error: Unexpected token {self.token.tag.name}. Expected one of {[t.name for t in self.expected]}"


def parse(tokens: List['Token']) -> Union[Dict, List, None]:
    '''
    Args:
        tokens: A list of JSON lexical tokens

    Returns:
        dict: A Python dictionary object containing the parsed JSON
        | list: A Python list containing the parsed JSON
        | None: The Python None value

    Each of the parser's recursive functions are implemented as a nested
    function. It may be better to refactor this code in the future so that
    each of these functions may be individually unit tested

    '''

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
