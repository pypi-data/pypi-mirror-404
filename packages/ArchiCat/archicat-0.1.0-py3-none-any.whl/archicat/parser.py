from .error import ArchiCatSyntaxError

from lark import Lark,Tree
from lark.exceptions import UnexpectedEOF,UnexpectedCharacters,UnexpectedToken
from pathlib import Path
from importlib.resources import files


grammar = files('archicat').joinpath('grammar.lark').read_text()
parser = Lark(grammar)

def parse(text: str) -> Tree:
    try:
        return parser.parse(text)
    except UnexpectedToken as exception:
        raise ArchiCatSyntaxError(exception.line,exception.column,f'Unexpected token {exception.token}')
    except UnexpectedCharacters as exception:
        raise ArchiCatSyntaxError(exception.line,exception.column,f'Unexpected character {exception.char}')
    except UnexpectedEOF as exception:
        raise ArchiCatSyntaxError(exception.line,exception.column,'Unexpected EOF')

def parse_file(path: Path | str) -> Tree:
    with open(str(path)) as file:
        return parse(file.read())