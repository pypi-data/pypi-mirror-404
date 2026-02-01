"""Tests for the LUXBIN Parser."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luxbin_compiler.lexer import Lexer
from luxbin_compiler.parser import Parser
from luxbin_compiler.ast_nodes import *


def parse(source: str) -> Program:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


class TestParserDeclarations:
    def test_let_declaration(self):
        prog = parse("let x = 42")
        assert len(prog.statements) == 1
        stmt = prog.statements[0]
        assert isinstance(stmt, Declaration)
        assert stmt.name == "x"
        assert stmt.mutable is True

    def test_const_declaration(self):
        prog = parse("const PI = 3.14")
        stmt = prog.statements[0]
        assert isinstance(stmt, Declaration)
        assert stmt.name == "PI"
        assert stmt.mutable is False

    def test_assignment(self):
        prog = parse("x = 10")
        stmt = prog.statements[0]
        assert isinstance(stmt, Assignment)
        assert stmt.name == "x"


class TestParserExpressions:
    def test_number_literal(self):
        prog = parse("42")
        stmt = prog.statements[0]
        assert isinstance(stmt, NumberLiteral)
        assert stmt.value == 42

    def test_string_literal(self):
        prog = parse('"hello"')
        stmt = prog.statements[0]
        assert isinstance(stmt, StringLiteral)
        assert stmt.value == "hello"

    def test_boolean_true(self):
        prog = parse("true")
        stmt = prog.statements[0]
        assert isinstance(stmt, BooleanLiteral)
        assert stmt.value is True

    def test_binary_expression(self):
        prog = parse("1 + 2")
        stmt = prog.statements[0]
        assert isinstance(stmt, BinaryOp)
        assert stmt.operator == "+"

    def test_operator_precedence(self):
        prog = parse("1 + 2 * 3")
        stmt = prog.statements[0]
        assert isinstance(stmt, BinaryOp)
        assert stmt.operator == "+"
        assert isinstance(stmt.right, BinaryOp)
        assert stmt.right.operator == "*"

    def test_array_literal(self):
        prog = parse("[1, 2, 3]")
        stmt = prog.statements[0]
        assert isinstance(stmt, ArrayLiteral)
        assert len(stmt.elements) == 3


class TestParserControlFlow:
    def test_if_then_end(self):
        prog = parse("if true then\n    42\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.else_body is None or len(stmt.else_body) == 0

    def test_if_else(self):
        prog = parse("if true then\n    1\nelse\n    2\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, IfStatement)
        assert stmt.else_body is not None
        assert len(stmt.else_body) > 0

    def test_while_loop(self):
        prog = parse("while true do\n    42\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, WhileLoop)

    def test_for_loop(self):
        prog = parse("for x in [1, 2, 3] do\n    x\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, ForLoop)
        assert stmt.variable == "x"


class TestParserFunctions:
    def test_function_definition(self):
        prog = parse("func add(a, b)\n    return a + b\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, FunctionDef)
        assert stmt.name == "add"
        assert stmt.params == ["a", "b"]

    def test_function_no_params(self):
        prog = parse("func hello()\n    42\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, FunctionDef)
        assert stmt.params == []

    def test_function_call(self):
        prog = parse("add(1, 2)")
        stmt = prog.statements[0]
        assert isinstance(stmt, FunctionCall)
        assert stmt.name == "add"
        assert len(stmt.arguments) == 2

    def test_return_statement(self):
        prog = parse("func f()\n    return 42\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, FunctionDef)
        ret = stmt.body[0]
        assert isinstance(ret, ReturnStatement)


class TestParserQuantum:
    def test_quantum_block(self):
        prog = parse("quantum\n    42\nend")
        stmt = prog.statements[0]
        assert isinstance(stmt, QuantumBlock)
