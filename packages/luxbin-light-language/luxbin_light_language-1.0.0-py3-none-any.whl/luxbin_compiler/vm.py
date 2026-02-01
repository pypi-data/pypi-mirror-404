"""
LUXBIN Virtual Machine

A stack-based virtual machine for executing LUXBIN bytecode.

Features:
- Stack-based execution
- Global and local variable scopes
- Function calls with call stack
- Garbage collection
- Quantum operation simulation
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import struct
import math
import random
from .codegen import Opcode, CompiledFunction
from .builtins import BUILTINS
from .errors import (
    RuntimeError, DivisionByZeroError, IndexError as LuxbinIndexError,
    StackOverflowError, QuantumError
)


@dataclass
class CallFrame:
    """A call frame on the call stack."""
    function: CompiledFunction
    ip: int  # Instruction pointer
    bp: int  # Base pointer (stack base for this frame)
    locals: List[Any] = field(default_factory=list)


@dataclass
class Qubit:
    """Simulated qubit for quantum operations."""
    state: List[complex]  # Amplitude for |0⟩ and |1⟩
    entangled_with: Optional['Qubit'] = None

    def __init__(self, initial: int = 0):
        if initial == 0:
            self.state = [complex(1, 0), complex(0, 0)]
        else:
            self.state = [complex(0, 0), complex(1, 0)]

    def probability_zero(self) -> float:
        """Probability of measuring 0."""
        return abs(self.state[0]) ** 2

    def probability_one(self) -> float:
        """Probability of measuring 1."""
        return abs(self.state[1]) ** 2


class LuxbinVM:
    """
    LUXBIN Virtual Machine.

    Executes LUXBIN bytecode with a stack-based architecture.
    """

    MAX_STACK_SIZE = 10000
    MAX_CALL_DEPTH = 1000

    def __init__(self):
        self.stack: List[Any] = []
        self.globals: Dict[int, Any] = {}
        self.call_stack: List[CallFrame] = []
        self.constants: List[Any] = []
        self.code: bytes = b''
        self.ip: int = 0  # Instruction pointer
        self.running: bool = False
        self.output: List[str] = []

    def push(self, value: Any):
        """Push value onto stack."""
        if len(self.stack) >= self.MAX_STACK_SIZE:
            raise StackOverflowError()
        self.stack.append(value)

    def pop(self) -> Any:
        """Pop value from stack."""
        if not self.stack:
            raise RuntimeError("Stack underflow")
        return self.stack.pop()

    def peek(self, offset: int = 0) -> Any:
        """Peek at stack value without popping."""
        if offset >= len(self.stack):
            raise RuntimeError("Stack underflow")
        return self.stack[-(offset + 1)]

    def read_byte(self) -> int:
        """Read a byte from bytecode."""
        if self.ip >= len(self.code):
            return Opcode.HALT
        byte = self.code[self.ip]
        self.ip += 1
        return byte

    def read_uint16(self) -> int:
        """Read a 16-bit unsigned integer."""
        data = self.code[self.ip:self.ip + 2]
        self.ip += 2
        return struct.unpack('<H', data)[0]

    def read_uint32(self) -> int:
        """Read a 32-bit unsigned integer."""
        data = self.code[self.ip:self.ip + 4]
        self.ip += 4
        return struct.unpack('<I', data)[0]

    def load_bytecode(self, bytecode: bytes):
        """Load bytecode into VM."""
        # Parse header
        if bytecode[:4] != b'LUXC':
            raise RuntimeError("Invalid bytecode: bad magic")

        version = struct.unpack('<H', bytecode[4:6])[0]
        flags = struct.unpack('<H', bytecode[6:8])[0]
        const_offset = struct.unpack('<I', bytecode[8:12])[0]
        code_offset = struct.unpack('<I', bytecode[12:16])[0]

        # Load constants
        self._load_constants(bytecode[const_offset:code_offset])

        # Load code
        self.code = bytecode[code_offset:]
        self.ip = 0

    def _load_constants(self, data: bytes):
        """Load constants pool from bytecode."""
        self.constants = []
        pos = 0

        count = struct.unpack('<I', data[pos:pos + 4])[0]
        pos += 4

        for _ in range(count):
            const_type = data[pos]
            pos += 1

            if const_type == 0x01:  # int
                value = struct.unpack('<q', data[pos:pos + 8])[0]
                pos += 8
                self.constants.append(value)

            elif const_type == 0x02:  # float
                value = struct.unpack('<d', data[pos:pos + 8])[0]
                pos += 8
                self.constants.append(value)

            elif const_type == 0x03:  # string
                length = struct.unpack('<I', data[pos:pos + 4])[0]
                pos += 4
                value = data[pos:pos + length].decode('utf-8')
                pos += length
                self.constants.append(value)

            elif const_type == 0x04:  # bool
                value = data[pos] != 0
                pos += 1
                self.constants.append(value)

            elif const_type == 0x05:  # nil
                self.constants.append(None)

            elif const_type == 0x06:  # function
                name_len = struct.unpack('<H', data[pos:pos + 2])[0]
                pos += 2
                name = data[pos:pos + name_len].decode('utf-8')
                pos += name_len

                num_params = struct.unpack('<H', data[pos:pos + 2])[0]
                pos += 2
                num_locals = struct.unpack('<H', data[pos:pos + 2])[0]
                pos += 2

                code_len = struct.unpack('<I', data[pos:pos + 4])[0]
                pos += 4
                func_code = data[pos:pos + code_len]
                pos += code_len

                func = CompiledFunction(
                    name=name,
                    params=[f"arg{i}" for i in range(num_params)],
                    code=[],
                    num_locals=num_locals
                )
                func._bytecode = func_code  # Store raw bytecode
                self.constants.append(func)

    def execute(self, bytecode: bytes) -> Any:
        """Execute bytecode and return result."""
        self.load_bytecode(bytecode)
        return self.run()

    def run(self) -> Any:
        """Run the VM until halt."""
        self.running = True

        while self.running:
            opcode = self.read_byte()
            self._execute_instruction(opcode)

        return self.stack[-1] if self.stack else None

    def _execute_instruction(self, opcode: int):
        """Execute a single instruction."""

        if opcode == Opcode.NOP:
            pass

        elif opcode == Opcode.PUSH:
            index = self.read_byte()
            if index >= len(self.constants):
                # Try reading as 32-bit
                self.ip -= 1
                index = self.read_uint32()
            self.push(self.constants[index])

        elif opcode == Opcode.POP:
            self.pop()

        elif opcode == Opcode.DUP:
            self.push(self.peek())

        elif opcode == Opcode.SWAP:
            a = self.pop()
            b = self.pop()
            self.push(a)
            self.push(b)

        # Arithmetic
        elif opcode == Opcode.ADD:
            b = self.pop()
            a = self.pop()
            if isinstance(a, str) and isinstance(b, str):
                self.push(a + b)
            elif isinstance(a, list) and isinstance(b, list):
                self.push(a + b)
            else:
                self.push(a + b)

        elif opcode == Opcode.SUB:
            b = self.pop()
            a = self.pop()
            self.push(a - b)

        elif opcode == Opcode.MUL:
            b = self.pop()
            a = self.pop()
            self.push(a * b)

        elif opcode == Opcode.DIV:
            b = self.pop()
            a = self.pop()
            if b == 0:
                raise DivisionByZeroError()
            self.push(a / b)

        elif opcode == Opcode.MOD:
            b = self.pop()
            a = self.pop()
            if b == 0:
                raise DivisionByZeroError()
            self.push(a % b)

        elif opcode == Opcode.POW:
            b = self.pop()
            a = self.pop()
            self.push(a ** b)

        elif opcode == Opcode.NEG:
            a = self.pop()
            self.push(-a)

        # Comparison
        elif opcode == Opcode.EQ:
            b = self.pop()
            a = self.pop()
            self.push(a == b)

        elif opcode == Opcode.NE:
            b = self.pop()
            a = self.pop()
            self.push(a != b)

        elif opcode == Opcode.LT:
            b = self.pop()
            a = self.pop()
            self.push(a < b)

        elif opcode == Opcode.GT:
            b = self.pop()
            a = self.pop()
            self.push(a > b)

        elif opcode == Opcode.LE:
            b = self.pop()
            a = self.pop()
            self.push(a <= b)

        elif opcode == Opcode.GE:
            b = self.pop()
            a = self.pop()
            self.push(a >= b)

        # Logical
        elif opcode == Opcode.AND:
            b = self.pop()
            a = self.pop()
            self.push(bool(a) and bool(b))

        elif opcode == Opcode.OR:
            b = self.pop()
            a = self.pop()
            self.push(bool(a) or bool(b))

        elif opcode == Opcode.NOT:
            a = self.pop()
            self.push(not bool(a))

        # Variables
        elif opcode == Opcode.LOAD:
            index = self.read_byte()
            if self.call_stack:
                frame = self.call_stack[-1]
                if index < len(frame.locals):
                    self.push(frame.locals[index])
                else:
                    self.push(None)
            else:
                self.push(None)

        elif opcode == Opcode.STORE:
            index = self.read_byte()
            value = self.pop()
            if self.call_stack:
                frame = self.call_stack[-1]
                while len(frame.locals) <= index:
                    frame.locals.append(None)
                frame.locals[index] = value
            # If no frame, silently ignore (shouldn't happen)

        elif opcode == Opcode.GLOAD:
            index = self.read_byte()
            self.push(self.globals.get(index))

        elif opcode == Opcode.GSTORE:
            index = self.read_byte()
            value = self.pop()
            self.globals[index] = value

        # Control flow
        elif opcode == Opcode.JMP:
            addr = self.read_byte()
            if addr < 256:
                self.ip = addr
            else:
                self.ip -= 1
                self.ip = self.read_uint32()

        elif opcode == Opcode.JZ:
            addr = self.read_byte()
            cond = self.pop()
            if not cond:
                self.ip = addr

        elif opcode == Opcode.JNZ:
            addr = self.read_byte()
            cond = self.pop()
            if cond:
                self.ip = addr

        # Functions
        elif opcode == Opcode.CALL:
            num_args = self.read_byte()
            func = self.pop()

            if isinstance(func, CompiledFunction):
                if len(self.call_stack) >= self.MAX_CALL_DEPTH:
                    raise StackOverflowError()

                # Get arguments
                args = [self.pop() for _ in range(num_args)]
                args.reverse()

                # Create new frame
                frame = CallFrame(
                    function=func,
                    ip=self.ip,
                    bp=len(self.stack),
                    locals=args + [None] * (func.num_locals - len(args))
                )
                self.call_stack.append(frame)

                # Execute function bytecode
                if hasattr(func, '_bytecode'):
                    saved_code = self.code
                    saved_ip = self.ip
                    self.code = func._bytecode
                    self.ip = 0

        elif opcode == Opcode.RET:
            if self.call_stack:
                frame = self.call_stack.pop()
                return_value = self.pop() if self.stack else None

                # Restore previous function's bytecode
                if len(self.call_stack) > 0:
                    # Continue in caller
                    pass
                else:
                    # Return to main program
                    pass

                self.push(return_value)
            else:
                # Return from main program
                self.running = False

        elif opcode == Opcode.BUILTIN:
            name_index = self.read_byte()
            name = self.constants[name_index]
            self._call_builtin(name)

        # Arrays
        elif opcode == Opcode.ARRAY:
            count = self.read_byte()
            elements = [self.pop() for _ in range(count)]
            elements.reverse()
            self.push(elements)

        elif opcode == Opcode.INDEX:
            index = self.pop()
            arr = self.pop()
            if isinstance(arr, (list, str)):
                if 0 <= index < len(arr):
                    self.push(arr[index])
                else:
                    raise LuxbinIndexError(index, len(arr))
            else:
                raise RuntimeError(f"Cannot index {type(arr).__name__}")

        elif opcode == Opcode.SETIDX:
            value = self.pop()
            index = self.pop()
            arr = self.pop()
            if isinstance(arr, list):
                if 0 <= index < len(arr):
                    arr[index] = value
                else:
                    raise LuxbinIndexError(index, len(arr))
            else:
                raise RuntimeError(f"Cannot set index on {type(arr).__name__}")

        # Quantum
        elif opcode == Opcode.QINIT:
            initial = self.read_byte()
            self.push(Qubit(initial))

        elif opcode == Opcode.QSUPER:
            num_states = self.read_byte()
            states = [self.pop() for _ in range(num_states)]
            states.reverse()
            qubit = Qubit()
            # Create superposition (equal probability)
            amp = 1.0 / math.sqrt(len(states))
            qubit.state = [complex(amp, 0)] * 2
            self.push(qubit)

        elif opcode == Opcode.QMEAS:
            self.read_byte()  # num args (should be 1)
            qubit = self.pop()
            if isinstance(qubit, Qubit):
                # Measure: collapse to 0 or 1 based on probability
                if random.random() < qubit.probability_zero():
                    result = 0
                    qubit.state = [complex(1, 0), complex(0, 0)]
                else:
                    result = 1
                    qubit.state = [complex(0, 0), complex(1, 0)]
                self.push(result)
            else:
                raise QuantumError("Cannot measure non-qubit")

        elif opcode == Opcode.QENT:
            self.read_byte()  # num args (should be 2)
            q2 = self.pop()
            q1 = self.pop()
            if isinstance(q1, Qubit) and isinstance(q2, Qubit):
                q1.entangled_with = q2
                q2.entangled_with = q1
                self.push(None)
            else:
                raise QuantumError("Cannot entangle non-qubits")

        elif opcode == Opcode.HALT:
            self.running = False

        else:
            raise RuntimeError(f"Unknown opcode: 0x{opcode:02x}")

    def _call_builtin(self, name: str):
        """Call a built-in function."""
        if name not in BUILTINS:
            raise RuntimeError(f"Unknown builtin: {name}")

        func, num_args = BUILTINS[name]

        if num_args == -1:
            # Variable arguments - peek to get count
            # For now, just call with available stack
            args = []
        else:
            args = [self.pop() for _ in range(num_args)]
            args.reverse()

        result = func(*args, vm=self)
        self.push(result)

    def get_output(self) -> str:
        """Get captured output."""
        return '\n'.join(self.output)
