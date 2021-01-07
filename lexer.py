"""
Title: JSON Lexer
Author: Brent Pappas
"""

# resources
# https://www.json.org/json-en.html (visual, very nice)

import unicodedata
from enum import Enum
from typing import List


class TokenError(Exception):
    """ Class for token errors """

    def __init__(self, character, line_number, message="Token error") -> None:
        self.character = character
        self.line_number = line_number
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}: Unexpected character '{self.character}' at line {self.line_number}"


class Tag(Enum):
    """ Enum for token tags """

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
    '''
    Base class for lexical tokens, and for tokens which do not have an
    attribute.
    '''

    def __init__(self, tag: 'Tag') -> None:
        self.tag = tag

    def __repr__(self) -> str:
        return f"({self.tag})"

    def __eq__(self, o: 'Token') -> bool:
        return self.tag == o.tag


class Number(Token):
    ''' Class for tokens representing integers and floating point numbers '''

    def __init__(self, value: 'Tag') -> None:
        super().__init__(Tag.NUMBER)
        self.value = value

    def __repr__(self) -> str:
        return f"({self.tag}, {self.value})"

    def __eq__(self, o: 'Number') -> bool:
        return self.tag == o.tag and self.value == o.value


class Literal(Token):
    ''' Class for tokens representing string literals '''

    def __init__(self, lexeme: str) -> None:
        super().__init__(Tag.LITERAL)
        self.lexeme = lexeme

    def __repr__(self) -> str:
        return f"({self.tag}, {self.lexeme})"

    def __eq__(self, o: 'Literal') -> bool:
        return self.tag == o.tag and self.lexeme == o.lexeme


class ObjectKey(Literal):
    ''' Class for tokens representing strings that are object keys '''

    def __init__(self, lexeme: str) -> None:
        super().__init__(lexeme)
        self.tag = Tag.OBJECT_KEY


class Boolean(Token):
    ''' Class for tokens representing boolean values '''

    def __init__(self, value: bool) -> None:
        super().__init__(Tag.BOOLEAN)
        self.value = value

    def __repr__(self) -> str:
        return f"({self.tag}, {self.value})"

    def __eq__(self, o: 'Boolean') -> bool:
        return self.tag == o.tag and self.value == o.value


def lex(text: str) -> List['Token']:
    '''
    Args:
        text: The JSON text to lex into tokens

    Returns:
        list: A list of JSON tokens

    '''
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
                    # it may have been better to have made colon into a token, but this works
                    while i + 1 < n and text[i+1].isspace():
                        if text[i + 1] == "\n":
                            line_number += 1
                        i += 1
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
