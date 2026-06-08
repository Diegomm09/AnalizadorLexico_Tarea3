from enum import Enum, auto
from dataclasses import dataclass

class LexErrorCode(Enum):
    CARACTER_NO_RECONOCIDO = auto()
    CADENA_NO_CERRADA = auto()
    CADENA_INICIA_CARACTER_INVALIDO = auto()
    NUMERO_MAL_FORMADO_EN_CADENA = auto()  # (legacy) por compatibilidad
    IDENT_NO_RECONOCIDO = auto()
    # Nuevos errores numéricos específicos
    NUMERO_MAL_FORMATO = auto()    # formato general inválido (espacios, letras, falta de dígitos, etc.)
    NUMERO_MAL_DECIMAL = auto()    # punto sin dígitos a la derecha
    NUMERO_MAL_EXP = auto()        # exponente sin dígitos (o con signo sin dígitos)

HINTS = {
    LexErrorCode.CARACTER_NO_RECONOCIDO:
        'Caracter fuera del alfabeto. Se esperaba { } [ ] , : " o un literal/keyword.',
    LexErrorCode.CADENA_NO_CERRADA:
        "Falta la comilla de cierre antes del fin de línea/archivo.",
    LexErrorCode.CADENA_INICIA_CARACTER_INVALIDO:
        "Un literal entre comillas debe iniciar con letra (cadena) o dígito/signo (número).",
    LexErrorCode.NUMERO_MAL_FORMADO_EN_CADENA:
        "Literal numérico inválido dentro de comillas.",
    LexErrorCode.IDENT_NO_RECONOCIDO:
        "Identificador desconocido. Use TRUE/FALSE/NULL (sin comillas) o literales entre comillas.",
    # Hints por defecto para los nuevos errores (pueden ser reemplazados dinámicamente)
    LexErrorCode.NUMERO_MAL_FORMATO:
        "Formato numérico inválido. Se permiten: [+-]?[0-9]+(.[0-9]+)?((e|E)(+|-)?[0-9]+)?",
    LexErrorCode.NUMERO_MAL_DECIMAL:
        "Después del punto decimal debe haber uno o más dígitos.",
    LexErrorCode.NUMERO_MAL_EXP:
        "El exponente debe tener uno o más dígitos (opcionalmente precedidos por + o -).",
}

@dataclass
class LexError:
    code: LexErrorCode
    line: int
    col: int
    lexeme: str
    hint: str
