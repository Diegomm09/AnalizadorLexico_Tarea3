from typing import Generator, Tuple
from .input_stream import InputStream
from .token import Token, TokenType
from .errors import LexErrorCode, LexError, HINTS
from .error_reporter import ErrorReporter

class Lexer:
    """
    Reglas:
      - Estructurales: { } [ ] , :
      - Literales entre comillas:
          ""   -> LITERAL_CADENA_VACIA
          "a"  -> LITERAL_CADENA
      - Números:
          LITERAL_NUM -> [+-]?[0-9]+(\.[0-9]+)?((e|E)(+|-)?[0-9]+)?
      - Keywords SIN comillas: TRUE / FALSE / NULL
      - Recuperación (panic mode).
    """

    SYNC_SET = set(['{', '}', '[', ']', ',', ':', '"'])

    def __init__(self, stream: InputStream, reporter: ErrorReporter):
        self.s = stream
        self.reporter = reporter
        self.keywords = {
            "TRUE": TokenType.PR_TRUE,
            "FALSE": TokenType.PR_FALSE,
            "NULL": TokenType.PR_NULL,
        }

    def tokenize(self) -> Generator[Tuple[str, object], None, None]:
        while not self.s.eof():
            ch = self._peek_non_whitespace()
            if ch == "":
                break

            line, col, _ = self.s.location()

            if ch in "{}[],:":
                self.s.advance()
                tok = self._make_struct_token(ch, line, col)
                self.reporter.inc_tokens()
                yield ("TOKEN", tok)
                continue

            if ch == '"':
                yield from self._scan_quoted_literal()
                continue

            # Números sin comillas
            if ch.isdigit() or ch in "+-":
                yield from self._scan_number()
                continue

            if ch.isalpha():
                yield from self._scan_keyword_or_ident()
                continue

            err = LexError(
                code=LexErrorCode.CARACTER_NO_RECONOCIDO,
                line=line, col=col, lexeme=ch,
                hint=HINTS[LexErrorCode.CARACTER_NO_RECONOCIDO]
            )
            yield ("ERROR", err)
            self._panic_recover()

        eof_line, eof_col, _ = self.s.location()
        eof = Token(TokenType.EOF, "", eof_line, eof_col)
        self.reporter.inc_tokens()
        yield ("TOKEN", eof)

    def _peek_non_whitespace(self) -> str:
        while not self.s.eof():
            ch = self.s.peek()
            if ch == "\ufeff":
                self.s.advance()
                continue
            if ch.isspace():
                self.s.advance()
                continue
            break
        return "" if self.s.eof() else self.s.peek()

    def _make_struct_token(self, ch: str, line: int, col: int) -> Token:
        mapping = {
            '{': TokenType.L_LLAVE,
            '}': TokenType.R_LLAVE,
            '[': TokenType.L_CORCHETE,
            ']': TokenType.R_CORCHETE,
            ',': TokenType.COMA,
            ':': TokenType.DOS_PUNTOS,
        }
        return Token(mapping[ch], ch, line, col)

    def _scan_quoted_literal(self):
        quote_line, quote_col, _ = self.s.location()
        self.s.advance()  # consume '"'

        if self.s.eof():
            err = LexError(
                code=LexErrorCode.CADENA_NO_CERRADA,
                line=quote_line, col=quote_col,
                lexeme='"', hint=HINTS[LexErrorCode.CADENA_NO_CERRADA]
            )
            yield ("ERROR", err)
            return

        content = []
        while not self.s.eof() and self.s.peek() != '"' and self.s.peek() != "\n":
            content.append(self.s.advance())

        if self.s.eof() or self.s.peek() == "\n":
            err = LexError(
                code=LexErrorCode.CADENA_NO_CERRADA,
                line=quote_line, col=quote_col,
                lexeme='"' + "".join(content) + '...', hint=HINTS[LexErrorCode.CADENA_NO_CERRADA]
            )
            yield ("ERROR", err)
            self._panic_recover()
            return

        self.s.advance()  # consume cierre '"'
        str_val = "".join(content)
        
        # Guardar el contenido EXACTO con comillas incluidas para el XML o al menos la cadena 
        # para preservar los datos literales. Agregamos las comillas explícitamente.
        full_lexeme = f'"{str_val}"'
        
        if str_val == "":
            tok = Token(TokenType.LITERAL_CADENA_VACIA, full_lexeme, quote_line, quote_col)
        else:
            tok = Token(TokenType.LITERAL_CADENA, full_lexeme, quote_line, quote_col)
            
        self.reporter.inc_tokens()
        yield ("TOKEN", tok)

    def _scan_number(self):
        line, col, _ = self.s.location()
        content = []
        while not self.s.eof():
            ch = self.s.peek()
            if ch.isdigit() or ch in "+-.eE":
                content.append(self.s.advance())
            else:
                break
        
        num = "".join(content)
        ok, err = self._validate_number(num, line, col)
        if ok:
            tok = Token(TokenType.LITERAL_NUM, num, line, col)
            self.reporter.inc_tokens()
            yield ("TOKEN", tok)
        else:
            yield ("ERROR", err)
            self._panic_recover()

    def _validate_number(self, s: str, line: int, col: int):
        i, n = 0, len(s)

        def make_err(code: LexErrorCode, msg: str):
            return LexError(code=code, line=line, col=col, lexeme=s, hint=msg)

        if n == 0:
            return (False, make_err(LexErrorCode.NUMERO_MAL_FORMATO, "Número vacío."))

        if s[i] in "+-":
            i += 1
            if i >= n:
                return (False, make_err(LexErrorCode.NUMERO_MAL_FORMATO, "Se esperaba al menos un dígito después del signo."))

        if i >= n or not s[i].isdigit():
            return (False, make_err(LexErrorCode.NUMERO_MAL_FORMATO, "Se requieren dígitos (0-9) en la parte entera."))

        while i < n and s[i].isdigit():
            i += 1

        if i < n and s[i] == '.':
            i += 1
            if i >= n or not s[i].isdigit():
                return (False, make_err(LexErrorCode.NUMERO_MAL_DECIMAL, "Después del punto debe haber uno o más dígitos."))
            while i < n and s[i].isdigit():
                i += 1

        if i < n and s[i] in 'eE':
            i += 1
            if i < n and s[i] in '+-':
                i += 1
            if i >= n or not s[i].isdigit():
                return (False, make_err(LexErrorCode.NUMERO_MAL_EXP, "El exponente requiere uno o más dígitos."))
            while i < n and s[i].isdigit():
                i += 1

        if i != n:
            ch = s[i]
            return (False, make_err(LexErrorCode.NUMERO_MAL_FORMATO, f"Carácter inesperado '{ch}'."))

        return (True, None)

    def _scan_keyword_or_ident(self):
        line, col, _ = self.s.location()
        buf = []
        while not self.s.eof() and (self.s.peek().isalnum() or self.s.peek() == "_"):
            buf.append(self.s.advance())
        word = "".join(buf)
        up = word.upper()
        if up in self.keywords:
            tok = Token(self.keywords[up], word, line, col)
            self.reporter.inc_tokens()
            yield ("TOKEN", tok)
        else:
            err = LexError(
                code=LexErrorCode.IDENT_NO_RECONOCIDO,
                line=line, col=col, lexeme=word,
                hint=HINTS[LexErrorCode.IDENT_NO_RECONOCIDO]
            )
            yield ("ERROR", err)
            self._panic_recover()

    def _panic_recover(self):
        while not self.s.eof():
            ch = self.s.peek()
            if ch in self.SYNC_SET:
                return
            self.s.advance()
