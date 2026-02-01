"""
LUXBIN Lexer

Tokenizes LUXBIN source code into wavelength-based tokens.

Each token carries:
- Type (keyword, identifier, number, operator, etc.)
- Value (the actual text)
- Wavelength (the photonic encoding)
- Location (line and column for error reporting)
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Generator
from .errors import LexerError, SourceLocation


class TokenType(Enum):
    """Token types for LUXBIN language."""
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()
    BOOLEAN = auto()
    NIL = auto()

    # Identifiers and Keywords
    IDENTIFIER = auto()
    KEYWORD = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()
    EQ = auto()
    NE = auto()
    LT = auto()
    GT = auto()
    LE = auto()
    GE = auto()
    ASSIGN = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    DOT = auto()

    # Special
    NEWLINE = auto()
    COMMENT = auto()
    EOF = auto()


# LUXBIN wavelength mappings (from spec)
CHAR_WAVELENGTHS = {
    # Alphabet A-Z (400-497.4nm)
    'A': 400.0, 'B': 403.9, 'C': 407.8, 'D': 411.7, 'E': 415.6,
    'F': 419.5, 'G': 423.4, 'H': 427.3, 'I': 431.2, 'J': 435.1,
    'K': 439.0, 'L': 442.9, 'M': 446.8, 'N': 450.6, 'O': 454.5,
    'P': 458.4, 'Q': 462.3, 'R': 466.2, 'S': 470.1, 'T': 474.0,
    'U': 477.9, 'V': 481.8, 'W': 485.7, 'X': 489.6, 'Y': 493.5,
    'Z': 497.4,
    # Lowercase same as uppercase
    'a': 400.0, 'b': 403.9, 'c': 407.8, 'd': 411.7, 'e': 415.6,
    'f': 419.5, 'g': 423.4, 'h': 427.3, 'i': 431.2, 'j': 435.1,
    'k': 439.0, 'l': 442.9, 'm': 446.8, 'n': 450.6, 'o': 454.5,
    'p': 458.4, 'q': 462.3, 'r': 466.2, 's': 470.1, 't': 474.0,
    'u': 477.9, 'v': 481.8, 'w': 485.7, 'x': 489.6, 'y': 493.5,
    'z': 497.4,
    # Numbers 0-9 (501.3-536.4nm)
    '0': 501.3, '1': 505.2, '2': 509.1, '3': 513.0, '4': 516.9,
    '5': 520.8, '6': 524.7, '7': 528.6, '8': 532.5, '9': 536.4,
    # Punctuation and special characters
    ' ': 540.3, '.': 544.2, ',': 548.1, '!': 552.0, '?': 555.8,
    ';': 559.7, ':': 563.6, '-': 567.5, '(': 571.4, ')': 575.3,
    '[': 579.2, ']': 583.1, '{': 587.0, '}': 590.9, '@': 594.8,
    '#': 598.7, '$': 602.6, '%': 606.5, '^': 610.4, '&': 614.3,
    '*': 618.2, '+': 622.1, '=': 626.0, '_': 629.9, '~': 633.8,
    '`': 637.7, '<': 641.6, '>': 645.5, '"': 649.4, "'": 653.2,
    '|': 657.1, '\\': 661.0, '/': 664.9, '\n': 668.8,
}

# Keyword wavelengths (670-700nm reserved range)
KEYWORD_WAVELENGTHS = {
    'let': 670.0, 'const': 671.0, 'func': 672.0, 'return': 673.0,
    'if': 674.0, 'then': 675.0, 'else': 676.0, 'end': 677.0,
    'while': 678.0, 'for': 679.0, 'in': 680.0, 'do': 681.0,
    'break': 682.0, 'continue': 683.0, 'true': 684.0, 'false': 685.0,
    'nil': 686.0, 'and': 687.0, 'or': 688.0, 'not': 689.0,
    'import': 690.0, 'export': 691.0, 'quantum': 692.0, 'measure': 693.0,
    'superpose': 694.0, 'entangle': 695.0,
}

KEYWORDS = set(KEYWORD_WAVELENGTHS.keys())


@dataclass
class Token:
    """A token in the LUXBIN language."""
    type: TokenType
    value: str
    wavelength: float
    location: SourceLocation

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.wavelength}nm, {self.location})"


class Lexer:
    """
    LUXBIN Lexer - Tokenizes source code into wavelength-based tokens.
    """

    def __init__(self, source: str, filename: Optional[str] = None):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    @property
    def current_char(self) -> Optional[str]:
        """Get current character or None if at end."""
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def peek(self, offset: int = 1) -> Optional[str]:
        """Peek ahead by offset characters."""
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]

    def advance(self) -> Optional[str]:
        """Advance to next character and return current."""
        char = self.current_char
        if char is not None:
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return char

    def location(self) -> SourceLocation:
        """Get current source location."""
        return SourceLocation(self.line, self.column, self.filename)

    def get_wavelength(self, char: str) -> float:
        """Get wavelength for a character."""
        return CHAR_WAVELENGTHS.get(char, 540.3)  # Default to space wavelength

    def make_token(self, token_type: TokenType, value: str, wavelength: Optional[float] = None) -> Token:
        """Create a token at current location."""
        if wavelength is None:
            wavelength = self.get_wavelength(value[0]) if value else 540.3
        return Token(token_type, value, wavelength, self.location())

    def skip_whitespace(self):
        """Skip whitespace (but not newlines in some contexts)."""
        while self.current_char is not None and self.current_char in ' \t\r':
            self.advance()

    def skip_comment(self):
        """Skip a comment (from # to end of line)."""
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def read_string(self) -> Token:
        """Read a string literal."""
        loc = self.location()
        quote = self.advance()  # Consume opening quote
        value = ""
        wavelength_sum = 0.0
        count = 0

        while self.current_char is not None and self.current_char != quote:
            if self.current_char == '\\':
                self.advance()
                escape = self.current_char
                if escape == 'n':
                    value += '\n'
                elif escape == 't':
                    value += '\t'
                elif escape == 'r':
                    value += '\r'
                elif escape == '\\':
                    value += '\\'
                elif escape == quote:
                    value += quote
                else:
                    value += escape or ''
                if self.current_char:
                    self.advance()
            else:
                char = self.current_char
                value += char
                wavelength_sum += self.get_wavelength(char)
                count += 1
                self.advance()

        if self.current_char != quote:
            raise LexerError(f"Unterminated string literal", loc)

        self.advance()  # Consume closing quote

        # Average wavelength of string content
        avg_wavelength = wavelength_sum / count if count > 0 else 698.0
        return Token(TokenType.STRING, value, avg_wavelength, loc)

    def read_number(self) -> Token:
        """Read a number literal (integer or float)."""
        loc = self.location()
        value = ""
        wavelength_sum = 0.0

        # Read integer part
        while self.current_char is not None and self.current_char.isdigit():
            value += self.current_char
            wavelength_sum += self.get_wavelength(self.current_char)
            self.advance()

        # Check for decimal point
        if self.current_char == '.' and self.peek() and self.peek().isdigit():
            value += self.advance()  # Consume '.'
            wavelength_sum += self.get_wavelength('.')

            # Read fractional part
            while self.current_char is not None and self.current_char.isdigit():
                value += self.current_char
                wavelength_sum += self.get_wavelength(self.current_char)
                self.advance()

            avg_wavelength = wavelength_sum / len(value)
            return Token(TokenType.FLOAT, value, avg_wavelength, loc)

        avg_wavelength = wavelength_sum / len(value) if value else 696.0
        return Token(TokenType.INTEGER, value, avg_wavelength, loc)

    def read_identifier(self) -> Token:
        """Read an identifier or keyword."""
        loc = self.location()
        value = ""
        wavelength_sum = 0.0

        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            value += self.current_char
            wavelength_sum += self.get_wavelength(self.current_char)
            self.advance()

        # Check for keywords
        if value in KEYWORDS:
            return Token(TokenType.KEYWORD, value, KEYWORD_WAVELENGTHS[value], loc)

        # Check for boolean literals
        if value == 'true':
            return Token(TokenType.BOOLEAN, value, 684.0, loc)
        if value == 'false':
            return Token(TokenType.BOOLEAN, value, 685.0, loc)
        if value == 'nil':
            return Token(TokenType.NIL, value, 686.0, loc)

        avg_wavelength = wavelength_sum / len(value) if value else 540.3
        return Token(TokenType.IDENTIFIER, value, avg_wavelength, loc)

    def read_operator(self) -> Token:
        """Read an operator."""
        loc = self.location()
        char = self.current_char

        # Two-character operators
        if char == '=' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token(TokenType.EQ, '==', 626.0, loc)

        if char == '!' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token(TokenType.NE, '!=', 552.0, loc)

        if char == '<' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token(TokenType.LE, '<=', 641.6, loc)

        if char == '>' and self.peek() == '=':
            self.advance()
            self.advance()
            return Token(TokenType.GE, '>=', 645.5, loc)

        # Single-character operators
        self.advance()

        operators = {
            '+': (TokenType.PLUS, 622.1),
            '-': (TokenType.MINUS, 567.5),
            '*': (TokenType.STAR, 618.2),
            '/': (TokenType.SLASH, 664.9),
            '%': (TokenType.PERCENT, 606.5),
            '^': (TokenType.CARET, 610.4),
            '<': (TokenType.LT, 641.6),
            '>': (TokenType.GT, 645.5),
            '=': (TokenType.ASSIGN, 626.0),
            '(': (TokenType.LPAREN, 571.4),
            ')': (TokenType.RPAREN, 575.3),
            '[': (TokenType.LBRACKET, 579.2),
            ']': (TokenType.RBRACKET, 583.1),
            '{': (TokenType.LBRACE, 587.0),
            '}': (TokenType.RBRACE, 590.9),
            ',': (TokenType.COMMA, 548.1),
            ':': (TokenType.COLON, 563.6),
            ';': (TokenType.SEMICOLON, 559.7),
            '.': (TokenType.DOT, 544.2),
        }

        if char in operators:
            token_type, wavelength = operators[char]
            return Token(token_type, char, wavelength, loc)

        raise LexerError(f"Unexpected character: {char!r}", loc)

    def tokenize(self) -> List[Token]:
        """Tokenize the entire source and return list of tokens."""
        self.tokens = []

        while self.current_char is not None:
            # Skip whitespace
            if self.current_char in ' \t\r':
                self.skip_whitespace()
                continue

            # Newlines
            if self.current_char == '\n':
                loc = self.location()
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\n', 668.8, loc))
                continue

            # Comments
            if self.current_char == '#':
                self.skip_comment()
                continue

            # String literals
            if self.current_char in '"\'':
                self.tokens.append(self.read_string())
                continue

            # Number literals
            if self.current_char.isdigit():
                self.tokens.append(self.read_number())
                continue

            # Identifiers and keywords
            if self.current_char.isalpha() or self.current_char == '_':
                self.tokens.append(self.read_identifier())
                continue

            # Operators and delimiters
            self.tokens.append(self.read_operator())

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', 700.0, self.location()))

        return self.tokens

    def token_stream(self) -> Generator[Token, None, None]:
        """Generate tokens one at a time (streaming mode)."""
        while self.current_char is not None:
            self.skip_whitespace()

            if self.current_char is None:
                break

            if self.current_char == '\n':
                loc = self.location()
                self.advance()
                yield Token(TokenType.NEWLINE, '\n', 668.8, loc)
                continue

            if self.current_char == '#':
                self.skip_comment()
                continue

            if self.current_char in '"\'':
                yield self.read_string()
                continue

            if self.current_char.isdigit():
                yield self.read_number()
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                yield self.read_identifier()
                continue

            yield self.read_operator()

        yield Token(TokenType.EOF, '', 700.0, self.location())
