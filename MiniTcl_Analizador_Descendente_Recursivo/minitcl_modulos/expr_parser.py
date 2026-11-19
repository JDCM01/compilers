# -*- coding: utf-8 -*-
"""Parser LALR(1) de expresiones con sly.Parser (sección 5)."""
from sly import Parser
from model import (Span, ParseError, cover,
                   Constant, VariableExpr, SubstitutionExpr, Unary, Binary, Variable)
from expr_lexer import ExprLexer

class ExprParser(Parser):
    tokens = ExprLexer.tokens
    start = 'expression'

    def __init__(self, text='', base_offset=0, source_name='<expr>'):
        self.text = text
        self.base_offset = base_offset
        self.source_name = source_name

    def _span(self, p, length=1):
        start = self.base_offset + p.index
        return Span(start, start + length, self.source_name)

    @_('logical_or')
    def expression(self, p):
        return p.logical_or

    @_('logical_or OR logical_and')
    def logical_or(self, p):
        return Binary(operator="||", left=p.logical_or, right=p.logical_and,
                      span=cover(p.logical_or.span, p.logical_and.span))

    @_('logical_and')
    def logical_or(self, p):
        return p.logical_and

    @_('logical_and AND equality')
    def logical_and(self, p):
        return Binary(operator="&&", left=p.logical_and, right=p.equality,
                      span=cover(p.logical_and.span, p.equality.span))

    @_('equality')
    def logical_and(self, p):
        return p.equality

    @_('equality EQ relational', 'equality NE relational',
       'equality STREQ relational', 'equality STRNE relational')
    def equality(self, p):
        op = "==" if p[1] == '==' else "!=" if p[1] == '!=' else p[1]
        return Binary(operator=op, left=p.equality, right=p.relational,
                      span=cover(p.equality.span, p.relational.span))

    @_('relational')
    def equality(self, p):
        return p.relational

    @_('relational LT additive', 'relational LE additive',
       'relational GT additive', 'relational GE additive')
    def relational(self, p):
        return Binary(operator=p[1], left=p.relational, right=p.additive,
                      span=cover(p.relational.span, p.additive.span))

    @_('additive')
    def relational(self, p):
        return p.additive

    @_('additive PLUS multiplicative', 'additive MINUS multiplicative')
    def additive(self, p):
        return Binary(operator=p[1], left=p.additive, right=p.multiplicative,
                      span=cover(p.additive.span, p.multiplicative.span))

    @_('multiplicative')
    def additive(self, p):
        return p.multiplicative

    @_('multiplicative TIMES unary', 'multiplicative DIVIDE unary', 'multiplicative MOD unary')
    def multiplicative(self, p):
        return Binary(operator=p[1], left=p.multiplicative, right=p.unary,
                      span=cover(p.multiplicative.span, p.unary.span))

    @_('unary')
    def multiplicative(self, p):
        return p.unary

    @_('PLUS unary', 'MINUS unary', 'NOT unary')
    def unary(self, p):
        return Unary(operator=p[0], operand=p.unary,
                     span=cover(self._span(p, len(p[0])), p.unary.span))

    @_('power')
    def unary(self, p):
        return p.power

    @_('primary POWER unary')
    def power(self, p):
        return Binary(operator="**", left=p.primary, right=p.unary,
                      span=cover(p.primary.span, p.unary.span))

    @_('primary')
    def power(self, p):
        return p.primary

    @_('LPAREN expression RPAREN')
    def primary(self, p):
        return p.expression

    @_('NUMBER')
    def primary(self, p):
        raw = p.NUMBER
        value = float(raw) if any(c in raw for c in '.eE') else int(raw)
        return Constant(value=value, span=self._span(p, len(raw)))

    @_('BOOL')
    def primary(self, p):
        val = p.BOOL.lower() in ('true', 'yes', 'on')
        return Constant(value=val, span=self._span(p, len(p.BOOL)))

    @_('STRING')
    def primary(self, p):
        val = p.STRING[1:-1]
        return Constant(value=val, span=self._span(p, len(p.STRING)))

    @_('VAR')
    def primary(self, p):
        name = p.VAR[1:]
        return VariableExpr(variable=Variable(name=name, span=self._span(p, len(p.VAR))),
                            span=self._span(p, len(p.VAR)))

    @_('CMD_SUBST')
    def primary(self, p):
        return SubstitutionExpr(script=p.CMD_SUBST, span=self._span(p, 1))

    def error(self, token):
        if token is None:
            position = self.base_offset + len(self.text)
            raise ParseError("Fin inesperado de expresión",
                             Span(position, position, self.source_name))
        position = self.base_offset + token.index
        raise ParseError(f"Token inesperado en expr: {token.type}",
                         Span(position, position + len(token.value), self.source_name))
