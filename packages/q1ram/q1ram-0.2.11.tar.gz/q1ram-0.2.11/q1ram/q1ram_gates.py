from typing import List, Sequence
from qiskit.circuit import Gate
from qiskit.circuit import Qubit
import pandas as pd
import numpy as np

from .circuit import Q1RAM



class Q1RAM_Operator(Gate):
    def __init__(self, q1ram:Q1RAM,name="Q1RAM Operator"):
        self.q1ram=q1ram
        num_qubits = 2*(self.q1ram.qr_AR.size + self.q1ram.qr_DR.size)+1
        super().__init__(name=name, num_qubits=num_qubits,params=[])
        self.name="Read"

    @classmethod
    def apply(cls, qram:Q1RAM)->'Q1RAM_Operator':
        return cls(qram),[*qram.qr_A,*qram.qr_D,*qram.qr_dq,*qram.qr_AR,*qram.qr_DR]
    
class Q1RAM_Read(Q1RAM_Operator):
    def __init__(self, q1ram:Q1RAM, name="Read"):
        super().__init__(q1ram, name)

class Q1RAM_Write(Q1RAM_Operator):
    def __init__(self, q1ram:Q1RAM, name="Write"):
        super().__init__(q1ram, name)

class Q1RAM_Replace(Q1RAM_Operator):
    def __init__(self, q1ram:Q1RAM, name="Replace"):
        super().__init__(q1ram, name)
