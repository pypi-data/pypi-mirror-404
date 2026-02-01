"""
LUXBIN Command-Line Interface

Usage:
    luxbin run <file.lux>          Run a LUXBIN program
    luxbin compile <file.lux>      Compile to bytecode (.luxc)
    luxbin exec <file.luxc>        Execute compiled bytecode
    luxbin tokens <file.lux>       Show lexer tokens
    luxbin ast <file.lux>          Show AST
    luxbin check <file.lux>        Run semantic analysis only
    luxbin repl                    Interactive REPL
    luxbin version                 Show version
"""

import sys
import os
import argparse

from .lexer import Lexer
from .parser import Parser
from .analyzer import SemanticAnalyzer
from .codegen import CodeGenerator, Opcode
from .vm import LuxbinVM
from .errors import LuxbinError


__version__ = "1.0.0"


def read_source(path: str) -> str:
    """Read source file."""
    if not os.path.exists(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r") as f:
        return f.read()


def run_file(path: str, debug: bool = False):
    """Compile and execute a .lux file."""
    source = read_source(path)
    try:
        # Lex
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        # Parse
        parser = Parser(tokens)
        ast = parser.parse()

        # Analyze
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        if analyzer.errors:
            for err in analyzer.errors:
                print(f"Analysis error: {err}", file=sys.stderr)
            sys.exit(1)

        # Compile
        codegen = CodeGenerator()
        bytecode = codegen.generate(ast)

        # Execute
        vm = LuxbinVM(debug=debug)
        vm.execute(bytecode)

    except LuxbinError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def compile_file(path: str, output: str = None):
    """Compile a .lux file to bytecode."""
    source = read_source(path)
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()

        parser = Parser(tokens)
        ast = parser.parse()

        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        if analyzer.errors:
            for err in analyzer.errors:
                print(f"Analysis error: {err}", file=sys.stderr)
            sys.exit(1)

        codegen = CodeGenerator()
        bytecode = codegen.generate(ast)

        if output is None:
            output = os.path.splitext(path)[0] + ".luxc"

        codegen.write_bytecode_file(bytecode, output)
        print(f"Compiled: {path} -> {output}")

    except LuxbinError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def exec_bytecode(path: str, debug: bool = False):
    """Execute a compiled .luxc file."""
    if not os.path.exists(path):
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    try:
        codegen = CodeGenerator()
        bytecode = codegen.read_bytecode_file(path)

        vm = LuxbinVM(debug=debug)
        vm.execute(bytecode)

    except LuxbinError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def show_tokens(path: str):
    """Display lexer tokens for a source file."""
    source = read_source(path)
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        for tok in tokens:
            wl = f" [{tok.wavelength:.1f}nm]" if tok.wavelength else ""
            print(f"  {tok.type.name:20s} {tok.value!r:30s}{wl}  "
                  f"(line {tok.line}, col {tok.column})")
    except LuxbinError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def show_ast(path: str):
    """Display AST for a source file."""
    source = read_source(path)
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        _print_ast(ast, indent=0)
    except LuxbinError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def _print_ast(node, indent: int = 0):
    """Recursively print AST nodes."""
    prefix = "  " * indent
    if isinstance(node, list):
        for item in node:
            _print_ast(item, indent)
        return

    name = type(node).__name__
    # Print node type
    attrs = {}
    if hasattr(node, "__dataclass_fields__"):
        for field_name in node.__dataclass_fields__:
            val = getattr(node, field_name)
            if field_name == "location":
                continue
            if isinstance(val, list):
                print(f"{prefix}{name}.{field_name}:")
                for item in val:
                    _print_ast(item, indent + 1)
            elif hasattr(val, "__dataclass_fields__"):
                print(f"{prefix}{name}.{field_name}:")
                _print_ast(val, indent + 1)
            else:
                attrs[field_name] = val

    attr_str = ", ".join(f"{k}={v!r}" for k, v in attrs.items())
    print(f"{prefix}{name}({attr_str})")


def check_file(path: str):
    """Run semantic analysis only."""
    source = read_source(path)
    try:
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        if analyzer.errors:
            for err in analyzer.errors:
                print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"OK: {path} (no errors)")

    except LuxbinError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def repl():
    """Interactive LUXBIN REPL."""
    print(f"LUXBIN Light Language REPL v{__version__}")
    print("Type 'exit' or Ctrl+D to quit.\n")

    vm = LuxbinVM()
    history = []

    while True:
        try:
            line = input("luxbin> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if line.strip() in ("exit", "quit"):
            break

        if not line.strip():
            continue

        history.append(line)

        # Accumulate multi-line input
        source = line
        while source.count("func ") > source.count("\nend") + source.count("end\n") + (1 if source.endswith("end") else 0):
            try:
                cont = input("...    ")
                source += "\n" + cont
            except (EOFError, KeyboardInterrupt):
                break

        try:
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            codegen = CodeGenerator()
            bytecode = codegen.generate(ast)
            vm.execute(bytecode)
        except LuxbinError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Runtime error: {e}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="luxbin",
        description="LUXBIN Light Language Compiler & Runtime",
    )
    parser.add_argument("--version", action="version", version=f"luxbin {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run
    run_parser = subparsers.add_parser("run", help="Run a .lux program")
    run_parser.add_argument("file", help="Source file (.lux)")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug output")

    # compile
    comp_parser = subparsers.add_parser("compile", help="Compile to bytecode")
    comp_parser.add_argument("file", help="Source file (.lux)")
    comp_parser.add_argument("-o", "--output", help="Output file (.luxc)")

    # exec
    exec_parser = subparsers.add_parser("exec", help="Execute compiled bytecode")
    exec_parser.add_argument("file", help="Bytecode file (.luxc)")
    exec_parser.add_argument("--debug", action="store_true", help="Enable debug output")

    # tokens
    tok_parser = subparsers.add_parser("tokens", help="Show lexer tokens")
    tok_parser.add_argument("file", help="Source file (.lux)")

    # ast
    ast_parser = subparsers.add_parser("ast", help="Show AST")
    ast_parser.add_argument("file", help="Source file (.lux)")

    # check
    chk_parser = subparsers.add_parser("check", help="Run semantic analysis")
    chk_parser.add_argument("file", help="Source file (.lux)")

    # repl
    subparsers.add_parser("repl", help="Interactive REPL")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "run":
        run_file(args.file, debug=getattr(args, "debug", False))
    elif args.command == "compile":
        compile_file(args.file, output=args.output)
    elif args.command == "exec":
        exec_bytecode(args.file, debug=getattr(args, "debug", False))
    elif args.command == "tokens":
        show_tokens(args.file)
    elif args.command == "ast":
        show_ast(args.file)
    elif args.command == "check":
        check_file(args.file)
    elif args.command == "repl":
        repl()


if __name__ == "__main__":
    main()
