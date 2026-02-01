"""
LUXBIN Standard Library Built-in Functions

Provides the standard library for the LUXBIN language including I/O,
math, string/wavelength, array, and quantum operations.
"""

import math
import random
from typing import Any, Dict, List, Callable, Optional


class LuxbinBuiltins:
    """Registry of all built-in functions available in LUXBIN programs."""

    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        self._register_all()

    def _register_all(self):
        """Register all built-in functions."""
        # I/O
        self._functions["photon_print"] = self._photon_print
        self._functions["photon_input"] = self._photon_input
        self._functions["photon_read"] = self._photon_read
        self._functions["photon_write"] = self._photon_write

        # Math
        self._functions["photon_abs"] = self._photon_abs
        self._functions["photon_sqrt"] = self._photon_sqrt
        self._functions["photon_pow"] = self._photon_pow
        self._functions["photon_sin"] = self._photon_sin
        self._functions["photon_cos"] = self._photon_cos
        self._functions["photon_tan"] = self._photon_tan
        self._functions["photon_floor"] = self._photon_floor
        self._functions["photon_ceil"] = self._photon_ceil
        self._functions["photon_round"] = self._photon_round
        self._functions["photon_min"] = self._photon_min
        self._functions["photon_max"] = self._photon_max

        # String/Wavelength
        self._functions["photon_len"] = self._photon_len
        self._functions["photon_concat"] = self._photon_concat
        self._functions["photon_slice"] = self._photon_slice
        self._functions["photon_wavelength"] = self._photon_wavelength
        self._functions["photon_char"] = self._photon_char
        self._functions["photon_upper"] = self._photon_upper
        self._functions["photon_lower"] = self._photon_lower
        self._functions["photon_to_int"] = self._photon_to_int
        self._functions["photon_to_float"] = self._photon_to_float
        self._functions["photon_to_string"] = self._photon_to_string
        self._functions["photon_to_bool"] = self._photon_to_bool

        # Array
        self._functions["photon_array"] = self._photon_array
        self._functions["photon_push"] = self._photon_push
        self._functions["photon_pop"] = self._photon_pop
        self._functions["photon_get"] = self._photon_get
        self._functions["photon_set"] = self._photon_set
        self._functions["photon_sort"] = self._photon_sort
        self._functions["photon_reverse"] = self._photon_reverse

        # Quantum
        self._functions["quantum_superpose"] = self._quantum_superpose
        self._functions["quantum_measure"] = self._quantum_measure
        self._functions["quantum_entangle"] = self._quantum_entangle
        self._functions["quantum_hadamard"] = self._quantum_hadamard
        self._functions["quantum_cnot"] = self._quantum_cnot
        self._functions["quantum_phase"] = self._quantum_phase
        self._functions["quantum_teleport"] = self._quantum_teleport

    def get(self, name: str) -> Optional[Callable]:
        """Look up a built-in function by name."""
        return self._functions.get(name)

    def is_builtin(self, name: str) -> bool:
        """Check if a name is a registered built-in."""
        return name in self._functions

    def get_all_names(self) -> List[str]:
        """Return all registered built-in function names."""
        return list(self._functions.keys())

    def call(self, name: str, args: List[Any]) -> Any:
        """Call a built-in function by name with arguments."""
        func = self._functions.get(name)
        if func is None:
            raise NameError(f"Unknown built-in function: {name}")
        return func(*args)

    # ── I/O Functions ──

    @staticmethod
    def _photon_print(*values) -> None:
        """Output values to light display (stdout)."""
        output = " ".join(str(v) for v in values)
        print(output)

    @staticmethod
    def _photon_input(prompt: str = "") -> str:
        """Read input from light sensor (stdin)."""
        return input(prompt)

    @staticmethod
    def _photon_read(path: str) -> str:
        """Read file as wavelength sequence."""
        with open(path, "r") as f:
            return f.read()

    @staticmethod
    def _photon_write(path: str, data: str) -> bool:
        """Write wavelength sequence to file."""
        with open(path, "w") as f:
            f.write(str(data))
        return True

    # ── Math Functions ──

    @staticmethod
    def _photon_abs(n) -> float:
        return abs(n)

    @staticmethod
    def _photon_sqrt(n) -> float:
        return math.sqrt(n)

    @staticmethod
    def _photon_pow(base, exp) -> float:
        return math.pow(base, exp)

    @staticmethod
    def _photon_sin(n) -> float:
        return math.sin(n)

    @staticmethod
    def _photon_cos(n) -> float:
        return math.cos(n)

    @staticmethod
    def _photon_tan(n) -> float:
        return math.tan(n)

    @staticmethod
    def _photon_floor(n) -> int:
        return math.floor(n)

    @staticmethod
    def _photon_ceil(n) -> int:
        return math.ceil(n)

    @staticmethod
    def _photon_round(n) -> int:
        return round(n)

    @staticmethod
    def _photon_min(a, b):
        return min(a, b)

    @staticmethod
    def _photon_max(a, b):
        return max(a, b)

    # ── String/Wavelength Functions ──

    @staticmethod
    def _photon_len(seq) -> int:
        return len(seq)

    @staticmethod
    def _photon_concat(a, b) -> str:
        return str(a) + str(b)

    @staticmethod
    def _photon_slice(seq, start: int, end: int):
        return seq[int(start):int(end)]

    @staticmethod
    def _photon_wavelength(char: str) -> float:
        """Get wavelength (nm) for a character using LUXBIN encoding.

        Maps visible spectrum 400-700nm across printable ASCII range.
        """
        if not char:
            return 0.0
        code = ord(char[0])
        # Map ASCII 32-126 to 400-700nm
        if 32 <= code <= 126:
            return 400.0 + (code - 32) * (300.0 / 94.0)
        return 400.0

    @staticmethod
    def _photon_char(wavelength: float) -> str:
        """Get character for a wavelength (nm)."""
        if wavelength < 400.0 or wavelength > 700.0:
            return ""
        code = int(32 + (wavelength - 400.0) * (94.0 / 300.0))
        code = max(32, min(126, code))
        return chr(code)

    @staticmethod
    def _photon_upper(s: str) -> str:
        return str(s).upper()

    @staticmethod
    def _photon_lower(s: str) -> str:
        return str(s).lower()

    @staticmethod
    def _photon_to_int(value) -> int:
        return int(value)

    @staticmethod
    def _photon_to_float(value) -> float:
        return float(value)

    @staticmethod
    def _photon_to_string(value) -> str:
        return str(value)

    @staticmethod
    def _photon_to_bool(value) -> bool:
        if isinstance(value, str):
            return len(value) > 0
        return bool(value)

    # ── Array Functions ──

    @staticmethod
    def _photon_array(size: int) -> list:
        return [None] * int(size)

    @staticmethod
    def _photon_push(arr: list, val) -> list:
        arr.append(val)
        return arr

    @staticmethod
    def _photon_pop(arr: list):
        if not arr:
            return None
        return arr.pop()

    @staticmethod
    def _photon_get(arr: list, index: int):
        return arr[int(index)]

    @staticmethod
    def _photon_set(arr: list, index: int, val) -> list:
        arr[int(index)] = val
        return arr

    @staticmethod
    def _photon_sort(arr: list) -> list:
        return sorted(arr)

    @staticmethod
    def _photon_reverse(arr: list) -> list:
        return list(reversed(arr))

    # ── Quantum Functions ──
    # These simulate quantum operations for classical hardware.
    # On photonic hardware, these map to actual quantum gates.

    @staticmethod
    def _quantum_superpose(*states) -> dict:
        """Create a superposition of the given states."""
        n = len(states)
        amplitude = 1.0 / math.sqrt(n) if n > 0 else 0.0
        return {
            "__type__": "qubit",
            "states": list(states),
            "amplitudes": [amplitude] * n,
            "measured": False,
        }

    @staticmethod
    def _quantum_measure(qubit: dict) -> int:
        """Measure a qubit, collapsing superposition."""
        if not isinstance(qubit, dict) or qubit.get("__type__") != "qubit":
            raise TypeError("quantum_measure requires a qubit")
        states = qubit["states"]
        amplitudes = qubit["amplitudes"]
        # Probability proportional to |amplitude|^2
        probs = [abs(a) ** 2 for a in amplitudes]
        total = sum(probs)
        if total == 0:
            return 0
        probs = [p / total for p in probs]
        result = random.choices(states, weights=probs, k=1)[0]
        qubit["measured"] = True
        qubit["result"] = result
        return result

    @staticmethod
    def _quantum_entangle(q1: dict, q2: dict) -> None:
        """Entangle two qubits."""
        if not isinstance(q1, dict) or not isinstance(q2, dict):
            raise TypeError("quantum_entangle requires two qubits")
        # Mark entanglement (simulation)
        entangle_id = id(q1) ^ id(q2)
        q1["entangled_with"] = entangle_id
        q2["entangled_with"] = entangle_id

    @staticmethod
    def _quantum_hadamard(q: dict) -> dict:
        """Apply Hadamard gate to a qubit."""
        if not isinstance(q, dict) or q.get("__type__") != "qubit":
            raise TypeError("quantum_hadamard requires a qubit")
        inv_sqrt2 = 1.0 / math.sqrt(2)
        return {
            "__type__": "qubit",
            "states": [0, 1],
            "amplitudes": [inv_sqrt2, inv_sqrt2],
            "measured": False,
        }

    @staticmethod
    def _quantum_cnot(control: dict, target: dict) -> None:
        """Apply CNOT gate (simulated)."""
        pass

    @staticmethod
    def _quantum_phase(q: dict, angle: float) -> dict:
        """Apply phase rotation to a qubit."""
        if not isinstance(q, dict) or q.get("__type__") != "qubit":
            raise TypeError("quantum_phase requires a qubit")
        result = dict(q)
        result["amplitudes"] = [
            a * complex(math.cos(angle), math.sin(angle))
            for a in q["amplitudes"]
        ]
        return result

    @staticmethod
    def _quantum_teleport(q: dict, dest) -> bool:
        """Quantum teleportation (simulated)."""
        if not isinstance(q, dict) or q.get("__type__") != "qubit":
            return False
        return True


# Module-level BUILTINS dict expected by the VM: {name: (callable, num_args)}
_instance = LuxbinBuiltins()
BUILTINS = {
    # I/O
    "photon_print": (_instance._photon_print, -1),
    "photon_input": (_instance._photon_input, 1),
    "photon_read": (_instance._photon_read, 1),
    "photon_write": (_instance._photon_write, 2),
    # Math
    "photon_abs": (_instance._photon_abs, 1),
    "photon_sqrt": (_instance._photon_sqrt, 1),
    "photon_pow": (_instance._photon_pow, 2),
    "photon_sin": (_instance._photon_sin, 1),
    "photon_cos": (_instance._photon_cos, 1),
    "photon_tan": (_instance._photon_tan, 1),
    "photon_floor": (_instance._photon_floor, 1),
    "photon_ceil": (_instance._photon_ceil, 1),
    "photon_round": (_instance._photon_round, 1),
    "photon_min": (_instance._photon_min, 2),
    "photon_max": (_instance._photon_max, 2),
    # String/Wavelength
    "photon_len": (_instance._photon_len, 1),
    "photon_concat": (_instance._photon_concat, 2),
    "photon_slice": (_instance._photon_slice, 3),
    "photon_wavelength": (_instance._photon_wavelength, 1),
    "photon_char": (_instance._photon_char, 1),
    "photon_upper": (_instance._photon_upper, 1),
    "photon_lower": (_instance._photon_lower, 1),
    "photon_to_int": (_instance._photon_to_int, 1),
    "photon_to_float": (_instance._photon_to_float, 1),
    "photon_to_string": (_instance._photon_to_string, 1),
    "photon_to_bool": (_instance._photon_to_bool, 1),
    # Array
    "photon_array": (_instance._photon_array, 1),
    "photon_push": (_instance._photon_push, 2),
    "photon_pop": (_instance._photon_pop, 1),
    "photon_get": (_instance._photon_get, 2),
    "photon_set": (_instance._photon_set, 3),
    "photon_sort": (_instance._photon_sort, 1),
    "photon_reverse": (_instance._photon_reverse, 1),
    # Quantum
    "quantum_superpose": (_instance._quantum_superpose, -1),
    "quantum_measure": (_instance._quantum_measure, 1),
    "quantum_entangle": (_instance._quantum_entangle, 2),
    "quantum_hadamard": (_instance._quantum_hadamard, 1),
    "quantum_cnot": (_instance._quantum_cnot, 2),
    "quantum_phase": (_instance._quantum_phase, 2),
    "quantum_teleport": (_instance._quantum_teleport, 2),
}
