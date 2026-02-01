"""
LUXBIN AST Node Definitions

Defines all Abstract Syntax Tree node types for the LUXBIN language.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from .errors import SourceLocation


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    location: Optional[SourceLocation] = field(default=None, repr=False, kw_only=True)


# ============================================================================
# Program and Statements
# ============================================================================

@dataclass
class Program(ASTNode):
    """Root node representing an entire program."""
    statements: List['Statement'] = field(default_factory=list)


Statement = Union[
    'Declaration',
    'Assignment',
    'IfStatement',
    'WhileStatement',
    'ForStatement',
    'FunctionDef',
    'ReturnStatement',
    'BreakStatement',
    'ContinueStatement',
    'QuantumBlock',
    'ImportStatement',
    'ExportStatement',
    'ExpressionStatement',
]


@dataclass
class Declaration(ASTNode):
    """Variable or constant declaration: let x = 5 or const y = 10"""
    name: str
    value: 'Expression'
    is_const: bool = False


@dataclass
class Assignment(ASTNode):
    """Variable assignment: x = 5"""
    target: Union[str, 'IndexExpression']
    value: 'Expression'


@dataclass
class IfStatement(ASTNode):
    """Conditional statement: if condition then ... else ... end"""
    condition: 'Expression'
    then_body: List[Statement]
    else_body: Optional[List[Statement]] = None


@dataclass
class WhileStatement(ASTNode):
    """While loop: while condition do ... end"""
    condition: 'Expression'
    body: List[Statement]


@dataclass
class ForStatement(ASTNode):
    """For loop: for x in iterable do ... end"""
    variable: str
    iterable: 'Expression'
    body: List[Statement]


@dataclass
class FunctionDef(ASTNode):
    """Function definition: func name(params) ... end"""
    name: str
    params: List[str]
    body: List[Statement]


@dataclass
class ReturnStatement(ASTNode):
    """Return statement: return expression"""
    value: Optional['Expression'] = None


@dataclass
class BreakStatement(ASTNode):
    """Break statement: break"""
    pass


@dataclass
class ContinueStatement(ASTNode):
    """Continue statement: continue"""
    pass


@dataclass
class QuantumBlock(ASTNode):
    """Quantum block: quantum ... end"""
    body: List[Statement]


@dataclass
class ImportStatement(ASTNode):
    """Import statement: import module"""
    module: str
    alias: Optional[str] = None


@dataclass
class ExportStatement(ASTNode):
    """Export statement: export name"""
    name: str


@dataclass
class ExpressionStatement(ASTNode):
    """Expression used as a statement (e.g., function call)."""
    expression: 'Expression'


# ============================================================================
# Expressions
# ============================================================================

Expression = Union[
    'IntegerLiteral',
    'FloatLiteral',
    'StringLiteral',
    'BooleanLiteral',
    'NilLiteral',
    'ArrayLiteral',
    'Identifier',
    'BinaryOp',
    'UnaryOp',
    'CallExpression',
    'IndexExpression',
    'MemberExpression',
    'QuantumExpression',
]


@dataclass
class IntegerLiteral(ASTNode):
    """Integer literal: 42"""
    value: int
    wavelength: float = 696.0  # photon_int type marker


@dataclass
class FloatLiteral(ASTNode):
    """Float literal: 3.14"""
    value: float
    wavelength: float = 697.0  # photon_float type marker


@dataclass
class StringLiteral(ASTNode):
    """String literal: "hello" """
    value: str
    wavelength: float = 698.0  # photon_string type marker


@dataclass
class BooleanLiteral(ASTNode):
    """Boolean literal: true or false"""
    value: bool
    wavelength: float = 699.0  # photon_bool type marker

    def __post_init__(self):
        self.wavelength = 684.0 if self.value else 685.0


@dataclass
class NilLiteral(ASTNode):
    """Nil literal: nil"""
    wavelength: float = 686.0


@dataclass
class ArrayLiteral(ASTNode):
    """Array literal: [1, 2, 3]"""
    elements: List['Expression'] = field(default_factory=list)
    wavelength: float = 700.0  # photon_array type marker


@dataclass
class Identifier(ASTNode):
    """Variable or function name."""
    name: str
    wavelength: float = 0.0

    def __post_init__(self):
        # Calculate average wavelength of name characters
        from .lexer import CHAR_WAVELENGTHS
        total = sum(CHAR_WAVELENGTHS.get(c, 540.3) for c in self.name)
        self.wavelength = total / len(self.name) if self.name else 540.3


@dataclass
class BinaryOp(ASTNode):
    """Binary operation: a + b, x == y, etc."""
    operator: str
    left: 'Expression'
    right: 'Expression'

    # Operator wavelengths (from amplitude modulation spec)
    OPERATOR_WAVELENGTHS = {
        '+': 622.1, '-': 567.5, '*': 618.2, '/': 664.9,
        '%': 606.5, '^': 610.4,
        '==': 626.0, '!=': 552.0,
        '<': 641.6, '>': 645.5, '<=': 641.6, '>=': 645.5,
        'and': 687.0, 'or': 688.0,
    }

    @property
    def wavelength(self) -> float:
        return self.OPERATOR_WAVELENGTHS.get(self.operator, 540.3)


@dataclass
class UnaryOp(ASTNode):
    """Unary operation: -x, not y"""
    operator: str
    operand: 'Expression'

    OPERATOR_WAVELENGTHS = {
        '-': 567.5,
        'not': 689.0,
    }

    @property
    def wavelength(self) -> float:
        return self.OPERATOR_WAVELENGTHS.get(self.operator, 540.3)


@dataclass
class CallExpression(ASTNode):
    """Function call: func(args)"""
    function: Union[str, 'Expression']
    arguments: List['Expression'] = field(default_factory=list)


@dataclass
class IndexExpression(ASTNode):
    """Array index: arr[index]"""
    array: 'Expression'
    index: 'Expression'


@dataclass
class MemberExpression(ASTNode):
    """Member access: obj.member"""
    object: 'Expression'
    member: str


@dataclass
class QuantumExpression(ASTNode):
    """Quantum operation expression."""
    operation: str  # 'superpose', 'measure', 'entangle', etc.
    arguments: List['Expression'] = field(default_factory=list)

    OPERATION_WAVELENGTHS = {
        'superpose': 694.0,
        'measure': 693.0,
        'entangle': 695.0,
        'hadamard': 637.0,
        'cnot': 637.0,
        'phase': 637.0,
    }

    @property
    def wavelength(self) -> float:
        return self.OPERATION_WAVELENGTHS.get(self.operation, 692.0)


# ============================================================================
# Type Annotations (optional)
# ============================================================================

@dataclass
class TypeAnnotation(ASTNode):
    """Type annotation for variables/parameters."""
    name: str  # photon_int, photon_float, etc.

    TYPE_WAVELENGTHS = {
        'photon_int': 696.0,
        'photon_float': 697.0,
        'photon_string': 698.0,
        'photon_bool': 699.0,
        'photon_array': 700.0,
        'photon_qubit': 637.0,
    }

    @property
    def wavelength(self) -> float:
        return self.TYPE_WAVELENGTHS.get(self.name, 540.3)


# ============================================================================
# Visitor Pattern Support
# ============================================================================

class ASTVisitor:
    """Base class for AST visitors."""

    def visit(self, node: ASTNode) -> Any:
        """Visit a node by dispatching to the appropriate visit_* method."""
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode) -> Any:
        """Called for nodes without a specific visitor method."""
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")


class ASTTransformer(ASTVisitor):
    """Base class for AST transformers that modify the tree."""

    def visit_Program(self, node: Program) -> Program:
        return Program(
            statements=[self.visit(stmt) for stmt in node.statements],
            location=node.location
        )

    def visit_Declaration(self, node: Declaration) -> Declaration:
        return Declaration(
            name=node.name,
            value=self.visit(node.value),
            is_const=node.is_const,
            location=node.location
        )

    def visit_BinaryOp(self, node: BinaryOp) -> BinaryOp:
        return BinaryOp(
            operator=node.operator,
            left=self.visit(node.left),
            right=self.visit(node.right),
            location=node.location
        )

    # Add more transform methods as needed...
