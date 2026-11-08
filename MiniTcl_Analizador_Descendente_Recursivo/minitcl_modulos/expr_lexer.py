# -*- coding: utf-8 -*-
"""Lexer de expresiones con sly.Lexer (sección 5)."""
from sly import Lexer
from model import Span, ParseError

class ExprLexer(Lexer):
    tokens = {
        NUMBER, BOOL, VAR, STRING, CMD_SUBST,
        OR, AND, EQ, NE, STREQ, STRNE,
        LT, LE, GT, GE,
        PLUS, MINUS, TIMES, DIVIDE, MOD, POWER, NOT,
        LPAREN, RPAREN
    }
    ignore = ' \t\r\n'

    POWER = r'\*\*'
    EQ = r'=='
    NE = r'!='
    LE = r'<='
    GE = r'>='
    OR = r'\|\|'
    AND = r'&&'

    LT = r'<'
    GT = r'>'
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    MOD = r'%'
    NOT = r'!'
    LPAREN = r'\('
    RPAREN = r'\)'

    STREQ = r'\beq\b'
    STRNE = r'\bne\b'
    BOOL = r'\b(true|false|yes|no|on|off)\b'
    NUMBER = r'(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
    VAR = r'\$[A-Za-z_][A-Za-z0-9_]*'
    STRING = r'"[^"\\]*"'

    @_(r'\[')
    def CMD_SUBST(self, token):
        if self.read_substitution is None:
            position = self.base_offset + token.index
            raise ParseError(
                "CMD_SUBST requiere el callback read_substitution",
                Span(position, position + 1, self.source_name))

        script, next_index = self.read_substitution(
            self.text, token.index, self.base_offset, self.source_name)

        token.value = script
        self.index = next_index
        return token

    def __init__(self, read_substitution=None, base_offset=0, source_name='<expr>'):
        self.base_offset = base_offset
        self.source_name = source_name
        self.read_substitution = read_substitution

    def error(self, token):
        position = self.base_offset + token.index
        raise ParseError(
            f"Carácter inválido en expresión: {token.value}",
            Span(position, position + len(token.value), self.source_name))
