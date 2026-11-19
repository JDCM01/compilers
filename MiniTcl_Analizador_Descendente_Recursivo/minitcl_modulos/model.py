# -*- coding: utf-8 -*-
"""Modelo del AST e infraestructura mínima (secciones 8 y 9)."""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from typing import Literal as Mode

@dataclass(frozen=True)
class Span:
    start: int
    end: int
    source: str = "<input>"

@dataclass(frozen=True, kw_only=True)
class Node:
    span: Span

@dataclass(frozen=True)
class Literal(Node):
    text: str

@dataclass(frozen=True)
class Variable(Node):
    name: str
    index: str | None = None

@dataclass(frozen=True)
class CommandSubstitution(Node):
    script: Script

Part = Literal | Variable | CommandSubstitution

@dataclass(frozen=True)
class Word(Node):
    parts: tuple[Part, ...]
    mode: Mode["bare", "quoted", "braced"] = "bare"

@dataclass(frozen=True)
class Command(Node):
    words: tuple[Word, ...]

@dataclass(frozen=True)
class Script(Node):
    commands: tuple[Command, ...]

@dataclass(frozen=True, kw_only=True)
class Expr(Node):
    pass

@dataclass(frozen=True)
class Constant(Expr):
    value: int | float | str | bool

@dataclass(frozen=True)
class VariableExpr(Expr):
    variable: Variable

@dataclass(frozen=True)
class SubstitutionExpr(Expr):
    script: Script

@dataclass(frozen=True)
class Unary(Expr):
    operator: str
    operand: Expr

@dataclass(frozen=True)
class Binary(Expr):
    operator: str
    left: Expr
    right: Expr


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    span: Span
    index: str | None = None

class ParseError(Exception):
    def __init__(self, message: str, span: Span):
        self.message = message
        self.span = span
        super().__init__(f"{span.source}:{span.start}: {message}")

class TokenCursor:
    def __init__(self, tokens):
        self.tokens = tuple(tokens)
        if not self.tokens or self.tokens[-1].kind != "EOF":
            raise ValueError("El lexer debe agregar EOF")
        self.position = 0

    @property
    def current(self):
        return self.tokens[self.position]

    def accept(self, kind):
        if self.current.kind != kind:
            return None
        token = self.current
        if kind != "EOF":
            self.position += 1
        return token

    def expect(self, kind):
        token = self.accept(kind)
        if token is None:
            raise ParseError(
                f"Se esperaba {kind}; se encontró {self.current.kind}",
                self.current.span)
        return token

    def skip(self, *kinds):
        while self.current.kind in kinds and self.current.kind != "EOF":
            self.position += 1


def cover(first: Span, last: Span):
    if first.source != last.source:
        raise ValueError("No combinar posiciones de fuentes diferentes")
    return Span(first.start, last.end, first.source)


def show_ast(value, indent=0):
    """Impresión estructurada del AST, sin dependencias externas."""
    prefix = " " * indent
    if is_dataclass(value):
        print(prefix + type(value).__name__)
        for field in fields(value):
            if field.name == "span":
                continue
            print(prefix + "  " + field.name + ":")
            show_ast(getattr(value, field.name), indent + 4)
    elif isinstance(value, tuple):
        for item in value:
            show_ast(item, indent)
    else:
        print(prefix + repr(value))
