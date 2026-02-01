"""
Copyright © 2026 Rohan Date

Utils: This is a file that contains utility functions for `scrypt`

Methods:
    - `apply_*_gate`: Apply different types of quantum gates (single qubit, rotation, etc.)
    - `randlist`: Generate a random list of integers of length `n` from `a` to `b`
    - `generate_distinct_qubit_set`: Generate a list of distinct qubits
    - `create_qc`: Generate a random quantum circuit
    - `generate_observables`: Generate `n_observables` different observables of length `n_qubits`
    - `convert_to_isa_circuit`: Converts a high-level quantum circuit into an ISA circuit
    - `construct_backend`: Runs a job with backend `backend`, observables `observables`, and ISA circuit `isa_circuit`

The last 4 methods are the core of the `scrngV2` function.

Note: This is an internal module, please do not use these functions directly
"""

import random

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime import EstimatorV2 as Estimator


class ScryptError(Exception):
    """An error specific to this package."""


def apply_single_gate(gate, n_qubits: int, conditions: list[int]) -> None:
    for i in range(n_qubits):
        if conditions[i] == 1:
            gate(i)
        elif conditions[i] == 0:
            pass


def apply_r_gate(gate, n_qubits: int, conditions: list[int], rotations: list) -> None:
    for i in range(n_qubits):
        if conditions[i] == 1:
            gate(rotations[i], i)
        elif conditions[i] == 0:
            pass


def apply_two_qubit_gate(
    gate, n_qubits: int, conditions: list[int], qubits_to_apply: list[list[int]]
) -> None:
    for i in range(n_qubits):
        if conditions[i] == 1:
            gate(qubits_to_apply[i][0], qubits_to_apply[i][1])
        elif conditions[i] == 0:
            pass


def apply_three_qubit_gate(
    gate, n_qubits: int, conditions: list[int], qubits_to_apply: list[list[int]]
) -> None:
    for i in range(n_qubits):
        if conditions[i] == 1:
            gate(qubits_to_apply[i][0], qubits_to_apply[i][1], qubits_to_apply[i][2])
        elif conditions[i] == 0:
            pass


def randlist(a, b, n) -> list[int]:
    return [random.randint(a, b) for i in range(n)]


def generate_distinct_qubit_set(qubits: int, n: int) -> list[int]:
    qubits_list: list[int] = [random.randint(0, qubits - 1)]
    if n > qubits:
        raise ValueError(
            "You must generate less or the same number of qubits as the maximum amount."
        )
    else:
        pass
    for i in range(n - 1):
        while True:
            qubit_n: int = random.randint(0, qubits - 1)
            if qubit_n in qubits_list:
                continue
            elif qubit_n not in qubits_list:
                qubits_list.append(qubit_n)
                break
    return qubits_list


def create_qc(n: int) -> QuantumCircuit:
    gates_to_apply = [
        "x",
        "y",
        "z",
        "h",
        "s",
        "t",
        "rx",
        "ry",
        "rz",
        "cx",
        "cz",
        "swap",
        "iswap",
        "ccx",
        "cswap",
    ]
    qc = QuantumCircuit(n)
    for i in gates_to_apply:
        match i:
            case "x":
                apply_single_gate(qc.x, n, randlist(0, 1, n))
            case "y":
                apply_single_gate(qc.y, n, randlist(0, 1, n))
            case "z":
                apply_single_gate(qc.z, n, randlist(0, 1, n))
            case "h":
                apply_single_gate(qc.h, n, randlist(0, 1, n))
            case "s":
                apply_single_gate(qc.s, n, randlist(0, 1, n))
            case "t":
                apply_single_gate(qc.t, n, randlist(0, 1, n))
            case "rx":
                apply_r_gate(qc.rx, n, randlist(0, 1, n), randlist(0, 360, n))
            case "ry":
                apply_r_gate(qc.ry, n, randlist(0, 1, n), randlist(0, 360, n))
            case "rz":
                apply_r_gate(qc.rz, n, randlist(0, 1, n), randlist(0, 360, n))
            case "cx":
                apply_two_qubit_gate(
                    qc.cx,
                    n,
                    randlist(0, 1, n),
                    [generate_distinct_qubit_set(n, 2) for i in range(n)],
                )
            case "cz":
                apply_two_qubit_gate(
                    qc.cz,
                    n,
                    randlist(0, 1, n),
                    [generate_distinct_qubit_set(n, 2) for i in range(n)],
                )
            case "swap":
                apply_two_qubit_gate(
                    qc.swap,
                    n,
                    randlist(0, 1, n),
                    [generate_distinct_qubit_set(n, 2) for i in range(n)],
                )
            case "iswap":
                apply_two_qubit_gate(
                    qc.iswap,
                    n,
                    randlist(0, 1, n),
                    [generate_distinct_qubit_set(n, 2) for i in range(n)],
                )
            case "ccx":
                apply_three_qubit_gate(
                    qc.ccx,
                    n,
                    randlist(0, 1, n),
                    [generate_distinct_qubit_set(n, 3) for i in range(n)],
                )
            case "cswap":
                apply_three_qubit_gate(
                    qc.cswap,
                    n,
                    randlist(0, 1, n),
                    [generate_distinct_qubit_set(n, 3) for i in range(n)],
                )

    return qc


def generate_obeservables(n_qubits: int, n_observables: int) -> list[SparsePauliOp]:
    observables_list = [
        "I",
        "I",
        "I",
        "I",
        "I",
        "I",
        "X",
        "X",
        "X",
        "X",
        "X",
        "X",
        "Y",
        "Y",
        "Y",
        "Y",
        "Y",
        "Y",
        "Z",
        "Z",
        "Z",
        "Z",
        "Z",
        "Z",
    ]
    observables_labels = [
        "".join(random.choices(observables_list, k=n_qubits))
        for i in range(n_observables)
    ]
    observables = [SparsePauliOp(label) for label in observables_labels]
    return observables


def convert_to_isa_circuit(backend, qc: QuantumCircuit):
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)
    return isa_circuit


def run_job(backend, observables: list[SparsePauliOp], isa_circuit):
    # Construct the Estimator instance.

    estimator = Estimator(mode=backend)
    # estimator.options.resilience_level = 1
    estimator.options.default_shots = 5000  # pyright: ignore[reportAttributeAccessIssue]

    mapped_observables = [
        observable.apply_layout(isa_circuit.layout) for observable in observables
    ]

    job = estimator.run([(isa_circuit, mapped_observables)])

    return job
