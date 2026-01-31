"""Formula parsing infrastructure.

This module provides a recursive descent parser for statistical formula strings
(e.g., "y ~ x1 + x2 * group"). It is vendored from the formulae library.

Public API:
    Scanner: Tokenize formula strings into Token objects.
    Parser: Parse Token sequences into AST nodes.
    ScanError: Raised when scanning fails.
    ParseError: Raised when parsing fails.

AST Node Types:
    Variable: Variable reference (e.g., "x")
    Literal: Literal value (numbers, strings)
    Binary: Binary operation (e.g., "x + y", "x ~ y")
    Unary: Unary operation (e.g., "-x")
    Call: Function call (e.g., "factor(x)", "center(y)")
    Grouping: Parenthesized expression
    QuotedName: Back-quoted name (e.g., "`weird name`")
    Assign: Assignment expression (e.g., "reference='A'")
    Token: Single token from scanner.

Examples:
    >>> from bossanova._parser import Scanner, Parser
    >>> tokens = Scanner("y ~ x1 + x2").scan()
    >>> ast = Parser(tokens).parse()
    >>> ast
    Binary(left=Literal(value=1), op='~', right=...)
"""

from .expr import Assign, Binary, Call, Grouping, Literal, QuotedName, Unary, Variable
from .parser import ParseError, Parser
from .scanner import ScanError, Scanner
from .token import Token

__all__ = [
    # Scanner/Parser
    "Scanner",
    "Parser",
    "ScanError",
    "ParseError",
    # Token
    "Token",
    # AST Nodes
    "Assign",
    "Binary",
    "Call",
    "Grouping",
    "Literal",
    "QuotedName",
    "Unary",
    "Variable",
]
