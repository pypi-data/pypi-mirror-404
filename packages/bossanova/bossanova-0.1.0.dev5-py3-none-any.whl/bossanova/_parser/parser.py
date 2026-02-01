"""Recursive descent parser for formula strings.

Vendored from formulae library (https://github.com/bambinos/formulae).
"""

from __future__ import annotations

from .expr import Assign, Binary, Call, Grouping, Literal, QuotedName, Unary, Variable
from .token import Token


class ParseError(Exception):
    """Error raised during formula parsing."""

    pass


def _listify(obj: str | list[str] | None) -> list[str]:
    """Wrap non-list objects in a list."""
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    return [obj]


class Parser:
    """Parse a sequence of Tokens and return an abstract syntax tree.

    Args:
        tokens: A list of Token objects as returned by Scanner.scan().
        formula: The original formula string (for error messages).
    """

    def __init__(self, tokens: list[Token], formula: str = "") -> None:
        self.current = 0
        self.tokens = tokens
        self.formula = formula

    def _format_error_context(self, position: int, message: str) -> str:
        """Format a parse error with visual pointer to the error location.

        Args:
            position: Character offset where error occurred.
            message: The error description.

        Returns:
            Formatted error message with context and pointer.
        """
        if not self.formula:
            return message
        # Clamp position to valid range
        position = max(0, min(position, len(self.formula)))
        pointer = " " * position + "^"
        return f"{message}\n\n  {self.formula}\n  {pointer}"

    def at_end(self) -> bool:
        return self.peek().kind == "EOF"

    def advance(self) -> Token | None:
        if not self.at_end():
            self.current += 1
            return self.tokens[self.current - 1]
        return None

    def peek(self) -> Token:
        """Return the Token we are about to consume."""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Return the last Token we consumed."""
        return self.tokens[self.current - 1]

    def check(self, types: str | list[str]) -> bool:
        """Check if current token matches any of the given types."""
        if self.at_end():
            return False
        return self.peek().kind in _listify(types)

    def match(self, types: str | list[str]) -> bool:
        """Match and consume token if it matches any of the given types."""
        if self.check(types):
            self.advance()
            return True
        return False

    def consume(self, kind: str, message: str) -> Token:
        """Consume the next Token, raising ParseError if it doesn't match.

        Args:
            kind: Expected token kind.
            message: Error message if token doesn't match.

        Returns:
            The consumed token.

        Raises:
            ParseError: If the next token doesn't match the expected kind.
        """
        if self.check(kind):
            token = self.advance()
            assert token is not None  # check() ensures we're not at EOF
            return token
        token = self.peek()
        raise ParseError(self._format_error_context(token.position, message))

    def parse(self) -> object:
        """Parse a sequence of Tokens.

        Returns:
            An AST expression node representing the parsed formula.

        Raises:
            ParseError: If there are unconsumed tokens after parsing.
        """
        expr = self.expression()

        # Check for unconsumed tokens (other than EOF)
        if not self.at_end():
            token = self.peek()
            raise ParseError(
                self._format_error_context(
                    token.position,
                    f"Unexpected token '{token.lexeme}' after expression.",
                )
                + "\n\nCheck for extra characters or mismatched parentheses."
            )

        return expr

    def expression(self) -> object:
        return self.assignment()

    def assignment(self) -> object:
        expr = self.tilde()
        if self.match("EQUAL"):
            equals_token = self.previous()
            right = self.addition()
            if isinstance(expr, Variable):
                return Assign(expr, right)
            raise ParseError(
                self._format_error_context(
                    equals_token.position,
                    "Invalid assignment target.",
                )
                + "\n\nAssignment (=) can only be used with variable names.\n"
                "Example: 'y ~ center(x, ref=0)'"
            )
        return expr

    def tilde(self) -> object:
        expr = self.random_effect()
        if self.match("TILDE"):
            operator = self.previous()
            right = self.addition()
            expr = Binary(expr, operator, right)
        return expr

    def random_effect(self) -> object:
        expr = self.comparison()
        while self.match("PIPE"):
            operator = self.previous()
            right = self.comparison()
            expr = Binary(expr, operator, right)
        return expr

    def comparison(self) -> object:
        expr = self.addition()
        while self.match(
            [
                "EQUAL_EQUAL",
                "BANG_EQUAL",
                "LESS_EQUAL",
                "LESS",
                "GREATER_EQUAL",
                "GREATER",
            ]
        ):
            operator = self.previous()
            right = self.addition()
            expr = Binary(expr, operator, right)
        return expr

    def addition(self) -> object:
        expr = self.multiplication()
        while self.match(["MINUS", "PLUS"]):
            operator = self.previous()
            right = self.multiplication()
            expr = Binary(expr, operator, right)
        return expr

    def multiplication(self) -> object:
        expr = self.interaction()
        while self.match(["STAR", "SLASH"]):
            operator = self.previous()
            right = self.interaction()
            expr = Binary(expr, operator, right)
        return expr

    def interaction(self) -> object:
        expr = self.multiple_interaction()
        while self.match("COLON"):
            operator = self.previous()
            right = self.multiple_interaction()
            expr = Binary(expr, operator, right)
        return expr

    def multiple_interaction(self) -> object:
        expr = self.unary()
        while self.match("STAR_STAR"):
            operator = self.previous()
            right = self.unary()
            expr = Binary(expr, operator, right)
        return expr

    def unary(self) -> object:
        if self.match(["PLUS", "MINUS"]):
            operator = self.previous()
            right = self.unary()
            return Unary(operator, right)
        return self.call()

    def call(self) -> object:
        expr = self.primary()
        while True:
            if self.match("LEFT_PAREN"):
                expr = self._finish_call(expr)
            else:
                break
        return expr

    def _finish_call(self, expr: object) -> Call:
        args = []
        if not self.check("RIGHT_PAREN"):
            while True:
                args.append(self.expression())
                if not self.match("COMMA"):
                    break
        self.consume("RIGHT_PAREN", "Missing ')' after function arguments.")
        return Call(expr, args)

    def primary(self) -> object:
        if self.match("IDENTIFIER"):
            identifier = self.previous()
            if self.match("LEFT_BRACKET"):
                bracket_token = self.previous()
                level_expr = self.primary()
                level: Literal
                if isinstance(level_expr, Literal):
                    if not isinstance(level_expr.value, str):
                        raise ParseError(
                            self._format_error_context(
                                bracket_token.position,
                                "Subset notation requires a string or identifier.",
                            )
                            + "\n\nExample: 'group[\"level_a\"]' or 'group[level_a]'"
                        )
                    level = level_expr
                elif isinstance(level_expr, Variable):
                    if level_expr.level is not None:
                        raise ParseError(
                            self._format_error_context(
                                bracket_token.position,
                                "Nested brackets are not supported.",
                            )
                            + "\n\nUse a single bracket: 'group[\"level\"]'"
                        )
                    level = Literal(level_expr.name.lexeme)
                else:
                    raise ParseError(
                        self._format_error_context(
                            bracket_token.position,
                            "Subset notation requires a string or identifier.",
                        )
                        + "\n\nExample: 'group[\"level_a\"]' or 'group[level_a]'"
                    )

                self.consume("RIGHT_BRACKET", "Expected ']' to close bracket notation.")
                return Variable(identifier, level)
            return Variable(self.previous())

        if self.match("NUMBER"):
            return Literal(self.previous().literal)

        if self.match("STRING"):
            token = self.previous()
            return Literal(token.literal, lexeme=token.lexeme)

        if self.match("BQNAME"):
            return QuotedName(self.previous())

        if self.match("PYTHON_LITERAL"):
            return Literal(self.previous().literal)

        if self.match("LEFT_PAREN"):
            paren_token = self.previous()
            expr = self.expression()
            self.consume(
                "RIGHT_PAREN",
                f"Missing ')' to close parenthesis opened at position {paren_token.position}.",
            )
            return Grouping(expr)

        if self.match("LEFT_BRACE"):
            # {x + 1} is translated to I(x + 1) and then we resolve the latter
            brace_token = self.previous()
            expr = self.expression()
            self.consume(
                "RIGHT_BRACE",
                f"Missing '}}' to close brace opened at position {brace_token.position}.",
            )
            return Call(Variable(Token("IDENTIFIER", "I")), [expr])

        token = self.peek()
        raise ParseError(
            self._format_error_context(
                token.position,
                f"Unexpected '{token.lexeme}' in formula.",
            )
            + "\n\nExpected a variable name, number, or expression."
        )
