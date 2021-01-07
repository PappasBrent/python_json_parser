'''
__init__.py file to expose user-friendly API
'''

from typing import Dict, List, Union

from .lexer import lex
from .parser_ import parse


def load_json_string(json: str) -> Union[Dict, List, None]:
    return parse(lex(json))
