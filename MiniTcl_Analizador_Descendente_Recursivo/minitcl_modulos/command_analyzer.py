# -*- coding: utf-8 -*-
"""Validación de comandos y fachadas de integración (secciones 6 y 13)."""
from dataclasses import dataclass
from model import (Span, ParseError, Script, Command, Word, Literal,
                   Variable, CommandSubstitution, Expr,
                   Constant, VariableExpr, SubstitutionExpr, Unary, Binary)
from script_lexer import ScriptLexer
from script_parser import ScriptParser
try:
    from expr_lexer import ExprLexer
    from expr_parser import ExprParser
    SLY_AVAILABLE = True
except Exception:
    SLY_AVAILABLE = False

#ACTIVIDAD ESCRIBIR ANALIZE_COMMAND
from dataclasses import dataclass

@dataclass(frozen=True)
class ArgumentAnalysis:
    word: Word
    expression: Expr | None = None
    script: Script | None = None
    substitutions: tuple['CommandAnalysis', ...] = ()

@dataclass(frozen=True)
class CommandAnalysis:
    command: Command
    name: str | None
    arguments: tuple[ArgumentAnalysis, ...]

def _literal_word_text(word: Word, role: str) -> str:
    if word.mode != "bare" or len(word.parts) != 1:
        raise ParseError(
            f"{role} debe ser una palabra literal simple",
            word.span)
    part = word.parts[0]
    if not isinstance(part, Literal):
        raise ParseError(
            f"{role} debe ser una palabra literal simple",
            word.span)
    return part.text

def _is_literal_word(word: Word, text: str) -> bool:
    return (
        word.mode == "bare"
        and len(word.parts) == 1
        and isinstance(word.parts[0], Literal)
        and word.parts[0].text == text)

def _braced_content(word: Word, role: str) -> tuple[str, int, str]:
    if word.mode != "braced" or len(word.parts) != 1:
        raise ParseError(f"{role} debe ser una palabra BRACED", word.span)
    part = word.parts[0]
    if not isinstance(part, Literal):
        raise ParseError(f"{role} debe ser una palabra BRACED", word.span)
    return part.text, word.span.start + 1, word.span.source

def _analyze_substitutions(word: Word) -> tuple[CommandAnalysis, ...]:
    result = []
    for part in word.parts:
        if isinstance(part, CommandSubstitution):
            result.extend(analyze_command(command)
                          for command in part.script.commands)
    return tuple(result)

def _analyze_expression(word: Word, role: str) -> Expr:
    text, offset, source_name = _braced_content(word, role)
    return parse_minitcl_expr(
        text, base_offset=offset, source_name=source_name)

def _analyze_script(word: Word, role: str) -> Script:
    text, offset, source_name = _braced_content(word, role)
    script = parse_minitcl(
        text, base_offset=offset, source_name=source_name)
    for command in script.commands:
        analyze_command(command)
    return script

def analyze_command(command: Command) -> CommandAnalysis:
    if not command.words:
        raise ParseError("El comando no puede estar vacío", command.span)

    name = _literal_word_text(command.words[0], "El nombre del comando")
    words = command.words[1:]
    analyses = [ArgumentAnalysis(
        word=word,
        substitutions=_analyze_substitutions(word))
        for word in words]

    def expression(index: int, role: str):
        analyses[index] = ArgumentAnalysis(
            word=analyses[index].word,
            expression=_analyze_expression(analyses[index].word, role),
            substitutions=analyses[index].substitutions)

    def script(index: int, role: str):
        analyses[index] = ArgumentAnalysis(
            word=analyses[index].word,
            script=_analyze_script(analyses[index].word, role),
            substitutions=analyses[index].substitutions)

    if name == "expr":
        if len(analyses) != 1:
            raise ParseError("expr requiere una expresión", command.span)
        expression(0, "La expresión de expr")
    elif name in {"while"}:
        if len(analyses) != 2:
            raise ParseError("while requiere condición y cuerpo", command.span)
        expression(0, "La condición de while")
        script(1, "El cuerpo de while")
    elif name == "for":
        if len(analyses) != 4:
            raise ParseError("for requiere cuatro argumentos", command.span)
        script(0, "La inicialización de for")
        expression(1, "La condición de for")
        script(2, "El paso de for")
        script(3, "El cuerpo de for")
    elif name == "foreach":
        if len(analyses) != 3:
            raise ParseError("foreach requiere variable, lista y cuerpo", command.span)
        script(2, "El cuerpo de foreach")
    elif name == "proc":
        if len(analyses) != 3:
            raise ParseError("proc requiere nombre, parámetros y cuerpo", command.span)
        ptext, _poff, _psrc = _braced_content(analyses[1].word, "Los parámetros de proc")
        _names = ptext.split()
        if len(_names) != len(set(_names)):
            raise ParseError("Parámetros duplicados en proc", analyses[1].word.span)
        script(2, "El cuerpo de proc")
    elif name == "catch":
        if not 1 <= len(analyses) <= 2:
            raise ParseError("catch requiere cuerpo y variable opcional", command.span)
        script(0, "El cuerpo de catch")
    elif name == "if":
        if len(analyses) < 2:
            raise ParseError("if requiere condición y cuerpo", command.span)
        index = 0
        expression(index, "La condición de if")
        index += 1
        if index < len(analyses) and _is_literal_word(analyses[index].word, "then"):
            index += 1
        if index >= len(analyses):
            raise ParseError("if requiere un cuerpo", command.span)
        script(index, "El cuerpo de if")
        index += 1
        while index < len(analyses):
            branch = _literal_word_text(analyses[index].word, "La rama de if")
            index += 1
            if branch == "elseif":
                if index >= len(analyses):
                    raise ParseError("elseif requiere condición y cuerpo", command.span)
                expression(index, "La condición de elseif")
                index += 1
                if index < len(analyses) and _is_literal_word(analyses[index].word, "then"):
                    index += 1
                if index >= len(analyses):
                    raise ParseError("elseif requiere un cuerpo", command.span)
                script(index, "El cuerpo de elseif")
                index += 1
            elif branch == "else":
                if index >= len(analyses):
                    raise ParseError("else requiere un cuerpo", command.span)
                script(index, "El cuerpo de else")
                index += 1
                if index != len(analyses):
                    raise ParseError("No puede haber argumentos después de else", command.span)
            else:
                raise ParseError(f"Rama desconocida de if: {branch}", analyses[index - 1].word.span)

    return CommandAnalysis(
        command=command,
        name=name,
        arguments=tuple(analyses))


# === Fachadas, diagnosticos (linea/columna) y bateria de pruebas ===

def read_substitution(text, opening_index, base_offset, source_name):
    depth = 1; i = opening_index + 1
    while i < len(text) and depth > 0:
        if text[i] == '[': depth += 1
        elif text[i] == ']': depth -= 1
        elif text[i] == '\\': i += 1
        i += 1
    if depth > 0:
        raise ParseError("Falta ']' en sustitucion", Span(opening_index, opening_index + 1, source_name))
    closing_index = i - 1
    inner_text = text[opening_index + 1 : closing_index]
    script = parse_minitcl(inner_text, base_offset=base_offset + opening_index + 1, source_name=source_name)
    return script, i

def _enrich(e, source, base_offset):
    off = e.span.start - base_offset
    if 0 <= off <= len(source):
        line = source.count('\n', 0, off) + 1
        bol = source.rfind('\n', 0, off) + 1
        col = off - bol + 1
        eol = source.find('\n', off)
        frag = source[bol: eol if eol != -1 else len(source)]
        msg = f"{e.message} (linea {line}, columna {col})\n    {frag}\n    {' '*(col-1)}^"
        return ParseError(msg, e.span)
    return e

def parse_minitcl(source: str, *, base_offset=0, source_name='<input>') -> Script:
    norm = source.replace('\r\n', '\n').replace('\r', '\n')
    try:
        tokens = ScriptLexer(source, base_offset, source_name).tokenize()
        return ScriptParser(tokens).parse()
    except ParseError as e:
        raise _enrich(e, norm, base_offset)

def parse_minitcl_expr(source: str, *, base_offset=0, source_name='<expr>') -> Expr:
    if not SLY_AVAILABLE:
        raise RuntimeError("SLY no esta instalado.")
    norm = source.replace('\r\n', '\n').replace('\r', '\n')
    try:
        lexer = ExprLexer(read_substitution=read_substitution, base_offset=base_offset, source_name=source_name)
        parser = ExprParser(text=source, base_offset=base_offset, source_name=source_name)
        result = parser.parse(lexer.tokenize(source))
        if result is None:
            raise ParseError("Expresion vacia o invalida", Span(base_offset, base_offset + len(source), source_name))
        return result
    except ParseError as e:
        raise _enrich(e, norm, base_offset)

def expr_shape(node):
    if isinstance(node, Constant): return node.value
    if isinstance(node, Unary):    return (node.operator, expr_shape(node.operand))
    if isinstance(node, Binary):   return (node.operator, expr_shape(node.left), expr_shape(node.right))
    if isinstance(node, VariableExpr):     return ("VAR", node.variable.name)
    if isinstance(node, SubstitutionExpr): return ("SUBST",)
    raise TypeError(type(node).__name__)
