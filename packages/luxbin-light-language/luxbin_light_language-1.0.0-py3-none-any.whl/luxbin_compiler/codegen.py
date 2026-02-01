"""
LUXBIN Code Generator

Generates LUXBIN bytecode from the AST.

Bytecode format:
- Magic: "LUXC" (4 bytes)
- Version: uint16
- Flags: uint16
- Constants offset: uint32
- Code offset: uint32
- Constants pool
- Bytecode instructions
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import struct
from .ast_nodes import *
from .errors import LuxbinError


# Opcodes (from spec)
class Opcode:
    # Stack operations
    NOP = 0x00
    PUSH = 0x01
    POP = 0x02
    DUP = 0x03
    SWAP = 0x04

    # Arithmetic
    ADD = 0x10
    SUB = 0x11
    MUL = 0x12
    DIV = 0x13
    MOD = 0x14
    POW = 0x15
    NEG = 0x16

    # Comparison
    EQ = 0x20
    NE = 0x21
    LT = 0x22
    GT = 0x23
    LE = 0x24
    GE = 0x25

    # Logical
    AND = 0x30
    OR = 0x31
    NOT = 0x32

    # Variables
    LOAD = 0x40
    STORE = 0x41
    GLOAD = 0x42
    GSTORE = 0x43

    # Control flow
    JMP = 0x50
    JZ = 0x51
    JNZ = 0x52

    # Functions
    CALL = 0x60
    RET = 0x61
    BUILTIN = 0x62

    # Arrays
    ARRAY = 0x70
    INDEX = 0x71
    SETIDX = 0x72

    # Quantum
    QINIT = 0x80
    QSUPER = 0x81
    QMEAS = 0x82
    QENT = 0x83

    # Control
    HALT = 0xFF


@dataclass
class Instruction:
    """A bytecode instruction."""
    opcode: int
    operand: Optional[Any] = None
    location: Optional[SourceLocation] = None

    def encode(self) -> bytes:
        """Encode instruction to bytes."""
        if self.operand is None:
            return bytes([self.opcode])
        elif isinstance(self.operand, int):
            if self.operand < 256:
                return bytes([self.opcode, self.operand])
            else:
                return bytes([self.opcode]) + struct.pack('<I', self.operand)
        elif isinstance(self.operand, float):
            return bytes([self.opcode]) + struct.pack('<d', self.operand)
        elif isinstance(self.operand, str):
            encoded = self.operand.encode('utf-8')
            return bytes([self.opcode]) + struct.pack('<H', len(encoded)) + encoded
        else:
            return bytes([self.opcode])


@dataclass
class CompiledFunction:
    """A compiled function."""
    name: str
    params: List[str]
    code: List[Instruction]
    num_locals: int = 0


class CodeGenerator(ASTVisitor):
    """
    Generates LUXBIN bytecode from AST.
    """

    def __init__(self):
        self.instructions: List[Instruction] = []
        self.constants: List[Any] = []
        self.constant_map: Dict[Any, int] = {}
        self.functions: Dict[str, CompiledFunction] = {}
        self.current_function: Optional[str] = None

        # Scope tracking
        self.locals: Dict[str, int] = {}  # variable name -> local index
        self.local_count: int = 0
        self.globals: Dict[str, int] = {}  # variable name -> global index
        self.global_count: int = 0

        # Control flow
        self.loop_starts: List[int] = []
        self.loop_ends: List[List[int]] = []

    def emit(self, opcode: int, operand: Any = None, location: Optional[SourceLocation] = None):
        """Emit an instruction."""
        self.instructions.append(Instruction(opcode, operand, location))

    def emit_at(self, index: int, opcode: int, operand: Any = None):
        """Emit instruction at specific index."""
        self.instructions[index] = Instruction(opcode, operand)

    def current_address(self) -> int:
        """Get current instruction address."""
        return len(self.instructions)

    def add_constant(self, value: Any) -> int:
        """Add a constant to the pool and return its index."""
        # Check if constant already exists
        key = (type(value).__name__, value)
        if key in self.constant_map:
            return self.constant_map[key]

        index = len(self.constants)
        self.constants.append(value)
        self.constant_map[key] = index
        return index

    def define_local(self, name: str) -> int:
        """Define a local variable."""
        if name in self.locals:
            return self.locals[name]
        index = self.local_count
        self.locals[name] = index
        self.local_count += 1
        return index

    def define_global(self, name: str) -> int:
        """Define a global variable."""
        if name in self.globals:
            return self.globals[name]
        index = self.global_count
        self.globals[name] = index
        self.global_count += 1
        return index

    def lookup_variable(self, name: str) -> tuple:
        """Look up variable. Returns (is_global, index)."""
        if name in self.locals:
            return (False, self.locals[name])
        if name in self.globals:
            return (True, self.globals[name])
        # Create as global
        return (True, self.define_global(name))

    def generate(self, program: Program) -> bytes:
        """Generate bytecode from program AST."""
        self.visit(program)
        self.emit(Opcode.HALT)
        return self._encode_bytecode()

    def _encode_bytecode(self) -> bytes:
        """Encode to final bytecode format."""
        # Build constants pool
        constants_data = self._encode_constants()

        # Build code section
        code_data = b''.join(inst.encode() for inst in self.instructions)

        # Build header
        header = b'LUXC'  # Magic
        header += struct.pack('<H', 1)  # Version 1
        header += struct.pack('<H', 0)  # Flags
        header += struct.pack('<I', 16)  # Constants offset (after header)
        header += struct.pack('<I', 16 + len(constants_data))  # Code offset

        return header + constants_data + code_data

    def _encode_constants(self) -> bytes:
        """Encode constants pool."""
        data = struct.pack('<I', len(self.constants))

        for const in self.constants:
            if isinstance(const, int):
                data += bytes([0x01])  # Type: int
                data += struct.pack('<q', const)
            elif isinstance(const, float):
                data += bytes([0x02])  # Type: float
                data += struct.pack('<d', const)
            elif isinstance(const, str):
                encoded = const.encode('utf-8')
                data += bytes([0x03])  # Type: string
                data += struct.pack('<I', len(encoded))
                data += encoded
            elif isinstance(const, bool):
                data += bytes([0x04])  # Type: bool
                data += bytes([1 if const else 0])
            elif const is None:
                data += bytes([0x05])  # Type: nil
            elif isinstance(const, CompiledFunction):
                data += bytes([0x06])  # Type: function
                encoded_name = const.name.encode('utf-8')
                data += struct.pack('<H', len(encoded_name))
                data += encoded_name
                data += struct.pack('<H', len(const.params))
                data += struct.pack('<H', const.num_locals)
                # Encode function code
                func_code = b''.join(inst.encode() for inst in const.code)
                data += struct.pack('<I', len(func_code))
                data += func_code

        return data

    # ========================================================================
    # Visitor Methods
    # ========================================================================

    def visit_Program(self, node: Program):
        """Visit program."""
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Declaration(self, node: Declaration):
        """Visit declaration."""
        self.visit(node.value)

        if self.current_function:
            index = self.define_local(node.name)
            self.emit(Opcode.STORE, index, node.location)
        else:
            index = self.define_global(node.name)
            self.emit(Opcode.GSTORE, index, node.location)

    def visit_Assignment(self, node: Assignment):
        """Visit assignment."""
        self.visit(node.value)

        if isinstance(node.target, str):
            is_global, index = self.lookup_variable(node.target)
            if is_global:
                self.emit(Opcode.GSTORE, index, node.location)
            else:
                self.emit(Opcode.STORE, index, node.location)
        else:
            # Index assignment: arr[idx] = value
            # Stack: value
            self.visit(node.target.array)  # Stack: value, array
            self.visit(node.target.index)  # Stack: value, array, index
            self.emit(Opcode.SETIDX, location=node.location)

    def visit_IfStatement(self, node: IfStatement):
        """Visit if statement."""
        self.visit(node.condition)

        # Jump to else/end if false
        jz_addr = self.current_address()
        self.emit(Opcode.JZ, 0)  # Placeholder

        # Then branch
        for stmt in node.then_body:
            self.visit(stmt)

        if node.else_body:
            # Jump over else branch
            jmp_addr = self.current_address()
            self.emit(Opcode.JMP, 0)  # Placeholder

            # Patch JZ to here
            self.emit_at(jz_addr, Opcode.JZ, self.current_address())

            # Else branch
            for stmt in node.else_body:
                self.visit(stmt)

            # Patch JMP to here
            self.emit_at(jmp_addr, Opcode.JMP, self.current_address())
        else:
            # Patch JZ to here
            self.emit_at(jz_addr, Opcode.JZ, self.current_address())

    def visit_WhileStatement(self, node: WhileStatement):
        """Visit while loop."""
        loop_start = self.current_address()
        self.loop_starts.append(loop_start)
        self.loop_ends.append([])

        self.visit(node.condition)

        jz_addr = self.current_address()
        self.emit(Opcode.JZ, 0)  # Placeholder for loop exit

        for stmt in node.body:
            self.visit(stmt)

        self.emit(Opcode.JMP, loop_start)

        loop_end = self.current_address()
        self.emit_at(jz_addr, Opcode.JZ, loop_end)

        # Patch break statements
        for break_addr in self.loop_ends.pop():
            self.emit_at(break_addr, Opcode.JMP, loop_end)

        self.loop_starts.pop()

    def visit_ForStatement(self, node: ForStatement):
        """Visit for loop."""
        # Evaluate iterable
        self.visit(node.iterable)

        # Initialize index
        index_var = self.define_local(f"__for_idx_{self.local_count}")
        self.emit(Opcode.PUSH, self.add_constant(0))
        self.emit(Opcode.STORE, index_var)

        # Store iterable
        iter_var = self.define_local(f"__for_iter_{self.local_count}")
        self.emit(Opcode.STORE, iter_var)

        # Loop start
        loop_start = self.current_address()
        self.loop_starts.append(loop_start)
        self.loop_ends.append([])

        # Check index < length
        self.emit(Opcode.LOAD, index_var)
        self.emit(Opcode.LOAD, iter_var)
        self.emit(Opcode.BUILTIN, self.add_constant("photon_len"))
        self.emit(Opcode.LT)

        jz_addr = self.current_address()
        self.emit(Opcode.JZ, 0)

        # Get current element
        loop_var = self.define_local(node.variable)
        self.emit(Opcode.LOAD, iter_var)
        self.emit(Opcode.LOAD, index_var)
        self.emit(Opcode.INDEX)
        self.emit(Opcode.STORE, loop_var)

        # Body
        for stmt in node.body:
            self.visit(stmt)

        # Increment index
        self.emit(Opcode.LOAD, index_var)
        self.emit(Opcode.PUSH, self.add_constant(1))
        self.emit(Opcode.ADD)
        self.emit(Opcode.STORE, index_var)

        self.emit(Opcode.JMP, loop_start)

        loop_end = self.current_address()
        self.emit_at(jz_addr, Opcode.JZ, loop_end)

        for break_addr in self.loop_ends.pop():
            self.emit_at(break_addr, Opcode.JMP, loop_end)

        self.loop_starts.pop()

    def visit_FunctionDef(self, node: FunctionDef):
        """Visit function definition."""
        # Save current state
        saved_instructions = self.instructions
        saved_locals = self.locals
        saved_local_count = self.local_count
        saved_function = self.current_function

        # Start new function
        self.instructions = []
        self.locals = {}
        self.local_count = 0
        self.current_function = node.name

        # Define parameters as locals
        for param in node.params:
            self.define_local(param)

        # Compile body
        for stmt in node.body:
            self.visit(stmt)

        # Add implicit return nil
        self.emit(Opcode.PUSH, self.add_constant(None))
        self.emit(Opcode.RET)

        # Create compiled function
        func = CompiledFunction(
            name=node.name,
            params=node.params,
            code=self.instructions,
            num_locals=self.local_count
        )

        # Restore state
        self.instructions = saved_instructions
        self.locals = saved_locals
        self.local_count = saved_local_count
        self.current_function = saved_function

        # Store function in constants and define globally
        func_index = self.add_constant(func)
        self.define_global(node.name)
        self.emit(Opcode.PUSH, func_index)
        global_idx = self.globals[node.name]
        self.emit(Opcode.GSTORE, global_idx)

    def visit_ReturnStatement(self, node: ReturnStatement):
        """Visit return statement."""
        if node.value:
            self.visit(node.value)
        else:
            self.emit(Opcode.PUSH, self.add_constant(None))
        self.emit(Opcode.RET)

    def visit_BreakStatement(self, node: BreakStatement):
        """Visit break statement."""
        if self.loop_ends:
            break_addr = self.current_address()
            self.emit(Opcode.JMP, 0)  # Placeholder
            self.loop_ends[-1].append(break_addr)

    def visit_ContinueStatement(self, node: ContinueStatement):
        """Visit continue statement."""
        if self.loop_starts:
            self.emit(Opcode.JMP, self.loop_starts[-1])

    def visit_QuantumBlock(self, node: QuantumBlock):
        """Visit quantum block."""
        for stmt in node.body:
            self.visit(stmt)

    def visit_ImportStatement(self, node: ImportStatement):
        """Visit import statement."""
        # Push module name
        self.emit(Opcode.PUSH, self.add_constant(node.module))
        self.emit(Opcode.BUILTIN, self.add_constant("__import__"))
        if node.alias:
            index = self.define_global(node.alias)
        else:
            index = self.define_global(node.module)
        self.emit(Opcode.GSTORE, index)

    def visit_ExportStatement(self, node: ExportStatement):
        """Visit export statement."""
        # Export is a compile-time directive, no bytecode needed
        pass

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        """Visit expression statement."""
        self.visit(node.expression)
        self.emit(Opcode.POP)  # Discard result

    # ========================================================================
    # Expression Visitors
    # ========================================================================

    def visit_IntegerLiteral(self, node: IntegerLiteral):
        index = self.add_constant(node.value)
        self.emit(Opcode.PUSH, index, node.location)

    def visit_FloatLiteral(self, node: FloatLiteral):
        index = self.add_constant(node.value)
        self.emit(Opcode.PUSH, index, node.location)

    def visit_StringLiteral(self, node: StringLiteral):
        index = self.add_constant(node.value)
        self.emit(Opcode.PUSH, index, node.location)

    def visit_BooleanLiteral(self, node: BooleanLiteral):
        index = self.add_constant(node.value)
        self.emit(Opcode.PUSH, index, node.location)

    def visit_NilLiteral(self, node: NilLiteral):
        index = self.add_constant(None)
        self.emit(Opcode.PUSH, index, node.location)

    def visit_ArrayLiteral(self, node: ArrayLiteral):
        for elem in node.elements:
            self.visit(elem)
        self.emit(Opcode.ARRAY, len(node.elements), node.location)

    def visit_Identifier(self, node: Identifier):
        is_global, index = self.lookup_variable(node.name)
        if is_global:
            self.emit(Opcode.GLOAD, index, node.location)
        else:
            self.emit(Opcode.LOAD, index, node.location)

    def visit_BinaryOp(self, node: BinaryOp):
        self.visit(node.left)
        self.visit(node.right)

        ops = {
            '+': Opcode.ADD, '-': Opcode.SUB, '*': Opcode.MUL,
            '/': Opcode.DIV, '%': Opcode.MOD, '^': Opcode.POW,
            '==': Opcode.EQ, '!=': Opcode.NE,
            '<': Opcode.LT, '>': Opcode.GT,
            '<=': Opcode.LE, '>=': Opcode.GE,
            'and': Opcode.AND, 'or': Opcode.OR,
        }

        if node.operator in ops:
            self.emit(ops[node.operator], location=node.location)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.operand)

        if node.operator == '-':
            self.emit(Opcode.NEG, location=node.location)
        elif node.operator == 'not':
            self.emit(Opcode.NOT, location=node.location)

    def visit_CallExpression(self, node: CallExpression):
        # Push arguments
        for arg in node.arguments:
            self.visit(arg)

        func_name = node.function if isinstance(node.function, str) else None
        if func_name is None and hasattr(node.function, 'name'):
            func_name = node.function.name

        # Check if it's a builtin
        from .analyzer import SemanticAnalyzer
        if func_name and func_name in SemanticAnalyzer.BUILTINS:
            name_index = self.add_constant(func_name)
            self.emit(Opcode.BUILTIN, name_index, node.location)
        else:
            # User-defined function
            if func_name:
                is_global, index = self.lookup_variable(func_name)
                if is_global:
                    self.emit(Opcode.GLOAD, index)
                else:
                    self.emit(Opcode.LOAD, index)
            else:
                self.visit(node.function)
            self.emit(Opcode.CALL, len(node.arguments), node.location)

    def visit_IndexExpression(self, node: IndexExpression):
        self.visit(node.array)
        self.visit(node.index)
        self.emit(Opcode.INDEX, location=node.location)

    def visit_MemberExpression(self, node: MemberExpression):
        self.visit(node.object)
        member_index = self.add_constant(node.member)
        self.emit(Opcode.PUSH, member_index)
        self.emit(Opcode.INDEX)

    def visit_QuantumExpression(self, node: QuantumExpression):
        # Push arguments
        for arg in node.arguments:
            self.visit(arg)

        # Map quantum operations to opcodes
        ops = {
            'superpose': Opcode.QSUPER,
            'measure': Opcode.QMEAS,
            'entangle': Opcode.QENT,
        }

        if node.operation in ops:
            self.emit(ops[node.operation], len(node.arguments), node.location)
        else:
            # Use builtin for other quantum operations
            name_index = self.add_constant(f"quantum_{node.operation}")
            self.emit(Opcode.BUILTIN, name_index, node.location)

    def generic_visit(self, node: ASTNode):
        """Default visitor."""
        pass
