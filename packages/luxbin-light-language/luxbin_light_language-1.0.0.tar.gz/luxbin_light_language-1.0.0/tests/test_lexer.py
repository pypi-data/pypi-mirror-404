"""Tests for the LUXBIN Lexer."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luxbin_compiler.lexer import Lexer, TokenType


class TestLexerBasics:
    def test_empty_source(self):
        lexer = Lexer("")
        tokens = lexer.tokenize()
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF

    def test_integer(self):
        lexer = Lexer("42")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_float(self):
        lexer = Lexer("3.14")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "3.14"

    def test_string(self):
        lexer = Lexer('"hello"')
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_identifier(self):
        lexer = Lexer("my_var")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "my_var"

    def test_comment_ignored(self):
        lexer = Lexer("# this is a comment\n42")
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"


class TestLexerKeywords:
    @pytest.mark.parametrize("keyword", [
        "let", "const", "func", "return", "if", "then", "else", "end",
        "while", "for", "in", "do", "break", "continue", "true", "false",
        "nil", "and", "or", "not", "import", "export", "quantum",
        "measure", "superpose", "entangle",
    ])
    def test_keyword(self, keyword):
        lexer = Lexer(keyword)
        tokens = lexer.tokenize()
        assert tokens[0].type == TokenType.KEYWORD
        assert tokens[0].value == keyword

    def test_keyword_has_wavelength(self):
        lexer = Lexer("let")
        tokens = lexer.tokenize()
        assert tokens[0].wavelength is not None
        assert tokens[0].wavelength > 0


class TestLexerOperators:
    @pytest.mark.parametrize("op,expected", [
        ("+", TokenType.PLUS),
        ("-", TokenType.MINUS),
        ("*", TokenType.STAR),
        ("/", TokenType.SLASH),
        ("%", TokenType.PERCENT),
        ("^", TokenType.CARET),
        ("==", TokenType.EQUAL_EQUAL),
        ("!=", TokenType.BANG_EQUAL),
        ("<", TokenType.LESS),
        (">", TokenType.GREATER),
        ("<=", TokenType.LESS_EQUAL),
        (">=", TokenType.GREATER_EQUAL),
        ("=", TokenType.EQUAL),
        ("(", TokenType.LPAREN),
        (")", TokenType.RPAREN),
        ("[", TokenType.LBRACKET),
        ("]", TokenType.RBRACKET),
        (",", TokenType.COMMA),
    ])
    def test_operator(self, op, expected):
        lexer = Lexer(op)
        tokens = lexer.tokenize()
        assert tokens[0].type == expected


class TestLexerPrograms:
    def test_variable_declaration(self):
        lexer = Lexer('let x = 42')
        tokens = lexer.tokenize()
        types = [t.type for t in tokens[:-1]]  # exclude EOF
        assert types == [TokenType.KEYWORD, TokenType.IDENTIFIER,
                        TokenType.EQUAL, TokenType.NUMBER]

    def test_function_definition(self):
        source = "func add(a, b)\n    return a + b\nend"
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        assert tokens[0].value == "func"
        assert tokens[1].value == "add"

    def test_wavelength_assigned(self):
        lexer = Lexer("a")
        tokens = lexer.tokenize()
        # Identifiers should have wavelength based on character encoding
        assert tokens[0].wavelength is not None
