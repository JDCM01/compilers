# -*- coding: utf-8 -*-
"""Parser descendente recursivo de scripts (sección 4)."""
from model import (Span, Token, ParseError, TokenCursor, cover,
                   Literal, Variable, CommandSubstitution,
                   Word, Command, Script, Part)

class ScriptParser(TokenCursor):
    WORD_START = {"TEXT", "VAR", "BRACED", "QOPEN", "LBRACKET"}

    def parse(self) -> Script:
        result = self.parse_script(stop="EOF")
        self.expect("EOF")
        return result

    def parse_script(self, stop="EOF") -> Script:
        start = self.current.span
        commands = []
        self.skip("WS", "SEP")
        while self.current.kind != stop:
            if self.current.kind == "EOF":
                raise ParseError(f"Falta {stop}", self.current.span)
            commands.append(self.parse_command())
            if self.current.kind == stop:
                break
            self.expect("SEP")
            self.skip("WS", "SEP")
        end = commands[-1].span if commands else self.current.span
        return Script(commands=tuple(commands), span=cover(start, end))

    def parse_command(self) -> Command:
        words = [self.parse_word()]
        while self.accept("WS"):
            if self.current.kind not in self.WORD_START:
                break
            words.append(self.parse_word())
        return Command(words=tuple(words), span=cover(words[0].span, words[-1].span))

    def parse_word(self) -> Word:
        if self.current.kind == "BRACED":
            return self.parse_braced_word()
        if self.current.kind == "QOPEN":
            return self.parse_quoted_word()
        if self.current.kind in {"TEXT", "VAR", "LBRACKET"}:
            return self.parse_bare_word()
        raise ParseError(
            f"Se esperaba una palabra; se encontró {self.current.kind}",
            self.current.span)

    def parse_bare_word(self) -> Word:
        parts = [self.parse_part()]
        while self.current.kind in {"TEXT", "VAR", "LBRACKET"}:
            parts.append(self.parse_part())
        return Word(
            parts=tuple(parts),
            mode="bare",
            span=cover(parts[0].span, parts[-1].span))

    def parse_quoted_word(self) -> Word:
        opening = self.expect("QOPEN")
        parts = []
        while self.current.kind in {"TEXT", "VAR", "LBRACKET"}:
            parts.append(self.parse_part())
        closing = self.expect("QCLOSE")
        return Word(
            parts=tuple(parts),
            mode="quoted",
            span=cover(opening.span, closing.span))

    def parse_braced_word(self) -> Word:
        token = self.expect("BRACED")
        part = Literal(text=token.value, span=token.span)
        return Word(parts=(part,), mode="braced", span=token.span)

    def parse_part(self) -> Part:
        if self.current.kind == "TEXT":
            token = self.expect("TEXT")
            return Literal(text=token.value, span=token.span)
        if self.current.kind == "VAR":
            token = self.expect("VAR")
            return Variable(name=token.value, index=token.index, span=token.span)
        if self.current.kind == "LBRACKET":
            return self.parse_substitution()
        raise ParseError(
            f"Se esperaba una parte de palabra; se encontró {self.current.kind}",
            self.current.span)

    def parse_substitution(self) -> CommandSubstitution:
        opening = self.expect("LBRACKET")
        script = self.parse_script(stop="RBRACKET")
        closing = self.expect("RBRACKET")
        return CommandSubstitution(
            script=script,
            span=cover(opening.span, closing.span))
