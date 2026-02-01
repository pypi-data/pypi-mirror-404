"""Tests for the LUXBIN Compiler (code generator)."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luxbin_compiler.lexer import Lexer
from luxbin_compiler.parser import Parser
from luxbin_compiler.codegen import CodeGenerator, Opcode


def compile_source(source: str) -> list:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    codegen = CodeGenerator()
    return codegen.generate(ast)


class TestCodeGenBasics:
    def test_number_literal(self):
        bytecode = compile_source("42")
        # Should contain PUSH and HALT at minimum
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.PUSH in opcodes
        assert Opcode.HALT in opcodes

    def test_string_literal(self):
        bytecode = compile_source('"hello"')
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.PUSH in opcodes

    def test_binary_op_add(self):
        bytecode = compile_source("1 + 2")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.ADD in opcodes

    def test_binary_op_sub(self):
        bytecode = compile_source("5 - 3")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.SUB in opcodes

    def test_binary_op_mul(self):
        bytecode = compile_source("2 * 3")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.MUL in opcodes

    def test_binary_op_div(self):
        bytecode = compile_source("6 / 2")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.DIV in opcodes

    def test_comparison(self):
        bytecode = compile_source("1 == 2")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.EQ in opcodes


class TestCodeGenVariables:
    def test_let_declaration(self):
        bytecode = compile_source("let x = 42")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.GSTORE in opcodes or Opcode.STORE in opcodes

    def test_variable_load(self):
        bytecode = compile_source("let x = 42\nx")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.GLOAD in opcodes or Opcode.LOAD in opcodes


class TestCodeGenControlFlow:
    def test_if_generates_jump(self):
        bytecode = compile_source("if true then\n    42\nend")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.JZ in opcodes

    def test_while_generates_jumps(self):
        bytecode = compile_source("while true do\n    42\nend")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.JZ in opcodes
        assert Opcode.JMP in opcodes


class TestCodeGenFunctions:
    def test_function_call(self):
        bytecode = compile_source("func f()\n    return 1\nend\nf()")
        opcodes = [instr[0] if isinstance(instr, tuple) else instr for instr in bytecode]
        assert Opcode.CALL in opcodes
        assert Opcode.RET in opcodes
