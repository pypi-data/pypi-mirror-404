"""Formula string scanner/tokenizer.

Vendored from formulae library (https://github.com/bambinos/formulae).
"""

from __future__ import annotations

from .token import Token


class ScanError(Exception):
    """Error raised during formula scanning."""

    pass


def _format_error_context(formula: str, position: int, message: str) -> str:
    """Format a scan error with visual pointer to the error location.

    Args:
        formula: The original formula string.
        position: Character offset where error occurred.
        message: The error description.

    Returns:
        Formatted error message with context and pointer.
    """
    # Clamp position to valid range
    position = max(0, min(position, len(formula)))
    pointer = " " * position + "^"
    return f"{message}\n\n  {formula}\n  {pointer}"


class Scanner:
    """Scan formula string and return Tokens.

    Args:
        code: The formula string to scan.

    Raises:
        ScanError: If the code is empty or contains unexpected characters.
    """

    def __init__(self, code: str) -> None:
        self.code = code
        self.start = 0
        self.current = 0
        self.tokens: list[Token] = []

        if not len(self.code):
            raise ScanError("'code' is a string of length 0.")
        if not self.code.strip():
            raise ScanError("Formula cannot be whitespace-only.")

    def at_end(self) -> bool:
        return self.current >= len(self.code)

    def advance(self) -> str:
        self.current += 1
        return self.code[self.current - 1]

    def peek(self) -> str:
        if self.at_end():
            return ""
        return self.code[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.code):
            return ""
        return self.code[self.current + 1]

    def match(self, expected: str) -> bool:
        if self.at_end():
            return False
        if self.code[self.current] != expected:
            return False
        self.current += 1
        return True

    def add_token(self, kind: str, literal: object = None) -> None:
        source = self.code[self.start : self.current]
        self.tokens.append(Token(kind, source, literal, position=self.start))

    def scan_token(self) -> None:
        char = self.advance()
        if char in ["'", '"']:
            self._char()
        elif char == "(":
            self.add_token("LEFT_PAREN")
        elif char == ")":
            self.add_token("RIGHT_PAREN")
        elif char == "[":
            self.add_token("LEFT_BRACKET")
        elif char == "]":
            self.add_token("RIGHT_BRACKET")
        elif char == "{":
            self.add_token("LEFT_BRACE")
        elif char == "}":
            self.add_token("RIGHT_BRACE")
        elif char == "`":
            self._backquote()
        elif char == ",":
            self.add_token("COMMA")
        elif char == ".":
            if self.peek().isdigit():
                self._floatnum()
            else:
                self.add_token("PERIOD")
        elif char == "+":
            self.add_token("PLUS")
        elif char == "-":
            self.add_token("MINUS")
        elif char == "/":
            if self.match("/"):
                self.add_token("SLASH_SLASH")
            else:
                self.add_token("SLASH")
        elif char == "*":
            if self.match("*"):
                self.add_token("STAR_STAR")
            else:
                self.add_token("STAR")
        elif char == "!":
            if self.match("="):
                self.add_token("BANG_EQUAL")
            else:
                self.add_token("BANG")
        elif char == "=":
            if self.match("="):
                self.add_token("EQUAL_EQUAL")
            else:
                self.add_token("EQUAL")
        elif char == "<":
            if self.match("="):
                self.add_token("LESS_EQUAL")
            else:
                self.add_token("LESS")
        elif char == ">":
            if self.match("="):
                self.add_token("GREATER_EQUAL")
            else:
                self.add_token("GREATER")
        elif char == "%":
            self.add_token("MODULO")
        elif char == "~":
            self.add_token("TILDE")
        elif char == ":":
            self.add_token("COLON")
        elif char == "|":
            self.add_token("PIPE")
        elif char in [" ", "\n", "\t", "\r"]:
            pass  # Skip whitespace
        elif char.isdigit():
            self._number()
        elif char.isalpha():
            self._identifier()
        else:
            raise ScanError(
                _format_error_context(
                    self.code,
                    self.current - 1,
                    f"Unexpected character '{char}' in formula.",
                )
                + "\n\nValid characters: letters, numbers, ~, +, -, *, :, |, (, ), [, ]"
            )

    def scan(self, add_intercept: bool = True) -> list[Token]:
        """Scan formula string.

        Args:
            add_intercept: Whether to add an implicit intercept. Defaults to True.

        Returns:
            A list of Token objects.

        Raises:
            ScanError: If there is more than one '~' in the formula.
        """
        while not self.at_end():
            self.start = self.current
            self.scan_token()
        self.tokens.append(Token("EOF", "", position=len(self.code)))

        # Check number of '~' and add implicit intercept
        tilde_idx = [i for i, t in enumerate(self.tokens) if t.kind == "TILDE"]

        if len(tilde_idx) > 1:
            # Find position of second tilde for error pointer
            second_tilde_pos = self.tokens[tilde_idx[1]].position
            raise ScanError(
                _format_error_context(
                    self.code,
                    second_tilde_pos,
                    "Multiple '~' symbols found in formula.",
                )
                + "\n\nA formula should have exactly one '~' separating "
                "the response (left) from predictors (right).\n"
                "Example: 'y ~ x1 + x2'"
            )

        if add_intercept:
            if len(tilde_idx) == 0:
                # No tilde - prepend implicit intercept at position 0
                self.tokens = [
                    Token("NUMBER", "1", 1, position=0),
                    Token("PLUS", "+", position=0),
                ] + self.tokens
            if len(tilde_idx) == 1:
                # Insert implicit intercept after tilde
                tilde_pos = self.tokens[tilde_idx[0]].position + 1
                self.tokens.insert(
                    tilde_idx[0] + 1, Token("NUMBER", "1", 1, position=tilde_pos)
                )
                self.tokens.insert(
                    tilde_idx[0] + 2, Token("PLUS", "+", position=tilde_pos)
                )

        return self.tokens

    def _floatnum(self) -> None:
        while self.peek().isdigit():
            self.advance()
        self.add_token("NUMBER", float(self.code[self.start : self.current]))

    def _number(self) -> None:
        is_float = False
        while self.peek().isdigit():
            self.advance()
        # Look for fractional part, if present
        if self.peek() == "." and self.peek_next().isdigit():
            is_float = True
            # Consume the dot
            self.advance()
            # Keep consuming numbers, if present
            while self.peek().isdigit():
                self.advance()
        if is_float:
            token = float(self.code[self.start : self.current])
        else:
            token = int(self.code[self.start : self.current])

        self.add_token("NUMBER", token)

    def _identifier(self) -> None:
        # 'mod.function' is also an identifier
        while self.peek().isalnum() or self.peek() in [".", "_"]:
            self.advance()

        token = self.code[self.start : self.current]
        if token in ("True", "False", "None"):
            # These are actually literals, not variable names
            # Use literal_eval for safety instead of eval
            literal_map = {"True": True, "False": False, "None": None}
            self.add_token("PYTHON_LITERAL", literal_map[token])
        else:
            self.add_token("IDENTIFIER")

    def _char(self) -> None:
        while self.peek() not in ["'", '"'] and not self.at_end():
            self.advance()

        if self.at_end():
            raise ScanError(
                _format_error_context(
                    self.code,
                    self.start,
                    "Unterminated string.",
                )
                + "\n\nStrings must be closed with a matching quote (' or \")."
            )

        # The closing quotation mark
        self.advance()

        # Trim the surrounding quotes
        value = self.code[self.start + 1 : self.current - 1]
        self.add_token("STRING", value)

    def _backquote(self) -> None:
        while True:
            if self.peek() == "`":
                break
            if self.at_end():
                raise ScanError(
                    _format_error_context(
                        self.code,
                        self.start,
                        "Unterminated backtick-quoted name.",
                    )
                    + "\n\nBacktick-quoted names must be closed with a matching backtick (`)."
                )
            self.advance()
        self.advance()
        # Strip the surrounding backticks from the lexeme
        name = self.code[self.start + 1 : self.current - 1]
        self.tokens.append(Token("BQNAME", name, position=self.start))
