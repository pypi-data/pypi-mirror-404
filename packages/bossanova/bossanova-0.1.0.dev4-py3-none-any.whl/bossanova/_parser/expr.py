"""AST expression node types for formula parsing.

Vendored from formulae library (https://github.com/bambinos/formulae).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .token import Token


class Assign:
    """Expression for assignments (e.g., x=value in function calls)."""

    def __init__(self, name: Variable, value: object) -> None:
        self.name = name
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Assign):
            return NotImplemented
        return self.name == other.name and self.value == other.value

    def __repr__(self) -> str:
        return f"Assign(name={self.name}, value={self.value})"


class Grouping:
    """Expression for parenthesized groups."""

    def __init__(self, expression: object) -> None:
        self.expression = expression

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grouping):
            return NotImplemented
        return self.expression == other.expression

    def __repr__(self) -> str:
        return f"Grouping({self.expression})"


class Binary:
    """Expression for binary operations (e.g., x + y, x ~ y)."""

    def __init__(self, left: object, operator: Token, right: object) -> None:
        self.left = left
        self.operator = operator
        self.right = right

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Binary):
            return NotImplemented
        return (
            self.left == other.left
            and self.operator == other.operator
            and self.right == other.right
        )

    def __repr__(self) -> str:
        return (
            f"Binary(left={self.left}, op={self.operator.lexeme!r}, right={self.right})"
        )


class Unary:
    """Expression for unary operations (e.g., -x, +x)."""

    def __init__(self, operator: Token, right: object) -> None:
        self.operator = operator
        self.right = right

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Unary):
            return NotImplemented
        return self.operator == other.operator and self.right == other.right

    def __repr__(self) -> str:
        return f"Unary(op={self.operator.lexeme!r}, right={self.right})"


class Call:
    """Expression for function calls (e.g., factor(x), center(y))."""

    def __init__(self, callee: object, args: list) -> None:
        self.callee = callee
        self.args = args

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Call):
            return NotImplemented
        return self.callee == other.callee and self.args == other.args

    def __repr__(self) -> str:
        return f"Call(callee={self.callee}, args={self.args})"


class Variable:
    """Expression for variable references."""

    def __init__(self, name: Token, level: Literal | None = None) -> None:
        self.name = name
        self.level = level

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Variable):
            return NotImplemented
        return self.name == other.name and self.level == other.level

    def __repr__(self) -> str:
        if self.level is not None:
            return f"Variable(name={self.name.lexeme!r}, level={self.level.value!r})"
        return f"Variable(name={self.name.lexeme!r})"


class QuotedName:
    """Expression for back-quoted names (e.g., `weird column name!`)."""

    def __init__(self, expression: Token) -> None:
        self.expression = expression

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QuotedName):
            return NotImplemented
        return self.expression == other.expression

    def __repr__(self) -> str:
        return f"QuotedName({self.expression.lexeme!r})"


class Literal:
    """Expression for literal values (numbers, strings, etc.)."""

    def __init__(self, value: object, lexeme: str | None = None) -> None:
        self.value = value
        self.lexeme = lexeme

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Literal):
            return NotImplemented
        return self.value == other.value and self.lexeme == other.lexeme

    def __repr__(self) -> str:
        if self.lexeme is not None:
            return f"Literal(value={self.value!r}, lexeme={self.lexeme!r})"
        return f"Literal(value={self.value!r})"
