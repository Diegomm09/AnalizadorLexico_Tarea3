import logging
import sys

def get_logger(name="json2xml_translator"):
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # 1. Console Handler con colores ANSI
    # PowerShell moderno (Windows 10+) soporta ANSI escape codes.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    class ColoredFormatter(logging.Formatter):
        RESET = "\033[0m"
        RED = "\033[31m"
        YELLOW = "\033[33m"
        GREEN = "\033[32m"
        CYAN = "\033[36m"
        BOLD = "\033[1m"

        def format(self, record):
            # Colores segun nivel o titulo
            color = self.RESET
            msg = record.getMessage()

            if record.levelno == logging.ERROR:
                color = self.RED
            elif record.levelno == logging.WARNING:
                color = self.YELLOW
            elif record.levelno == logging.INFO:
                # Si es un titulo de fase, poner en Cyan
                if msg.startswith("===") or "FASE" in msg:
                    color = self.CYAN
                else:
                    color = self.GREEN

            time_str = self.formatTime(record, self.datefmt)
            return f"{self.BOLD}{color}[{time_str}] {record.levelname}{self.RESET}\n    |--> {msg}"

    console_handler.setFormatter(ColoredFormatter())

    # 2. File Handler para server.log (SIN colores ANSI, utf-8-sig para bloc de notas)
    file_handler = logging.FileHandler("server.log", encoding="utf-8-sig")
    file_handler.setLevel(logging.DEBUG)

    class PlainFormatter(logging.Formatter):
        def format(self, record):
            time_str = self.formatTime(record, self.datefmt)
            return f"[{time_str}] {record.levelname}\n    |--> {record.getMessage()}"

    file_handler.setFormatter(PlainFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
