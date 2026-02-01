"""
LUXBIN Compiler Error Types

Defines all error types used throughout the LUXBIN compiler and runtime.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SourceLocation:
    """Location in source code for error reporting."""
    line: int
    column: int
    file: Optional[str] = None

    def __str__(self):
        if self.file:
            return f"{self.file}:{self.line}:{self.column}"
        return f"line {self.line}, column {self.column}"


class LuxbinError(Exception):
    """Base class for all LUXBIN errors."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        self.message = message
        self.location = location
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.location:
            return f"[{self.location}] {self.message}"
        return self.message


class LexerError(LuxbinError):
    """Error during lexical analysis."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Lexer Error: {message}", location)


class ParserError(LuxbinError):
    """Error during parsing."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Parser Error: {message}", location)


class SemanticError(LuxbinError):
    """Error during semantic analysis."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Semantic Error: {message}", location)


class TypeError(LuxbinError):
    """Type mismatch error."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Type Error: {message}", location)


class NameError(LuxbinError):
    """Undefined variable or function error."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Name Error: {message}", location)


class RuntimeError(LuxbinError):
    """Error during execution."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Runtime Error: {message}", location)


class DivisionByZeroError(RuntimeError):
    """Division by zero."""

    def __init__(self, location: Optional[SourceLocation] = None):
        super().__init__("Division by zero", location)


class IndexError(RuntimeError):
    """Array index out of bounds."""

    def __init__(self, index: int, length: int, location: Optional[SourceLocation] = None):
        super().__init__(f"Index {index} out of bounds for array of length {length}", location)


class StackOverflowError(RuntimeError):
    """VM stack overflow."""

    def __init__(self, location: Optional[SourceLocation] = None):
        super().__init__("Stack overflow", location)


class QuantumError(LuxbinError):
    """Error in quantum operations."""

    def __init__(self, message: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Quantum Error: {message}", location)


class ImportError(LuxbinError):
    """Error importing module."""

    def __init__(self, module: str, location: Optional[SourceLocation] = None):
        super().__init__(f"Cannot import module '{module}'", location)


def format_error_context(source: str, location: SourceLocation, context_lines: int = 2) -> str:
    """Format error with source context."""
    lines = source.split('\n')
    result = []

    start = max(0, location.line - context_lines - 1)
    end = min(len(lines), location.line + context_lines)

    for i in range(start, end):
        line_num = i + 1
        prefix = ">>> " if line_num == location.line else "    "
        result.append(f"{prefix}{line_num:4d} | {lines[i]}")

        if line_num == location.line:
            # Add caret pointing to error column
            result.append("    " + " " * 7 + " " * (location.column - 1) + "^")

    return '\n'.join(result)
