# -*- coding: utf-8 -*-
"""Lexer manual de scripts MiniTcl (sección 3)."""
from model import Span, Token, ParseError

# === Lexer de scripts (PARCHADO) ===
# Arreglos sobre la base:
#  1) Soporta la forma ${nombre}
#  2) Decodifica escapes fuera de llaves (TEXT ya viene decodificado)
#  3) Restringe el indice de arreglo (rechaza $a($i)) y normaliza CRLF/CR

ESCAPES = {
    'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', ' ': ' ',
    '$': '$', '[': '[', ']': ']', '{': '{', '}': '}',
    '"': '"', ';': ';', '#': '#',
}

def _is_ident_start(c): return c.isascii() and (c.isalpha() or c == '_')
def _is_ident_char(c):  return c.isascii() and (c.isalnum() or c == '_')
def _is_index_char(c):  return _is_ident_char(c) or c in '.-:'

class ScriptLexer:
    def __init__(self, text: str, base_offset: int = 0, source_name: str = "<input>"):
        text = text.replace("\r\n", "\n").replace("\r", "\n")  # normalizar antes de medir offsets
        self.text = text
        self.base_offset = base_offset
        self.source_name = source_name
        self.pos = 0
        self.length = len(text)
        self.in_quotes = False

    def span(self, start, end):
        return Span(start + self.base_offset, end + self.base_offset, self.source_name)

    def error(self, msg, pos, end=None):
        raise ParseError(msg, self.span(pos, pos + 1 if end is None else end))

    def _decode_escape(self):
        start = self.pos
        if self.pos + 1 >= self.length:
            self.error("Escape '\\' incompleto al final de la fuente", start)
        nxt = self.text[self.pos + 1]
        if nxt == '\n':
            self.error("Continuacion de linea fuera del perfil", start, start + 2)
        if nxt in ESCAPES:
            self.pos += 2
            return ESCAPES[nxt]
        self.error(f"Escape desconocido '\\{nxt}'", start, start + 2)

    def _read_variable(self, tokens, start):
        self.pos += 1  # consumir '$'
        if self.pos < self.length and self.text[self.pos] == '{':   # forma ${nombre}
            self.pos += 1
            name_start = self.pos
            while self.pos < self.length and self.text[self.pos] != '}':
                self.pos += 1
            if self.pos >= self.length:
                self.error("'${' sin '}' de cierre", start)
            name = self.text[name_start:self.pos]
            if not name or not _is_ident_start(name[0]) or not all(_is_ident_char(ch) for ch in name):
                self.error("Nombre invalido en ${...}", start, self.pos + 1)
            self.pos += 1  # consumir '}'
            tokens.append(Token("VAR", name, self.span(start, self.pos)))
            return
        if self.pos >= self.length or not _is_ident_start(self.text[self.pos]):
            self.error("'$' sin un nombre de variable valido", start)
        name_start = self.pos
        while self.pos < self.length and _is_ident_char(self.text[self.pos]):
            self.pos += 1
        name = self.text[name_start:self.pos]
        index = None
        if self.pos < self.length and self.text[self.pos] == '(':
            self.pos += 1
            idx_start = self.pos
            while self.pos < self.length and self.text[self.pos] != ')':
                if not _is_index_char(self.text[self.pos]):
                    self.error("Indice de arreglo fuera del perfil lexico", self.pos)
                self.pos += 1
            if self.pos >= self.length:
                self.error("Indice de arreglo sin ')' de cierre", start)
            index = self.text[idx_start:self.pos]
            if index == "":
                self.error("Indice de arreglo vacio", start, self.pos + 1)
            self.pos += 1  # consumir ')'
        tokens.append(Token("VAR", name, self.span(start, self.pos), index=index))

    def tokenize(self):
        tokens = []
        at_command_start = True
        while self.pos < self.length:
            start = self.pos
            char = self.text[self.pos]

            if self.in_quotes:
                if char == '"':
                    self.pos += 1
                    tokens.append(Token("QCLOSE", char, self.span(start, self.pos)))
                    self.in_quotes = False
                    continue
                if char == '$':
                    self._read_variable(tokens, start); continue
                if char == '[':
                    self.pos += 1
                    tokens.append(Token("LBRACKET", char, self.span(start, self.pos))); continue
                run = []; text_start = self.pos
                while self.pos < self.length and self.text[self.pos] not in '"$[':
                    if self.text[self.pos] == '\\':
                        run.append(self._decode_escape())
                    else:
                        run.append(self.text[self.pos]); self.pos += 1
                if run:
                    tokens.append(Token("TEXT", "".join(run), self.span(text_start, self.pos)))
                continue

            if char in ' \t':
                self.pos += 1
                while self.pos < self.length and self.text[self.pos] in ' \t':
                    self.pos += 1
                tokens.append(Token("WS", self.text[start:self.pos], self.span(start, self.pos))); continue

            if char == '\n' or char == ';':
                self.pos += 1
                tokens.append(Token("SEP", char, self.span(start, self.pos)))
                at_command_start = True; continue

            if char == '#' and at_command_start:
                while self.pos < self.length and self.text[self.pos] != '\n':
                    self.pos += 1
                continue

            at_command_start = False

            if char == '{':
                self.pos += 1
                depth = 1; content_start = self.pos
                while self.pos < self.length and depth > 0:
                    c = self.text[self.pos]
                    if c == '\\' and self.pos + 1 < self.length and self.text[self.pos + 1] in '{}':
                        self.pos += 2; continue
                    if c == '{': depth += 1
                    elif c == '}':
                        depth -= 1
                        if depth == 0: break
                    self.pos += 1
                if depth != 0:
                    self.error("Falta llave de cierre '}'", start)
                content = self.text[content_start:self.pos]
                self.pos += 1  # consumir '}'
                tokens.append(Token("BRACED", content, self.span(start, self.pos)))
                if self.pos < self.length and self.text[self.pos] not in ' \t;\n]':
                    self.error("Texto pegado tras una palabra agrupada", self.pos)
                continue

            if char == '"':
                self.pos += 1
                tokens.append(Token("QOPEN", char, self.span(start, self.pos)))
                self.in_quotes = True; continue

            if char == '[':
                self.pos += 1
                tokens.append(Token("LBRACKET", char, self.span(start, self.pos)))
                at_command_start = True; continue

            if char == ']':
                self.pos += 1
                tokens.append(Token("RBRACKET", char, self.span(start, self.pos))); continue

            if char == '$':
                self._read_variable(tokens, start); continue

            run = []; text_start = self.pos
            while self.pos < self.length:
                c = self.text[self.pos]
                if c in ' \t\r\n;[]$"':
                    break
                if c in '{}':
                    self.error(f"'{c}' no escapado en palabra no agrupada", self.pos)
                if c == '\\':
                    run.append(self._decode_escape())
                else:
                    run.append(c); self.pos += 1
            if run:
                tokens.append(Token("TEXT", "".join(run), self.span(text_start, self.pos))); continue
            self.error(f"Caracter inesperado: {char}", self.pos)

        tokens.append(Token("EOF", "", self.span(self.length, self.length)))
        return tokens
