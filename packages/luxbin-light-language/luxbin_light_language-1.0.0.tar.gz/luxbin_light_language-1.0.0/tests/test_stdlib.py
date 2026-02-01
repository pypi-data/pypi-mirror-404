"""Tests for the LUXBIN Standard Library (builtins)."""

import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from luxbin_compiler.builtins import LuxbinBuiltins


@pytest.fixture
def builtins():
    return LuxbinBuiltins()


class TestBuiltinRegistry:
    def test_all_registered(self, builtins):
        names = builtins.get_all_names()
        assert "photon_print" in names
        assert "photon_abs" in names
        assert "quantum_superpose" in names

    def test_is_builtin(self, builtins):
        assert builtins.is_builtin("photon_print") is True
        assert builtins.is_builtin("nonexistent") is False


class TestMathBuiltins:
    def test_abs(self, builtins):
        assert builtins.call("photon_abs", [-5]) == 5

    def test_sqrt(self, builtins):
        assert builtins.call("photon_sqrt", [16]) == 4.0

    def test_pow(self, builtins):
        assert builtins.call("photon_pow", [2, 10]) == 1024.0

    def test_floor(self, builtins):
        assert builtins.call("photon_floor", [3.7]) == 3

    def test_ceil(self, builtins):
        assert builtins.call("photon_ceil", [3.2]) == 4

    def test_round(self, builtins):
        assert builtins.call("photon_round", [3.5]) == 4

    def test_min(self, builtins):
        assert builtins.call("photon_min", [3, 7]) == 3

    def test_max(self, builtins):
        assert builtins.call("photon_max", [3, 7]) == 7


class TestStringBuiltins:
    def test_len(self, builtins):
        assert builtins.call("photon_len", ["hello"]) == 5

    def test_concat(self, builtins):
        assert builtins.call("photon_concat", ["foo", "bar"]) == "foobar"

    def test_slice(self, builtins):
        assert builtins.call("photon_slice", ["hello", 1, 4]) == "ell"

    def test_upper(self, builtins):
        assert builtins.call("photon_upper", ["hello"]) == "HELLO"

    def test_lower(self, builtins):
        assert builtins.call("photon_lower", ["HELLO"]) == "hello"

    def test_wavelength_roundtrip(self, builtins):
        ch = "A"
        wl = builtins.call("photon_wavelength", [ch])
        result = builtins.call("photon_char", [wl])
        assert result == ch


class TestArrayBuiltins:
    def test_array_create(self, builtins):
        arr = builtins.call("photon_array", [5])
        assert len(arr) == 5

    def test_push_pop(self, builtins):
        arr = []
        builtins.call("photon_push", [arr, 42])
        assert arr == [42]
        val = builtins.call("photon_pop", [arr])
        assert val == 42
        assert arr == []

    def test_get_set(self, builtins):
        arr = [1, 2, 3]
        assert builtins.call("photon_get", [arr, 1]) == 2
        builtins.call("photon_set", [arr, 1, 99])
        assert arr[1] == 99

    def test_sort(self, builtins):
        result = builtins.call("photon_sort", [[3, 1, 2]])
        assert result == [1, 2, 3]

    def test_reverse(self, builtins):
        result = builtins.call("photon_reverse", [[1, 2, 3]])
        assert result == [3, 2, 1]


class TestConversionBuiltins:
    def test_to_int(self, builtins):
        assert builtins.call("photon_to_int", [3.7]) == 3

    def test_to_float(self, builtins):
        assert builtins.call("photon_to_float", [3]) == 3.0

    def test_to_string(self, builtins):
        assert builtins.call("photon_to_string", [42]) == "42"

    def test_to_bool(self, builtins):
        assert builtins.call("photon_to_bool", [1]) is True
        assert builtins.call("photon_to_bool", [0]) is False


class TestQuantumBuiltins:
    def test_superpose(self, builtins):
        q = builtins.call("quantum_superpose", [0, 1])
        assert q["__type__"] == "qubit"
        assert q["states"] == [0, 1]

    def test_measure(self, builtins):
        q = builtins.call("quantum_superpose", [0, 1])
        result = builtins.call("quantum_measure", [q])
        assert result in [0, 1]

    def test_entangle(self, builtins):
        q1 = builtins.call("quantum_superpose", [0, 1])
        q2 = builtins.call("quantum_superpose", [0, 1])
        builtins.call("quantum_entangle", [q1, q2])
        assert "entangled_with" in q1
        assert "entangled_with" in q2

    def test_hadamard(self, builtins):
        q = builtins.call("quantum_superpose", [0])
        result = builtins.call("quantum_hadamard", [q])
        assert result["states"] == [0, 1]
