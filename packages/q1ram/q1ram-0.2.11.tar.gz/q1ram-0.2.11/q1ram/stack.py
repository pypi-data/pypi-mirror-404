from qiskit import (
    QuantumCircuit,
    QuantumRegister,
    AncillaRegister,
    qasm3,
    ClassicalRegister,
)
from qiskit.circuit import Qubit
import requests
import getpass
import os
from .auth import authenticate
from ...schema.models import BuildCircuitRequest, BuildCircuitReponse
from qiskit.qpy import dump, load
import io
from .circuit import Q1RAM

# API_BASE = "https://api.q1ram.com"
API_BASE = "http://0.0.0.0:8000"


# authenticate()


class Q1Stack(Q1RAM):
    def __init__(
        self,
        circuit: QuantumCircuit,
        number_address_qubits: int,
        number_data_qubits: int,
        prefix: str = "",
    ):
        super().__init__(circuit, number_address_qubits,
                         number_data_qubits, prefix)

    def push(self,
             data_value: int | list[int] = None):
        # token = os.environ.get("Q1RAM_TOKEN")
        # if not token:
        #     raise Exception("❌ No token found. Please login first.")

        # headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{self.base_url}/stack/push/",
            json={
                "number_address_bits": self.number_address_qubits,
                "number_data_bits": self.number_data_qubits,
                "data_value": data_value if isinstance(data_value, list) else None,
            },
            # headers=headers,
        )

        self.write_qasm = response.json().get("circuit")
        if not self.write_qasm:
            raise Exception("Failed to get the write circuit")
        qc_write = qasm3.loads(self.write_qasm)
        qc_write.name = "Q1Stack-Push"

        if self.qr_AR is None:
            self.qr_AR = QuantumRegister(
                self.number_address_qubits, name=self.prefix + "AR"
            )
            self.qc.add_register(self.qr_AR)

        if self.qr_DR is None:
            self.qr_DR = QuantumRegister(
                self.number_data_qubits, name=self.prefix + "DR"
            )
            self.qc.add_register(self.qr_DR)

        self.qc.append(qc_write, self.ordered_qram_qubits)

    def pop(self):
        # token = os.environ.get("Q1RAM_TOKEN")
        # if not token:
        #     raise Exception("❌ No token found. Please login first.")

        # headers = {"Authorization": f"Bearer {token}"}

        response = requests.post(
            f"{self.base_url}/stack/pop/",
            json={
                "number_address_bits": self.number_address_qubits,
                "number_data_bits": self.number_data_qubits
            },
            # headers=headers,
        )

        self.read_qasm = response.json().get("circuit")
        if not self.read_qasm:
            raise Exception("Failed to get the read circuit")
        qc_read = qasm3.loads(self.read_qasm)
        qc_read.name = "Q1Stack-Pop"

        if self.qr_AR is None:
            self.qr_AR = QuantumRegister(
                self.number_address_qubits, name=self.prefix + "AR"
            )
            self.qc.add_register(self.qr_AR)

        if self.qr_DR is None:
            self.qr_DR = QuantumRegister(
                self.number_data_qubits, name=self.prefix + "DR"
            )
            self.qc.add_register(self.qr_DR)

        self.qc.append(qc_read, self.ordered_qram_qubits)
