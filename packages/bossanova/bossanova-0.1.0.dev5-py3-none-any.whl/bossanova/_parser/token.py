"""Token class for formula parsing.

Vendored from formulae library (https://github.com/bambinos/formulae).
"""

from __future__ import annotations


class Token:
    """Representation of a single Token.

    Attributes:
        kind: Token type (e.g., "IDENTIFIER", "PLUS", "TILDE").
        lexeme: The actual string from the source.
        literal: Parsed literal value (for numbers, strings).
        position: Character offset in the original formula string.
    """

    def __init__(
        self, kind: str, lexeme: str, literal: object = None, position: int = 0
    ) -> None:
        self.kind = kind
        self.lexeme = lexeme
        self.literal = literal
        self.position = position

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Token):
            return NotImplemented
        return (
            self.kind == other.kind
            and self.lexeme == other.lexeme
            and self.literal == other.literal
            # Note: position intentionally excluded from equality
        )

    def __repr__(self) -> str:
        return (
            f"Token(kind={self.kind!r}, lexeme={self.lexeme!r}, "
            f"literal={self.literal!r}, position={self.position})"
        )

    def __str__(self) -> str:
        return (
            f"Token(kind={self.kind}, lexeme={self.lexeme}, position={self.position})"
        )
