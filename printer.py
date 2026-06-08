from typing import Optional
from .token import Token, TokenType

class PrettyPrinter:
    """
    Pretty-print de tokens, independiente del formato de entrada.
      - L_LLAVE / L_CORCHETE: imprime token, salto de línea, indent++.
      - R_LLAVE / R_CORCHETE: indent--, salto de línea, imprime token.
      - COMA: imprime token y salto de línea.
      - DOS_PUNTOS: en la misma línea.
      - Literales y PR_*: en la misma línea.
      - EOF: nueva línea.
    """
    def __init__(self):
        self.indent = 0
        self.line_buf = ""
        self.out = []

    def _emit_line(self):
        if self.line_buf != "":
            self.out.append(("  " * self.indent) + self.line_buf + "\n")
            self.line_buf = ""

    def _emit_token_inline(self, token_name: str):
        if self.line_buf:
            self.line_buf += " " + token_name
        else:
            self.line_buf = token_name

    def feed_error_line(self, error_line: str):
        # cerrar lo que haya y dejar una línea en blanco antes del error
        self._emit_line()
        self.out.append("\n")  # <-- línea en blanco de separación
        self.out.append(("  " * self.indent) + error_line + "\n")

    def feed_token(self, token: Token) -> Optional[str]:
        t = token.type

        def name(tt: TokenType) -> str:
            return tt.name

        if t in (TokenType.R_LLAVE, TokenType.R_CORCHETE):
            self._emit_line()
            if self.indent > 0:
                self.indent -= 1
            self._emit_token_inline(name(t))
            self._emit_line()
            return None

        if t in (TokenType.L_LLAVE, TokenType.L_CORCHETE):
            self._emit_token_inline(name(t))
            self._emit_line()
            self.indent += 1
            return None

        if t == TokenType.COMA:
            self._emit_token_inline(name(t))
            self._emit_line()
            return None

        if t == TokenType.DOS_PUNTOS:
            self._emit_token_inline(name(t))
            return None

        if t in (
            TokenType.LITERAL_CADENA, TokenType.LITERAL_CADENA_VACIA, TokenType.LITERAL_NUM,
            TokenType.PR_TRUE, TokenType.PR_FALSE, TokenType.PR_NULL
        ):
            self._emit_token_inline(name(t))
            return None

        if t == TokenType.EOF:
            self._emit_line()
            self._emit_token_inline(name(t))
            self._emit_line()
            return None

        self._emit_token_inline(name(t))
        return None

    def flush(self) -> Optional[str]:
        if self.line_buf:
            last = ("  " * self.indent) + self.line_buf + "\n"
            self.line_buf = ""
            return last
        return None
