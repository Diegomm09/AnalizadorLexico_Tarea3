import sys
from typing import List
from .errors import LexError, HINTS, LexErrorCode

# ANSI
RST  = "\x1b[0m"
BOLD = "\x1b[1m"
DIM  = "\x1b[2m"

COLORS = {
    # genéricos
    LexErrorCode.CARACTER_NO_RECONOCIDO: "\x1b[31m",  # rojo
    LexErrorCode.CADENA_NO_CERRADA:      "\x1b[31m",  # rojo
    LexErrorCode.IDENT_NO_RECONOCIDO:    "\x1b[31m",  # rojo
    # strings
    LexErrorCode.CADENA_INICIA_CARACTER_INVALIDO: "\x1b[35m",  # magenta
    # números
    LexErrorCode.NUMERO_MAL_FORMATO:     "\x1b[33m",  # amarillo
    LexErrorCode.NUMERO_MAL_DECIMAL:     "\x1b[33m",
    LexErrorCode.NUMERO_MAL_EXP:         "\x1b[33m",
    # legacy
    LexErrorCode.NUMERO_MAL_FORMADO_EN_CADENA: "\x1b[33m",
}

LEX = "\x1b[36m" + BOLD  # cian y negrita para el lexema

class ErrorReporter:
    def __init__(self, ansi: bool = False):
        self.ansi = ansi
        self._errors: List[LexError] = []
        self._tokens_emitted = 0

    def inc_tokens(self, n: int = 1):
        self._tokens_emitted += n

    def add(self, err: LexError):
        self._errors.append(err)

    def has_errors(self) -> bool:
        return len(self._errors) > 0

    # --- Formatos de error ---
    def print_console(self, err: LexError):
        msg = self.format_error_for_console(err)
        print(msg, file=sys.stderr)

    def format_error_for_console(self, err: LexError) -> str:
        base = (
            f"{BOLD}ERROR({err.code.name}){RST} "
            f"{DIM}linea={err.line} col={err.col}{RST}; "
            f'lexema={LEX}"{err.lexeme}"{RST}\n'
            f"  pista: {err.hint}"
        )
        if self.ansi:
            color = COLORS.get(err.code, "\x1b[31m")
            return f"{color}{base}{RST}"
        return base

    # Para archivo (inline minimalista lo usamos desde programa.py)
    def format_error_for_file(self, err: LexError) -> str:
        return f'ERROR({err.code.name}) linea={err.line} col={err.col} lexema="{err.lexeme}" | pista="{err.hint}"'

    def format_error_inline(self, err: LexError) -> str:
        return f'tipo={err.code.name} lexema="{err.lexeme}"'

    # --- Resumen ---
    def summary_lines(self):
        lines = []
        lines.append("# RESUMEN")
        lines.append(f"# TOKENS_EMITIDOS: {self._tokens_emitted}")
        lines.append(f"# ERRORES: {len(self._errors)}")
        if self._errors:
            lines.append("# DETALLES_ERRORES:")
            for e in self._errors:
                lines.append(
                    f'#  - linea={e.line} col={e.col} tipo={e.code.name} lexema="{e.lexeme}" pista="{e.hint}"'
                )
        return lines
