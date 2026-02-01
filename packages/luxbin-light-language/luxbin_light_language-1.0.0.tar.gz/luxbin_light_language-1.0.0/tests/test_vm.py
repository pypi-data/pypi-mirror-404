"""Tests for the LUXBIN Virtual Machine."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luxbin_compiler.codegen import Opcode
from luxbin_compiler.vm import LuxbinVM


class TestVMStack:
    def test_push_pop(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 42),
            (Opcode.PUSH, 10),
            Opcode.POP,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 42

    def test_dup(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 42),
            Opcode.DUP,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert len(vm.stack) >= 2
        assert vm.stack[-1] == 42
        assert vm.stack[-2] == 42

    def test_swap(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 1),
            (Opcode.PUSH, 2),
            Opcode.SWAP,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 1
        assert vm.stack[-2] == 2


class TestVMArithmetic:
    def test_add(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 3),
            (Opcode.PUSH, 4),
            Opcode.ADD,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 7

    def test_sub(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 10),
            (Opcode.PUSH, 3),
            Opcode.SUB,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 7

    def test_mul(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 6),
            (Opcode.PUSH, 7),
            Opcode.MUL,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 42

    def test_div(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 10),
            (Opcode.PUSH, 2),
            Opcode.DIV,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 5.0

    def test_mod(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 10),
            (Opcode.PUSH, 3),
            Opcode.MOD,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 1


class TestVMComparison:
    def test_equal_true(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 5),
            (Opcode.PUSH, 5),
            Opcode.EQ,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] is True

    def test_equal_false(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 5),
            (Opcode.PUSH, 3),
            Opcode.EQ,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] is False

    def test_less_than(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 3),
            (Opcode.PUSH, 5),
            Opcode.LT,
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] is True


class TestVMJumps:
    def test_unconditional_jump(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.JMP, 3),       # 0: jump to index 3
            (Opcode.PUSH, 999),    # 1: skipped
            Opcode.HALT,           # 2: skipped
            (Opcode.PUSH, 42),     # 3: land here
            Opcode.HALT,           # 4: stop
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 42

    def test_jump_if_zero(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 0),     # false/zero
            (Opcode.JZ, 4),       # jump to 4 if zero
            (Opcode.PUSH, 999),   # skipped
            Opcode.HALT,
            (Opcode.PUSH, 42),    # land here
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 42


class TestVMVariables:
    def test_global_store_load(self):
        vm = LuxbinVM()
        bytecode = [
            (Opcode.PUSH, 42),
            (Opcode.GSTORE, "x"),
            (Opcode.GLOAD, "x"),
            Opcode.HALT,
        ]
        vm.execute(bytecode)
        assert vm.stack[-1] == 42
