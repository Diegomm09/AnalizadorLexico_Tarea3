"""
parser.py – Analizador sintáctico descendente recursivo (LL(1)) para JSON simplificado.

Modificado para la Tarea 3: 
Ahora construye y devuelve un Árbol de Sintaxis Abstracta (AST) de las clases de `ast_nodes`.
También se integra con `logger` para registrar el proceso.
"""

from dataclasses import dataclass
from typing import Iterable, Optional, Set, Tuple, Dict, List

from lexer.token import Token, TokenType  # type: ignore
from lexer.lexer import Lexer  # type: ignore
from ast_nodes import JSONNode, JSONObject, JSONArray, JSONPrimitive
from logger import get_logger

logger = get_logger()

# ---------------------------------------------------------------------------
#  Definición de error sintáctico (propio del parser)
# ---------------------------------------------------------------------------

@dataclass
class SyntaxErrorInfo:
    message: str
    line: int
    col: int
    found: TokenType


# ---------------------------------------------------------------------------
#  Conjuntos de sincronización (panic mode)
# ---------------------------------------------------------------------------

SYNC_GENERAL: Set[TokenType] = {
    TokenType.L_LLAVE,
    TokenType.R_LLAVE,
    TokenType.L_CORCHETE,
    TokenType.R_CORCHETE,
    TokenType.COMA,
    TokenType.DOS_PUNTOS,
    TokenType.EOF,
}

FOLLOW_JSON: Set[TokenType] = {TokenType.EOF}

FOLLOW_ELEMENT: Set[TokenType] = {
    TokenType.COMA,
    TokenType.R_CORCHETE,
    TokenType.R_LLAVE,
    TokenType.EOF,
}

FOLLOW_OBJECT: Set[TokenType] = FOLLOW_ELEMENT
FOLLOW_ARRAY: Set[TokenType] = FOLLOW_ELEMENT

FOLLOW_ATTRIBUTES_LIST: Set[TokenType] = {
    TokenType.R_LLAVE,
    TokenType.EOF,
}

FOLLOW_ATTRIBUTE: Set[TokenType] = {
    TokenType.COMA,
    TokenType.R_LLAVE,
    TokenType.EOF,
}

FOLLOW_ATTRIBUTE_VALUE: Set[TokenType] = FOLLOW_ATTRIBUTE.copy()


# ---------------------------------------------------------------------------
#  Clase Parser
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self._token_iter = iter(self.tokens)
        self.current: Token = self._next_token()

        self.syntax_errors: list[SyntaxErrorInfo] = []
        self.had_errors: bool = False

    def _next_token(self) -> Token:
        try:
            return next(self._token_iter)
        except StopIteration:
            return Token(TokenType.EOF, "", line=0, col=0)

    def advance(self) -> None:
        if self.current.type == TokenType.EOF:
            return
        self.current = self._next_token()

    def lookahead_type(self) -> TokenType:
        return self.current.type

    def error(self, message: str) -> None:
        self.had_errors = True
        err = SyntaxErrorInfo(
            message=message,
            line=self.current.line,
            col=self.current.col,
            found=self.current.type,
        )
        self.syntax_errors.append(err)
        logger.error(f"Error de Sintaxis (línea {err.line}, col {err.col}): {message} (Encontrado: {err.found.name})")

    def sync(self, follow_set: Set[TokenType]) -> None:
        while (
            self.current.type not in follow_set
            and self.current.type not in SYNC_GENERAL
            and self.current.type != TokenType.EOF
        ):
            self.advance()

    def match(self, expected: TokenType, follow_set: Set[TokenType]) -> bool:
        if self.current.type == expected:
            self.advance()
            return True

        msg = f"Se esperaba {expected.name} pero se encontro {self.current.type.name}."
        self.error(msg)
        self.sync(follow_set)
        return False

    def parse(self) -> Optional[JSONNode]:
        logger.info("Iniciando analisis sintactico (Parser)...")
        ast_root = self.json()
        if self.current.type != TokenType.EOF:
            self.error("Se encontraron tokens adicionales despues del elemento raiz del JSON.")
        
        if self.had_errors:
            logger.warning("El analisis sintactico finalizo con errores (Panic Mode activado).")
        else:
            logger.info("Analisis sintactico completado con exito.")
            
        return ast_root

    def print_syntax_errors(self) -> None:
        if not self.had_errors:
            print("JSON sintácticamente correcto (sin errores sintácticos).")
            return

        print("Se encontraron errores sintácticos:")
        for e in self.syntax_errors:
            print(f"  - linea={e.line}, col={e.col}: {e.message} (token encontrado: {e.found.name})")

    # ----------------------------
    #  Reglas de la gramática
    # ----------------------------

    def json(self) -> Optional[JSONNode]:
        if self.current.type in (TokenType.L_LLAVE, TokenType.L_CORCHETE):
            return self.element()
        else:
            self.error("Se esperaba un objeto '{' o un arreglo '[' al inicio del JSON.")
            self.sync(FOLLOW_JSON)
            return None

    def element(self) -> Optional[JSONNode]:
        t = self.current.type
        if t == TokenType.L_LLAVE:
            return self.object()
        elif t == TokenType.L_CORCHETE:
            return self.array()
        else:
            self.error("Se esperaba un objeto '{' o un arreglo '[' como elemento.")
            self.sync(FOLLOW_ELEMENT)
            return None

    def object(self) -> Optional[JSONObject]:
        if not self.match(TokenType.L_LLAVE, FOLLOW_OBJECT):
            return JSONObject() # Recuperación parcial

        if self.current.type == TokenType.R_LLAVE:
            self.advance()
            return JSONObject()

        attrs = self.attributes_list()

        if not self.match(TokenType.R_LLAVE, FOLLOW_OBJECT):
            pass # Sincronizado

        return JSONObject(attributes=attrs)

    def attributes_list(self) -> Dict[str, JSONNode]:
        attrs = {}
        attr = self.attribute()
        if attr:
            attrs[attr[0]] = attr[1]

        while self.current.type == TokenType.COMA:
            self.advance()
            if self.current.type == TokenType.R_LLAVE:
                self.error("No se permite una coma final después del último atributo.")
                break
            attr = self.attribute()
            if attr:
                # Si la clave ya existe, en JSON genérico puede sobreescribir. Lo mantenemos simple.
                attrs[attr[0]] = attr[1]

        return attrs

    def attribute(self) -> Optional[Tuple[str, JSONNode]]:
        key_name = ""
        if self.current.type in (TokenType.LITERAL_CADENA, TokenType.LITERAL_CADENA_VACIA):
            key_name = self.current.lexeme
            self.advance()
        else:
            self.error("Se esperaba un literal de cadena como nombre de atributo.")
            self.sync(FOLLOW_ATTRIBUTE)
            return None

        if not self.match(TokenType.DOS_PUNTOS, FOLLOW_ATTRIBUTE):
            return None

        val = self.attribute_value()
        if val is not None:
            return (key_name, val)
        return None

    def attribute_value(self) -> Optional[JSONNode]:
        t = self.current.type

        if t in (TokenType.L_LLAVE, TokenType.L_CORCHETE):
            return self.element()

        if t in (TokenType.LITERAL_CADENA, TokenType.LITERAL_CADENA_VACIA):
            val = JSONPrimitive(self.current.lexeme)
            self.advance()
            return val

        if t == TokenType.LITERAL_NUM:
            val = JSONPrimitive(self.current.lexeme)
            self.advance()
            return val

        if t in (TokenType.PR_TRUE, TokenType.PR_FALSE, TokenType.PR_NULL):
            val = JSONPrimitive(self.current.lexeme)
            self.advance()
            return val

        self.error("Se esperaba un valor válido (objeto, arreglo, cadena, número, true, false o null) como valor de atributo.")
        self.sync(FOLLOW_ATTRIBUTE_VALUE)
        return None

    def array(self) -> Optional[JSONArray]:
        if not self.match(TokenType.L_CORCHETE, FOLLOW_ARRAY):
            return JSONArray()

        if self.current.type == TokenType.R_CORCHETE:
            self.advance()
            return JSONArray()

        elems = self.element_list()

        if not self.match(TokenType.R_CORCHETE, FOLLOW_ARRAY):
            pass

        return JSONArray(elements=elems)

    def element_list(self) -> List[JSONNode]:
        elems = []
        elem = self.element()
        if elem is not None:
            elems.append(elem)

        while self.current.type == TokenType.COMA:
            self.advance()
            if self.current.type == TokenType.R_CORCHETE:
                self.error("No se permite una coma final después del último elemento del arreglo.")
                break
            elem = self.element()
            if elem is not None:
                elems.append(elem)

        return elems
