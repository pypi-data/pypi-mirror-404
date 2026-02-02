import json
from typing import List, Sequence
from qiskit.circuit import Gate
from qiskit.circuit import Qubit
import pandas as pd
import numpy as np
from qiskit import QuantumCircuit
from ...schema import ClassicalDataset


class GatewayLoader(Gate):
    @staticmethod
    def get_name():
        return "Gateway Loader"
    def __init__(self, AR:Sequence[Qubit],DR:Sequence[Qubit],classical_dataseet:ClassicalDataset):
        self.AR=AR
        self.DR=DR
        num_qubits = len(AR) + len(DR)
        dataset_json = json.dumps(classical_dataseet.to_dict())
        super().__init__(name=self.get_name(), num_qubits=num_qubits,params=[])
        self.definition=QuantumCircuit(num_qubits)
        self.label=dataset_json
        self.dataset:ClassicalDataset=classical_dataseet
        self.name=self.get_name()

    @classmethod
    def from_excel(cls, file_path:str,AR:Sequence[Qubit],DR:Sequence[Qubit])->'GatewayLoader':
        dataset= ClassicalDataset.from_excel(file_path)
        if(len(AR)!=dataset.n):
            raise ValueError("Number of AR qubits must match dataset.n")
        if(len(DR)!=dataset.m):
            raise ValueError("Number of DR qubits must match dataset.m")
        return cls(AR,DR,dataset),[*AR,*DR]