"""
LUXBIN Semantic Analyzer

Performs semantic analysis on the AST:
- Type checking
- Scope resolution
- Variable declaration validation
- Function signature validation
- Quantum operation validation
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from .ast_nodes import *
from .errors import SemanticError, NameError, TypeError, SourceLocation


@dataclass
class Symbol:
    """Symbol table entry."""
    name: str
    symbol_type: str  # 'variable', 'constant', 'function', 'parameter', 'builtin'
    data_type: Optional[str] = None  # 'int', 'float', 'string', 'bool', 'array', 'qubit', 'any'
    is_const: bool = False
    params: Optional[List[str]] = None  # For functions
    location: Optional[SourceLocation] = None


@dataclass
class Scope:
    """Represents a scope in the program."""
    parent: Optional['Scope'] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    is_function: bool = False
    is_loop: bool = False
    is_quantum: bool = False

    def define(self, symbol: Symbol):
        """Define a symbol in this scope."""
        if symbol.name in self.symbols:
            raise SemanticError(
                f"'{symbol.name}' is already defined in this scope",
                symbol.location
            )
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        """Look up a symbol in this scope or parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope."""
        return self.symbols.get(name)


class SemanticAnalyzer(ASTVisitor):
    """
    Semantic analyzer for LUXBIN programs.

    Performs:
    - Symbol table construction
    - Type checking
    - Scope validation
    - Control flow validation
    """

    # Built-in functions with their signatures
    BUILTINS = {
        # I/O
        'photon_print': ('any', ['any']),
        'photon_input': ('string', ['string']),
        'photon_read': ('string', ['string']),
        'photon_write': ('bool', ['string', 'any']),

        # Math
        'photon_abs': ('float', ['float']),
        'photon_sqrt': ('float', ['float']),
        'photon_pow': ('float', ['float', 'float']),
        'photon_sin': ('float', ['float']),
        'photon_cos': ('float', ['float']),
        'photon_tan': ('float', ['float']),
        'photon_floor': ('int', ['float']),
        'photon_ceil': ('int', ['float']),
        'photon_round': ('int', ['float']),
        'photon_min': ('float', ['float', 'float']),
        'photon_max': ('float', ['float', 'float']),

        # String/Wavelength
        'photon_len': ('int', ['any']),
        'photon_concat': ('string', ['string', 'string']),
        'photon_slice': ('string', ['string', 'int', 'int']),
        'photon_wavelength': ('float', ['string']),
        'photon_char': ('string', ['float']),
        'photon_upper': ('string', ['string']),
        'photon_lower': ('string', ['string']),

        # Array
        'photon_array': ('array', ['int']),
        'photon_push': ('array', ['array', 'any']),
        'photon_pop': ('any', ['array']),
        'photon_get': ('any', ['array', 'int']),
        'photon_set': ('array', ['array', 'int', 'any']),
        'photon_sort': ('array', ['array']),
        'photon_reverse': ('array', ['array']),

        # Type conversion
        'photon_to_int': ('int', ['any']),
        'photon_to_float': ('float', ['any']),
        'photon_to_string': ('string', ['any']),
        'photon_to_bool': ('bool', ['any']),

        # Quantum
        'quantum_superpose': ('qubit', ['any']),
        'quantum_measure': ('int', ['qubit']),
        'quantum_entangle': ('nil', ['qubit', 'qubit']),
        'quantum_hadamard': ('qubit', ['qubit']),
        'quantum_cnot': ('nil', ['qubit', 'qubit']),
        'quantum_phase': ('qubit', ['qubit', 'float']),
        'quantum_teleport': ('bool', ['qubit', 'any']),
    }

    def __init__(self):
        self.current_scope: Scope = Scope()
        self.global_scope: Scope = self.current_scope
        self.errors: List[SemanticError] = []
        self.warnings: List[str] = []
        self._init_builtins()

    def _init_builtins(self):
        """Initialize built-in functions in global scope."""
        for name, (return_type, params) in self.BUILTINS.items():
            self.global_scope.define(Symbol(
                name=name,
                symbol_type='builtin',
                data_type=return_type,
                params=params
            ))

    def enter_scope(self, is_function: bool = False, is_loop: bool = False,
                    is_quantum: bool = False) -> Scope:
        """Enter a new scope."""
        new_scope = Scope(
            parent=self.current_scope,
            is_function=is_function,
            is_loop=is_loop,
            is_quantum=is_quantum
        )
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self):
        """Exit current scope."""
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent

    def in_loop(self) -> bool:
        """Check if we're inside a loop."""
        scope = self.current_scope
        while scope:
            if scope.is_loop:
                return True
            scope = scope.parent
        return False

    def in_function(self) -> bool:
        """Check if we're inside a function."""
        scope = self.current_scope
        while scope:
            if scope.is_function:
                return True
            scope = scope.parent
        return False

    def in_quantum(self) -> bool:
        """Check if we're inside a quantum block."""
        scope = self.current_scope
        while scope:
            if scope.is_quantum:
                return True
            scope = scope.parent
        return False

    def error(self, message: str, location: Optional[SourceLocation] = None):
        """Record a semantic error."""
        self.errors.append(SemanticError(message, location))

    def warn(self, message: str):
        """Record a warning."""
        self.warnings.append(message)

    def analyze(self, program: Program) -> bool:
        """Analyze a program. Returns True if no errors."""
        self.visit(program)
        if self.errors:
            for err in self.errors:
                print(f"Error: {err}")
            return False
        return True

    # ========================================================================
    # Visitor Methods
    # ========================================================================

    def visit_Program(self, node: Program):
        """Visit program node."""
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Declaration(self, node: Declaration):
        """Visit variable/constant declaration."""
        # Analyze the value expression first
        value_type = self.visit(node.value)

        # Define the variable in current scope
        try:
            self.current_scope.define(Symbol(
                name=node.name,
                symbol_type='constant' if node.is_const else 'variable',
                data_type=value_type,
                is_const=node.is_const,
                location=node.location
            ))
        except SemanticError as e:
            self.error(str(e), node.location)

    def visit_Assignment(self, node: Assignment):
        """Visit assignment statement."""
        # Check target exists and is not a constant
        if isinstance(node.target, str):
            symbol = self.current_scope.lookup(node.target)
            if symbol is None:
                self.error(f"Undefined variable '{node.target}'", node.location)
            elif symbol.is_const:
                self.error(f"Cannot assign to constant '{node.target}'", node.location)
        else:
            # Index assignment
            self.visit(node.target)

        self.visit(node.value)

    def visit_IfStatement(self, node: IfStatement):
        """Visit if statement."""
        cond_type = self.visit(node.condition)

        # Condition should be boolean-compatible
        if cond_type not in ('bool', 'int', 'any'):
            self.warn(f"Condition in if statement should be boolean, got {cond_type}")

        self.enter_scope()
        for stmt in node.then_body:
            self.visit(stmt)
        self.exit_scope()

        if node.else_body:
            self.enter_scope()
            for stmt in node.else_body:
                self.visit(stmt)
            self.exit_scope()

    def visit_WhileStatement(self, node: WhileStatement):
        """Visit while loop."""
        cond_type = self.visit(node.condition)

        if cond_type not in ('bool', 'int', 'any'):
            self.warn(f"Condition in while loop should be boolean, got {cond_type}")

        self.enter_scope(is_loop=True)
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_ForStatement(self, node: ForStatement):
        """Visit for loop."""
        iter_type = self.visit(node.iterable)

        if iter_type not in ('array', 'string', 'any'):
            self.warn(f"For loop iterable should be array or string, got {iter_type}")

        self.enter_scope(is_loop=True)

        # Define loop variable
        self.current_scope.define(Symbol(
            name=node.variable,
            symbol_type='variable',
            data_type='any',
            location=node.location
        ))

        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_FunctionDef(self, node: FunctionDef):
        """Visit function definition."""
        # Define function in current scope
        try:
            self.current_scope.define(Symbol(
                name=node.name,
                symbol_type='function',
                data_type='any',  # Return type inferred
                params=node.params,
                location=node.location
            ))
        except SemanticError as e:
            self.error(str(e), node.location)

        # Enter function scope
        self.enter_scope(is_function=True)

        # Define parameters
        for param in node.params:
            self.current_scope.define(Symbol(
                name=param,
                symbol_type='parameter',
                data_type='any'
            ))

        # Analyze body
        for stmt in node.body:
            self.visit(stmt)

        self.exit_scope()

    def visit_ReturnStatement(self, node: ReturnStatement):
        """Visit return statement."""
        if not self.in_function():
            self.error("'return' outside function", node.location)

        if node.value:
            self.visit(node.value)

    def visit_BreakStatement(self, node: BreakStatement):
        """Visit break statement."""
        if not self.in_loop():
            self.error("'break' outside loop", node.location)

    def visit_ContinueStatement(self, node: ContinueStatement):
        """Visit continue statement."""
        if not self.in_loop():
            self.error("'continue' outside loop", node.location)

    def visit_QuantumBlock(self, node: QuantumBlock):
        """Visit quantum block."""
        self.enter_scope(is_quantum=True)
        for stmt in node.body:
            self.visit(stmt)
        self.exit_scope()

    def visit_ImportStatement(self, node: ImportStatement):
        """Visit import statement."""
        # For now, just record the import
        pass

    def visit_ExportStatement(self, node: ExportStatement):
        """Visit export statement."""
        symbol = self.current_scope.lookup(node.name)
        if symbol is None:
            self.error(f"Cannot export undefined '{node.name}'", node.location)

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        """Visit expression statement."""
        self.visit(node.expression)

    # ========================================================================
    # Expression Visitors (return type string)
    # ========================================================================

    def visit_IntegerLiteral(self, node: IntegerLiteral) -> str:
        return 'int'

    def visit_FloatLiteral(self, node: FloatLiteral) -> str:
        return 'float'

    def visit_StringLiteral(self, node: StringLiteral) -> str:
        return 'string'

    def visit_BooleanLiteral(self, node: BooleanLiteral) -> str:
        return 'bool'

    def visit_NilLiteral(self, node: NilLiteral) -> str:
        return 'nil'

    def visit_ArrayLiteral(self, node: ArrayLiteral) -> str:
        for elem in node.elements:
            self.visit(elem)
        return 'array'

    def visit_Identifier(self, node: Identifier) -> str:
        symbol = self.current_scope.lookup(node.name)
        if symbol is None:
            self.error(f"Undefined variable '{node.name}'", node.location)
            return 'any'
        return symbol.data_type or 'any'

    def visit_BinaryOp(self, node: BinaryOp) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        # Arithmetic operators
        if node.operator in ('+', '-', '*', '/', '%', '^'):
            if left_type in ('int', 'float') and right_type in ('int', 'float'):
                return 'float' if 'float' in (left_type, right_type) else 'int'
            if node.operator == '+' and left_type == 'string' and right_type == 'string':
                return 'string'
            return 'any'

        # Comparison operators
        if node.operator in ('==', '!=', '<', '>', '<=', '>='):
            return 'bool'

        # Logical operators
        if node.operator in ('and', 'or'):
            return 'bool'

        return 'any'

    def visit_UnaryOp(self, node: UnaryOp) -> str:
        operand_type = self.visit(node.operand)

        if node.operator == '-':
            if operand_type in ('int', 'float'):
                return operand_type
            return 'any'

        if node.operator == 'not':
            return 'bool'

        return 'any'

    def visit_CallExpression(self, node: CallExpression) -> str:
        # Get function name
        func_name = node.function if isinstance(node.function, str) else None
        if func_name is None and isinstance(node.function, Identifier):
            func_name = node.function.name

        if func_name is None:
            # Higher-order function call
            for arg in node.arguments:
                self.visit(arg)
            return 'any'

        # Look up function
        symbol = self.current_scope.lookup(func_name)
        if symbol is None:
            self.error(f"Undefined function '{func_name}'", node.location)
            return 'any'

        if symbol.symbol_type not in ('function', 'builtin'):
            self.error(f"'{func_name}' is not a function", node.location)
            return 'any'

        # Check argument count for builtins
        if symbol.params:
            expected = len(symbol.params)
            got = len(node.arguments)
            if got != expected:
                self.error(
                    f"Function '{func_name}' expects {expected} arguments, got {got}",
                    node.location
                )

        # Analyze arguments
        for arg in node.arguments:
            self.visit(arg)

        return symbol.data_type or 'any'

    def visit_IndexExpression(self, node: IndexExpression) -> str:
        array_type = self.visit(node.array)
        index_type = self.visit(node.index)

        if array_type not in ('array', 'string', 'any'):
            self.warn(f"Index expression on non-indexable type '{array_type}'")

        if index_type not in ('int', 'any'):
            self.warn(f"Array index should be integer, got '{index_type}'")

        return 'any'

    def visit_MemberExpression(self, node: MemberExpression) -> str:
        self.visit(node.object)
        return 'any'

    def visit_QuantumExpression(self, node: QuantumExpression) -> str:
        for arg in node.arguments:
            self.visit(arg)

        # Return types for quantum operations
        return_types = {
            'superpose': 'qubit',
            'measure': 'int',
            'entangle': 'nil',
            'hadamard': 'qubit',
            'cnot': 'nil',
            'phase': 'qubit',
        }

        return return_types.get(node.operation, 'any')

    def generic_visit(self, node: ASTNode) -> str:
        """Default visitor."""
        return 'any'
