"""Tests for LUXBIN example programs - verifies they parse and compile."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luxbin_compiler.lexer import Lexer
from luxbin_compiler.parser import Parser
from luxbin_compiler.codegen import CodeGenerator


EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")


def get_example_files():
    """Get all .lux files in the examples directory."""
    if not os.path.exists(EXAMPLES_DIR):
        return []
    return [f for f in os.listdir(EXAMPLES_DIR) if f.endswith(".lux")]


class TestExamplesParse:
    @pytest.mark.parametrize("filename", get_example_files())
    def test_example_parses(self, filename):
        """Each example file should parse without errors."""
        path = os.path.join(EXAMPLES_DIR, filename)
        with open(path, "r") as f:
            source = f.read()

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        assert ast is not None
        assert len(ast.statements) > 0

    @pytest.mark.parametrize("filename", get_example_files())
    def test_example_compiles(self, filename):
        """Each example file should compile to bytecode without errors."""
        path = os.path.join(EXAMPLES_DIR, filename)
        with open(path, "r") as f:
            source = f.read()

        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        codegen = CodeGenerator()
        bytecode = codegen.generate(ast)
        assert bytecode is not None
        assert len(bytecode) > 0
