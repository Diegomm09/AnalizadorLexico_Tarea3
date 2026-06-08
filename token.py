from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    L_CORCHETE = auto()      # [
    R_CORCHETE = auto()      # ]
    L_LLAVE = auto()         # {
    R_LLAVE = auto()         # }
    COMA = auto()            # ,
    DOS_PUNTOS = auto()      # :
    LITERAL_CADENA = auto()  # "a..." (debe iniciar con letra; interior libre)
    LITERAL_CADENA_VACIA = auto()  # ""
    LITERAL_NUM = auto()     # "123"
    PR_TRUE = auto()         # true/TRUE (sin comillas)
    PR_FALSE = auto()        # false/FALSE (sin comillas)
    PR_NULL = auto()         # null/NULL (sin comillas)
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    lexeme: str = ""
    line: int = 0
    col: int = 0
