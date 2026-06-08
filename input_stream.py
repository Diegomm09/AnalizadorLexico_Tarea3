from dataclasses import dataclass

@dataclass
class Position:
    line: int = 1
    col: int = 1
    index: int = 0

class InputStream:
    def __init__(self, text: str):
        self.text = text
        self.pos = Position()

    def eof(self) -> bool:
        return self.pos.index >= len(self.text)

    def peek(self, k: int = 0) -> str:
        idx = self.pos.index + k
        if idx < 0 or idx >= len(self.text):
            return ""
        return self.text[idx]

    def advance(self) -> str:
        if self.eof():
            return ""
        ch = self.text[self.pos.index]
        self.pos.index += 1
        if ch == "\n":
            self.pos.line += 1
            self.pos.col = 1
        else:
            self.pos.col += 1
        return ch

    def location(self):
        return self.pos.line, self.pos.col, self.pos.index
