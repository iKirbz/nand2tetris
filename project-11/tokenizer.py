import re
from enum import Enum
from dataclasses import dataclass


class TokenType(Enum):
    KEYWORD = "keyword"
    SYMBOL = "symbol"
    INTEGER_CONSTANT = "integerConstant"
    STRING_CONSTANT = "stringConstant"
    IDENTIFIER = "identifier"


@dataclass
class Token:
    value: str
    type: TokenType


TOKEN_REGEX_GROUPS = re.compile(
    r"""
    (?P<KEYWORD>\b(?:class|constructor|function|method|field|static|var|
                   int|char|boolean|void|true|false|null|this|
                   let|do|if|else|while|return)\b)
    |(?P<SYMBOL>[{}()\[\].,;+\-*/&|<>=~])
    |(?P<INTEGER_CONSTANT>\d+)
    |"(?P<STRING_CONSTANT>[^"\n]*)"
    |(?P<IDENTIFIER>[a-zA-Z_]\w*)
""",
    re.VERBOSE,
)


def get_tokens(jack_code: str) -> list[Token]:
    tokens: list[Token] = []
    for match in TOKEN_REGEX_GROUPS.finditer(jack_code):
        if match.lastgroup:
            token_value = match.group(match.lastgroup)
            token_type = TokenType[match.lastgroup]

            tokens.append(Token(token_value, token_type))

    return tokens


def remove_comments(jack_code: str) -> str:
    jack_code = re.sub(r"//.*", "", jack_code)
    jack_code = re.sub(r"/\*.*?\*/", "", jack_code, flags=re.DOTALL)
    return jack_code


def tokenize(file: str):
    with open(file, "r", encoding="utf-8") as f:
        jack_code = f.read()

    cleaned_code = remove_comments(jack_code)
    tokens = get_tokens(cleaned_code)
    return tokens
