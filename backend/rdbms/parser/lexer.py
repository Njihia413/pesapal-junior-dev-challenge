"""
PesapalDB SQL Lexer

Tokenizes SQL strings into a stream of tokens.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    """SQL token types."""

    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    SELECT = auto()
    FROM = auto()
    WHERE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    BETWEEN = auto()
    LIKE = auto()
    IS = auto()
    NULL = auto()
    TRUE = auto()
    FALSE = auto()
    AS = auto()
    ON = auto()
    JOIN = auto()
    LEFT = auto()
    RIGHT = auto()
    INNER = auto()
    OUTER = auto()
    FULL = auto()
    CROSS = auto()
    ORDER = auto()
    BY = auto()
    ASC = auto()
    DESC = auto()
    LIMIT = auto()
    OFFSET = auto()
    GROUP = auto()
    HAVING = auto()
    DISTINCT = auto()

    # DML
    INSERT = auto()
    INTO = auto()
    VALUES = auto()
    UPDATE = auto()
    SET = auto()
    DELETE = auto()

    # DDL
    CREATE = auto()
    DROP = auto()
    ALTER = auto()
    TABLE = auto()
    INDEX = auto()
    DATABASE = auto()

    # Constraints
    PRIMARY = auto()
    KEY = auto()
    FOREIGN = auto()
    REFERENCES = auto()
    UNIQUE = auto()
    DEFAULT = auto()
    AUTO_INCREMENT = auto()

    # Types
    INT = auto()
    INTEGER_TYPE = auto()
    FLOAT_TYPE = auto()
    VARCHAR = auto()
    BOOLEAN = auto()
    DATE = auto()
    TIMESTAMP = auto()

    # Operators
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    LESS_THAN_EQUALS = auto()
    GREATER_THAN = auto()
    GREATER_THAN_EQUALS = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    MODULO = auto()

    # Punctuation
    COMMA = auto()
    SEMICOLON = auto()
    LPAREN = auto()
    RPAREN = auto()
    DOT = auto()
    STAR = auto()

    # Special
    EOF = auto()
    NEWLINE = auto()


# Keyword mapping
KEYWORDS = {
    "SELECT": TokenType.SELECT,
    "FROM": TokenType.FROM,
    "WHERE": TokenType.WHERE,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "NOT": TokenType.NOT,
    "IN": TokenType.IN,
    "BETWEEN": TokenType.BETWEEN,
    "LIKE": TokenType.LIKE,
    "IS": TokenType.IS,
    "NULL": TokenType.NULL,
    "TRUE": TokenType.TRUE,
    "FALSE": TokenType.FALSE,
    "AS": TokenType.AS,
    "ON": TokenType.ON,
    "JOIN": TokenType.JOIN,
    "LEFT": TokenType.LEFT,
    "RIGHT": TokenType.RIGHT,
    "INNER": TokenType.INNER,
    "OUTER": TokenType.OUTER,
    "FULL": TokenType.FULL,
    "CROSS": TokenType.CROSS,
    "ORDER": TokenType.ORDER,
    "BY": TokenType.BY,
    "ASC": TokenType.ASC,
    "DESC": TokenType.DESC,
    "LIMIT": TokenType.LIMIT,
    "OFFSET": TokenType.OFFSET,
    "GROUP": TokenType.GROUP,
    "HAVING": TokenType.HAVING,
    "DISTINCT": TokenType.DISTINCT,
    "INSERT": TokenType.INSERT,
    "INTO": TokenType.INTO,
    "VALUES": TokenType.VALUES,
    "UPDATE": TokenType.UPDATE,
    "SET": TokenType.SET,
    "DELETE": TokenType.DELETE,
    "CREATE": TokenType.CREATE,
    "DROP": TokenType.DROP,
    "ALTER": TokenType.ALTER,
    "TABLE": TokenType.TABLE,
    "INDEX": TokenType.INDEX,
    "DATABASE": TokenType.DATABASE,
    "PRIMARY": TokenType.PRIMARY,
    "KEY": TokenType.KEY,
    "FOREIGN": TokenType.FOREIGN,
    "REFERENCES": TokenType.REFERENCES,
    "UNIQUE": TokenType.UNIQUE,
    "DEFAULT": TokenType.DEFAULT,
    "AUTO_INCREMENT": TokenType.AUTO_INCREMENT,
    "AUTOINCREMENT": TokenType.AUTO_INCREMENT,
    "INT": TokenType.INT,
    "INTEGER": TokenType.INTEGER_TYPE,
    "FLOAT": TokenType.FLOAT_TYPE,
    "DOUBLE": TokenType.FLOAT_TYPE,
    "REAL": TokenType.FLOAT_TYPE,
    "VARCHAR": TokenType.VARCHAR,
    "CHAR": TokenType.VARCHAR,
    "TEXT": TokenType.VARCHAR,
    "BOOLEAN": TokenType.BOOLEAN,
    "BOOL": TokenType.BOOLEAN,
    "DATE": TokenType.DATE,
    "TIMESTAMP": TokenType.TIMESTAMP,
    "DATETIME": TokenType.TIMESTAMP,
}


@dataclass
class Token:
    """Represents a single token."""

    type: TokenType
    value: any
    line: int
    column: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r})"


class Lexer:
    """SQL Lexer - tokenizes SQL strings."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    @property
    def current_char(self) -> Optional[str]:
        """Get current character or None if at end."""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def peek(self, offset: int = 1) -> Optional[str]:
        """Peek at character at offset from current position."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]

    def advance(self) -> str:
        """Advance to next character and return current."""
        char = self.current_char
        self.pos += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.current_char and self.current_char.isspace():
            self.advance()

    def skip_comment(self) -> None:
        """Skip SQL comments."""
        if self.current_char == "-" and self.peek() == "-":
            # Single line comment
            while self.current_char and self.current_char != "\n":
                self.advance()
        elif self.current_char == "/" and self.peek() == "*":
            # Multi-line comment
            self.advance()  # /
            self.advance()  # *
            while self.current_char:
                if self.current_char == "*" and self.peek() == "/":
                    self.advance()  # *
                    self.advance()  # /
                    break
                self.advance()

    def read_string(self) -> Token:
        """Read a string literal."""
        quote = self.advance()  # Opening quote
        start_line, start_col = self.line, self.column
        value = ""

        while self.current_char and self.current_char != quote:
            if self.current_char == "\\" and self.peek() == quote:
                self.advance()
            value += self.advance()

        if self.current_char == quote:
            self.advance()  # Closing quote

        return Token(TokenType.STRING, value, start_line, start_col)

    def read_number(self) -> Token:
        """Read a numeric literal."""
        start_line, start_col = self.line, self.column
        value = ""
        is_float = False

        while self.current_char and (
            self.current_char.isdigit() or self.current_char == "."
        ):
            if self.current_char == ".":
                if is_float:
                    break
                is_float = True
            value += self.advance()

        if is_float:
            return Token(TokenType.FLOAT, float(value), start_line, start_col)
        return Token(TokenType.INTEGER, int(value), start_line, start_col)

    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        start_line, start_col = self.line, self.column
        value = ""

        while self.current_char and (
            self.current_char.isalnum() or self.current_char == "_"
        ):
            value += self.advance()

        # Check if it's a keyword
        upper = value.upper()
        if upper in KEYWORDS:
            return Token(KEYWORDS[upper], value.upper(), start_line, start_col)

        return Token(TokenType.IDENTIFIER, value, start_line, start_col)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire input."""
        while self.current_char:
            self.skip_whitespace()

            if not self.current_char:
                break

            # Comments
            if self.current_char == "-" and self.peek() == "-":
                self.skip_comment()
                continue
            if self.current_char == "/" and self.peek() == "*":
                self.skip_comment()
                continue

            start_line, start_col = self.line, self.column

            # String literals
            if self.current_char in ('"', "'"):
                self.tokens.append(self.read_string())
                continue

            # Numbers
            if self.current_char.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == "_":
                self.tokens.append(self.read_identifier())
                continue

            # Operators and punctuation
            char = self.current_char

            if char == "=" and self.peek() == "=":
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.EQUALS, "==", start_line, start_col))
            elif char == "=":
                self.advance()
                self.tokens.append(Token(TokenType.EQUALS, "=", start_line, start_col))
            elif char == "!" and self.peek() == "=":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.NOT_EQUALS, "!=", start_line, start_col)
                )
            elif char == "<" and self.peek() == ">":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.NOT_EQUALS, "<>", start_line, start_col)
                )
            elif char == "<" and self.peek() == "=":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.LESS_THAN_EQUALS, "<=", start_line, start_col)
                )
            elif char == "<":
                self.advance()
                self.tokens.append(
                    Token(TokenType.LESS_THAN, "<", start_line, start_col)
                )
            elif char == ">" and self.peek() == "=":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.GREATER_THAN_EQUALS, ">=", start_line, start_col)
                )
            elif char == ">":
                self.advance()
                self.tokens.append(
                    Token(TokenType.GREATER_THAN, ">", start_line, start_col)
                )
            elif char == "+":
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, "+", start_line, start_col))
            elif char == "-":
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, "-", start_line, start_col))
            elif char == "*":
                self.advance()
                self.tokens.append(Token(TokenType.STAR, "*", start_line, start_col))
            elif char == "/":
                self.advance()
                self.tokens.append(Token(TokenType.DIVIDE, "/", start_line, start_col))
            elif char == "%":
                self.advance()
                self.tokens.append(Token(TokenType.MODULO, "%", start_line, start_col))
            elif char == ",":
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif char == ";":
                self.advance()
                self.tokens.append(
                    Token(TokenType.SEMICOLON, ";", start_line, start_col)
                )
            elif char == "(":
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif char == ")":
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif char == ".":
                self.advance()
                self.tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
            else:
                # Unknown character, skip
                self.advance()

        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens
