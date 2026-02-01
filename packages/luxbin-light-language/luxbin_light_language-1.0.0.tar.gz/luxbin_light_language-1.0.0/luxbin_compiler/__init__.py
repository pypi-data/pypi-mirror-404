"""
LUXBIN Light Language Compiler

A complete compiler/interpreter for the LUXBIN photonic programming language.

Components:
- lexer: Tokenize source code into wavelength-based tokens
- parser: Build Abstract Syntax Tree from tokens
- ast_nodes: AST node class definitions
- analyzer: Semantic analysis and type checking
- codegen: Generate LUXBIN bytecode
- vm: Stack-based virtual machine for execution
- builtins: Standard library functions
- errors: Error types and messages
- cli: Command-line interface

Usage:
    from luxbin_compiler import compile_and_run

    source = '''
    func fibonacci(n)
        if n < 2 then
            return n
        end
        return fibonacci(n - 1) + fibonacci(n - 2)
    end

    let result = fibonacci(10)
    photon_print(result)
    '''

    compile_and_run(source)
"""

__version__ = "1.0.0"
__author__ = "Nichole Christie"
__license__ = "MIT"

from .lexer import Lexer, Token, TokenType
from .parser import Parser
from .ast_nodes import *
from .analyzer import SemanticAnalyzer
from .codegen import CodeGenerator
from .vm import LuxbinVM
from .builtins import BUILTINS
from .errors import LuxbinError, LexerError, ParserError, RuntimeError


def tokenize(source: str) -> list:
    """Tokenize LUXBIN source code."""
    lexer = Lexer(source)
    return lexer.tokenize()


def parse(source: str):
    """Parse LUXBIN source code into AST."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def compile_to_bytecode(source: str) -> bytes:
    """Compile LUXBIN source code to bytecode."""
    ast = parse(source)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    codegen = CodeGenerator()
    return codegen.generate(ast)


def run_bytecode(bytecode: bytes):
    """Execute LUXBIN bytecode."""
    vm = LuxbinVM()
    return vm.execute(bytecode)


def compile_and_run(source: str):
    """Compile and execute LUXBIN source code."""
    bytecode = compile_to_bytecode(source)
    return run_bytecode(bytecode)


def interpret(source: str):
    """Interpret LUXBIN source code directly (without bytecode)."""
    from .interpreter import Interpreter
    ast = parse(source)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    interpreter = Interpreter()
    return interpreter.run(ast)
