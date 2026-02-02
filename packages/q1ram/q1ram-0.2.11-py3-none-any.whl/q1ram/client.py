import os
import requests
from typing import List, Optional, Union, Literal
import json
import getpass

# Try to import Qiskit for circuit reconstruction, but don't fail if missing
try:
    from qiskit import qasm3, QuantumCircuit
    from qiskit.circuit import Instruction, Gate
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

# Default to local for dev, or https://api.q1ram.com
DEFAULT_API_URL = "https://api.q1ram.com"


def authenticate():
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    response = requests.post(
        f"{DEFAULT_API_URL}/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        os.environ["Q1RAM_TOKEN"] = token
        print("✅ Login successful!")
    else:
        raise Exception(f"Login failed: {response.text}")


if HAS_QISKIT:
    class QRAMOperationInstruction(Instruction):
        """
        A Qiskit Instruction representing a high-level QRAM operation.
        Envelops the operation at the client side for better circuit visualization.
        """

        def __init__(self, op_type: str, num_qubits: int, params: dict):
            # Store parameters for later API retrieval
            self.op_type = op_type
            self.op_params = params

            # Format name for visualization
            visible_name = f"QRAM_{op_type}"

            super().__init__(visible_name, num_qubits, 0, [])

        def __repr__(self):
            return f"QRAMOperationInstruction(op={self.op_type}, params={self.op_params})"


class _APIClient:
    """
    Internal client for interacting with the Q1RAM V2 API.
    Handles authentication and connection details.
    """

    def __init__(self, token: Optional[str] = None, base_url: str = DEFAULT_API_URL):
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("Q1RAM_TOKEN")

        if not self.token:
            pass

    def login(self, username: str, password: str) -> str:
        """Authenticates with the API and stores the token."""
        response = requests.post(
            f"{self.base_url}/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            self.token = response.json()["access_token"]
            return "Login successful"
        else:
            raise Exception(f"Login failed: {response.text}")

    def execute_batch(self, batch_data: dict) -> 'ExecutionResult':
        """Sends a batch definition to the API and returns the result."""
        headers = {
            "Content-Type": "application/json"
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.base_url}/v2/batch/execute"
        response = requests.post(url, json=batch_data, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"Execution failed ({response.status_code}): {response.text}")

        config = batch_data.get("config", {})
        return ExecutionResult(
            response.json(),
            address_bits=config.get("address_bits", 0),
            data_bits=config.get("data_bits", 0),
            operations=batch_data.get("operations", [])
        )


class CircuitProxy:
    """
    Wraps a Qiskit QuantumCircuit to intercept gate calls.
    Allows custom gates to be batched in order when inside @q1ram_batch.
    """

    def __init__(self, qram_instance: 'Q1RAM', real_circuit: 'QuantumCircuit'):
        self._qram = qram_instance
        self._circuit = real_circuit

    _PASS_THROUGH = {
        'depth', 'size', 'width', 'count_ops', 'draw', 'qasm', 'decompose',
        'to_gate', 'to_instruction', 'copy', 'inverse', 'num_qubits', 'qubits',
        'clbits', 'num_clbits', 'data'
    }

    def __getattr__(self, name):
        # Get property or method from the real circuit
        attr = getattr(self._circuit, name)

        if not callable(attr) or name in self._PASS_THROUGH:
            return attr

        # If it's a method (likely a gate or instruction)
        def wrapper(*args, **kwargs):
            if self._qram._defer_mode:
                # Check if this is a standard gate method
                # (Simple heuristic: gate methods usually have 'h', 'x', 'cx', etc names)
                # If we are in defer mode, we record it as a GATE operation.

                # We need to flatten the qubit arguments to indices
                flat_qubits = []
                for arg in args:
                    try:
                        flat_qubits.extend(self._qram._get_indices(arg))
                    except:
                        # Fallback for non-qubit args (parameters etc)
                        pass

                self._qram._record_op(
                    "GATE", gate_name=name, qubits=flat_qubits)
                return None  # The gate is deferred
            else:
                # Immediate application to real circuit
                return attr(*args, **kwargs)

        return wrapper

    def __repr__(self):
        return self._circuit.__repr__()


class BatchContext:
    """Context manager for Q1RAM batching."""

    def __init__(self, qram: 'Q1RAM', label: str = None):
        self.qram = qram
        self.label = label
        self.prev_mode = False

    def __enter__(self):
        self.prev_mode = self.qram._defer_mode
        self.qram._defer_mode = True
        if not self.prev_mode:
            self.qram._pending_ops = []
        return self.qram

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                self.qram._flush_batch(label=self.label)
        finally:
            self.qram._defer_mode = self.prev_mode
            if not self.prev_mode:
                self.qram._pending_ops = []


class MemoryPage:
    """Represents a single page in a paged Q1RAM system."""

    def __init__(self, index: int, qram: 'Q1RAM'):
        self.index = index
        self.A = qram._get_or_create_reg(f"A{index}", qram.address_bits)
        self.PC = qram._get_or_create_reg(f"PC{index}", qram.page_bits)
        self.D = qram._get_or_create_reg(f"D{index}", qram.data_bits)
        self.dq = qram._get_or_create_reg(f"dq{index}", 1)

        # Initialize PC with the binary representation of the page index (for comparison with PR)
        if qram.page_bits > 0:
            for i in range(qram.page_bits):
                if (index >> i) & 1:
                    qram._real_circuit.x(self.PC[i])

        # Initialize A (Local Address) with Hadamard gates for superposition
        if self.A.size > 0:
            qram._real_circuit.h(self.A)


class Q1RAM:
    """
    Main Q1RAM Quantum Memory Manager.
    Maintains the quantum state (Circuit + Registers) and handles operations.
    Supports Paging via num_pages.
    """

    def __init__(self,
                 address_bits: Optional[int] = None,
                 data_bits: Optional[int] = None,
                 num_pages: int = 1,
                 num_qr: int = 0,
                 token: Optional[str] = None,
                 base_url: str = DEFAULT_API_URL,
                 circuit: Optional['QuantumCircuit'] = None,
                 **kwargs):
        import math
        # Support V1 Aliases
        self.address_bits = address_bits or kwargs.get(
            "number_address_qubits", 0)
        self.data_bits = data_bits or kwargs.get("number_data_qubits", 0)

        self.num_pages = num_pages
        self.num_qr = num_qr
        self.page_bits = math.ceil(
            math.log2(num_pages)) if num_pages > 1 else 0
        self.client = _APIClient(token, base_url)

        # Initialize Circuit and Registers
        if HAS_QISKIT:
            from qiskit import QuantumCircuit, QuantumRegister

            if circuit is not None:
                self._real_circuit = circuit
            else:
                self._real_circuit = QuantumCircuit()

            # Requested Order: QR, rw, AR, PR, DR, anc
            self.QR = []
            if num_qr > 0:
                for i in range(num_qr):
                    self.QR.append(self._get_or_create_reg(
                        f"QR{i}", self.address_bits))

            self.rw = self._get_or_create_reg("rw", 1)
            self.AR = self._get_or_create_reg("AR", self.address_bits)
            self.PR = self._get_or_create_reg(
                "PR", self.page_bits) if self.page_bits > 0 else []
            self.DR = self._get_or_create_reg("DR", self.data_bits)

            # Paging initialization
            self.pages = [MemoryPage(i, self) for i in range(num_pages)]

            # For backward compatibility and single-page use cases
            # dq, A, D, PC refer to the first page (Page 0)
            self.A = self.pages[0].A
            self.PC = self.pages[0].PC
            self.D = self.pages[0].D
            self.dq = self.pages[0].dq

            # Ancilla
            eff_addr = self.address_bits + self.page_bits
            num_anc = max(0, (eff_addr // 2) - 1)
            if num_anc > 0:
                self.anc = self._get_or_create_reg("anc", num_anc)
            else:
                self.anc = []

            self.circuit = CircuitProxy(self, self._real_circuit)
            self.qc = self._real_circuit  # Alias for V1 compatibility
        else:
            self.circuit = None
            raise ImportError("Qiskit required to use Q1RAM class.")

        # --- Deferral Logic ---
        self._pending_ops = []
        self._defer_mode = False
        self._placeholder_instructions = []

    def _get_qram_qubits(self):
        """Returns all qubits managed by this Q1RAM instance in a logical ordering for visualization."""
        all_q = []
        for qr in self.QR:
            all_q.extend(list(qr))
        all_q.extend(list(self.rw))
        all_q.extend(list(self.AR))
        if self.page_bits > 0:
            all_q.extend(list(self.PR))
        all_q.extend(list(self.DR))
        for page in self.pages:
            all_q.extend(list(page.A))
            all_q.extend(list(page.PC))
            all_q.extend(list(page.D))
            all_q.extend(list(page.dq))
        all_q.extend(list(self.anc))
        return all_q

    def _get_or_create_reg(self, name, size):
        from qiskit import QuantumRegister
        for reg in self._real_circuit.qregs:
            if reg.name == name:
                if reg.size != size:
                    raise ValueError(
                        f"Existing register '{name}' in circuit has wrong size ({reg.size} vs {size})")
                return reg
        reg = QuantumRegister(size, name)
        self._real_circuit.add_register(reg)
        return reg

    def batch(self, label: str = None):
        """Returns a context manager for batching operations."""
        return BatchContext(self, label=label)

    def _get_indices(self, reg):
        from qiskit.circuit import Qubit, QuantumRegister

        if reg is None or (isinstance(reg, list) and not reg):
            return []

        if isinstance(reg, Qubit):
            return [self._real_circuit.qubits.index(reg)]

        # If it's a list or QuantumRegister, iterate
        if isinstance(reg, (list, QuantumRegister)):
            return [self._real_circuit.qubits.index(q) for q in reg]

        # Fallback for any other iterable of qubits
        try:
            return [self._real_circuit.qubits.index(q) for q in reg]
        except:
            raise ValueError(
                f"Could not determine indices for {reg}. Expected Qubit, list, or QuantumRegister.")

    def integrate_result(self, result: 'ExecutionResult', encapsulate: bool = True, label: str = None, onto_circuit: 'QuantumCircuit' = None):
        """
        Integrates an ExecutionResult into the managed Q1RAM circuit or a provided target circuit.
        Wraps the result in a block that spans all managed QRAM qubits.
        """
        if not HAS_QISKIT:
            return

        target_qc = onto_circuit if onto_circuit is not None else self._real_circuit

        try:
            source_qc = result.to_qiskit()
            qram_qubits = self._get_qram_qubits()

            # Map source qubits to target qubits
            qubit_map = []
            name_mapping_failed = False

            for source_bit in source_qc.qubits:
                bit_loc = source_qc.find_bit(source_bit)
                if not bit_loc.registers:
                    name_mapping_failed = True
                    break

                source_reg = bit_loc.registers[0][0]
                source_idx = bit_loc.registers[0][1]
                reg_name = source_reg.name

                # Robust name matching (strip escaping/prefixes)
                clean_name = reg_name.split('_')[-1]
                if reg_name.startswith("esc_"):
                    clean_name = reg_name[4:]

                target_reg = None
                # Try match against the final real circuit registers for mapping consistency
                for r in self._real_circuit.qregs:
                    if r.name == reg_name or r.name == clean_name:
                        target_reg = r
                        break

                if target_reg and source_idx < target_reg.size:
                    qubit_map.append(target_reg[source_idx])
                else:
                    name_mapping_failed = True
                    break

            # Fallback to positional mapping if name mapping failed
            if name_mapping_failed or len(qubit_map) != len(source_qc.qubits):
                if len(source_qc.qubits) <= len(qram_qubits):
                    qubit_map = qram_qubits[:len(source_qc.qubits)]
                else:
                    # Last resort fallback: just compose it
                    target_qc.compose(source_qc, inplace=True)
                    return

            if encapsulate:
                label = label or "QRAM_op"
                # Create a wrapper circuit spanning ALL QRAM qubits for consistent box size
                wrapper_qc = QuantumCircuit(len(qram_qubits), name=label)

                # Map source bits to their relative index in the wrapper
                rel_indices = []
                for q in qubit_map:
                    try:
                        rel_indices.append(qram_qubits.index(q))
                    except ValueError:
                        pass

                if len(rel_indices) == len(source_qc.qubits):
                    # Add logic directly to the wrapper
                    wrapper_qc.compose(
                        source_qc, qubits=rel_indices, inplace=True)

                    try:
                        instr = wrapper_qc.to_gate()
                    except:
                        instr = wrapper_qc.to_instruction()

                    instr.name = label
                    target_qc.append(instr, qram_qubits)
                else:
                    target_qc.compose(
                        source_qc, qubits=qubit_map, inplace=True)
            else:
                target_qc.compose(source_qc, qubits=qubit_map, inplace=True)

        except Exception as e:
            try:
                target_qc.compose(result.to_qiskit(), inplace=True)
            except:
                pass

    def run_batch(self, batch: 'Batch', ar=None, dr=None, pr=None, label: str = None, encapsulate: bool = True, onto_circuit: 'QuantumCircuit' = None) -> 'ExecutionResult':
        """
        Executes a Batch batch and integrates it into the memory state.
        """
        if not batch.client:
            batch.client = self.client

        # Determine Register Layout
        target_ar = ar if ar is not None else self.AR
        target_dr = dr if dr is not None else self.DR
        target_pr = pr if pr is not None else self.PR

        layout = {
            "ar": self._get_indices(target_ar),
            "qr": [self._get_indices(q) for q in self.QR],
            "dr": self._get_indices(target_dr),
            "pr": self._get_indices(target_pr),
            "rw": self._get_indices(self.rw)[0],
            "anc": self._get_indices(self.anc),
            "total_qubits": self._real_circuit.num_qubits
        }

        # Handle Page configurations in layout
        pages_data = []
        for p in self.pages:
            pages_data.append({
                "index": p.index,
                "pc": self._get_indices(p.PC),
                "a": self._get_indices(p.A),
                "d": self._get_indices(p.D),
                "dq": self._get_indices(p.dq)[0]
            })
        layout["pages"] = pages_data
        layout["num_pages"] = self.num_pages
        layout["page_bits"] = self.page_bits

        # Execute with the determined layout
        result = batch.execute(layout=layout)

        # Integrate (using the pass-through parameters)
        self.integrate_result(
            result, label=label, encapsulate=encapsulate, onto_circuit=onto_circuit)

        return result

    # --- Deferral Logic ---

    def _flush_batch(self, label: str = None):
        """Executes the current pending batch."""
        if not self._pending_ops:
            return

        # print(f"DEBUG: Flushing Batch: {len(self._pending_ops)} operations")
        qram_qubits = self._get_qram_qubits()
        active_label = label or "QRAM_Batch"

        # If it's a batch and we want hierarchical boxes
        if len(self._pending_ops) > 0:
            # Batch Processing: Send ALL operations in ONE API call
            # This allows the server to optimize across operations and reduces network overhead

            # print(f"DEBUG: Flushing Batch: {len(self._pending_ops)} operations in 1 Request")

            batch = Batch(self.address_bits, self.data_bits,
                          self.num_pages, self.page_bits, self.num_qr, self.client)
            batch.operations = self._pending_ops

            # Execute as a single unit
            # If multiple ops, we encapsulate the whole sequence in a labelled block
            should_encapsulate = len(
                self._pending_ops) > 1 or label is not None
            self.run_batch(batch, label=active_label,
                           encapsulate=should_encapsulate)

        # Reset
        self._pending_ops = []

        # Reset
        self._pending_ops = []

    def _record_op(self, op_type, address=None, data=None, qr=None, qr_index=None, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        """Records an operation when in defer mode."""
        op = {"op": op_type}

        # Handle Page Splitting if address is large integer
        active_address = address
        active_page = page_index

        if isinstance(address, int) and self.page_bits > 0:
            max_addr = 1 << self.address_bits
            # Extract page from top bits ONLY if page_index was not provided
            if page_index is None:
                active_page = address >> self.address_bits
                active_address = address & (max_addr - 1)
            else:
                active_address = address  # Use as local address since page is explicit
                active_page = page_index

        if active_address is not None:
            # Map low bits (active_address) to 'address' (which maps to builder.regs.AR)
            op["address"] = active_address

        if active_page is not None:
            # Map high bits (active_page) to 'page_index' (which maps to builder.regs.PR)
            op["page_index"] = active_page
        if data is not None:
            op["data"] = data
        if qr is not None:
            op["qr"] = qr
        if qr_index is not None:
            op["qr_index"] = qr_index

        # If specific registers provided, calculate indices and attach
        if ar is not None:
            op["ar_indices"] = self._get_indices(ar)
        if dr is not None:
            op["dr_indices"] = self._get_indices(dr)
        if pr is not None:
            op["pr_indices"] = self._get_indices(pr)

        # Add any extra info (e.g. gate_name, qubits)
        op.update(kwargs)

        self._pending_ops.append(op)

        if not self._defer_mode:
            self._flush_batch(label=op["op"])

    def read(self, address=None, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        # Support V1 Aliases
        active_address = address if address is not None else kwargs.get(
            "address_value")
        active_ar = ar if ar is not None else kwargs.get("address_register")
        active_dr = dr if dr is not None else kwargs.get("data_register")

        self._record_op("READ", address=active_address, ar=active_ar,
                        dr=active_dr, pr=pr, page_index=page_index)

    def read_all(self, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        """
        Specialized read that entangles the Address Bus (A) with AR 
        using CX gates before reading.
        """
        active_ar = ar if ar is not None else kwargs.get("address_register")
        active_dr = dr if dr is not None else kwargs.get("data_register")

        self._record_op("READ_ALL", ar=active_ar, dr=active_dr,
                        pr=pr, page_index=page_index)

    def write(self, address=None, data=None, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        # Support V1 Aliases
        active_address = address if address is not None else kwargs.get(
            "address_value")
        active_data = data if data is not None else kwargs.get("data_value")
        active_ar = ar if ar is not None else kwargs.get("address_register")
        active_dr = dr if dr is not None else kwargs.get("data_register")

        self._record_op("WRITE", address=active_address, data=active_data,
                        ar=active_ar, dr=active_dr, pr=pr, page_index=page_index)

    def write_all(self, data=None, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        """
        Specialized write that entangles the Address Bus (A) with AR 
        using CX gates before writing the same data to all addresses.
        """
        active_data = data if data is not None else kwargs.get("data_value")
        self._record_op("WRITE_ALL", data=active_data, ar=ar,
                        dr=dr, pr=pr, page_index=page_index)

    def push(self, data=None, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        active_data = data if data is not None else kwargs.get("data_value")
        self._record_op("PUSH", data=active_data, ar=ar,
                        dr=dr, pr=pr, page_index=page_index)

    def pop(self, ar=None, dr=None, pr=None, page_index=None):
        self._record_op("POP", ar=ar, dr=dr, pr=pr, page_index=page_index)

    def enqueue(self, data=None, ar=None, dr=None, pr=None, page_index=None, **kwargs):
        active_data = data if data is not None else kwargs.get("data_value")
        self._record_op("ENQUEUE", data=active_data, ar=ar,
                        dr=dr, pr=pr, page_index=page_index)

    def dequeue(self, ar=None, dr=None, pr=None, page_index=None):
        self._record_op("DEQUEUE", ar=ar, dr=dr, pr=pr, page_index=page_index)

    def save_ar_to_qr(self, qr_index: int = 0):
        """Saves the state of AR into a specific QR using CX gates."""
        self._record_op("SAVE_AR_TO_QR", qr_index=qr_index)

    def restore_ar_from_qr(self, qr_index: int = 0):
        """Restores the state of AR from a specific QR using CX gates."""
        self._record_op("RESTORE_AR_FROM_QR", qr_index=qr_index)

    # --- Utility & Simulation Helpers ---
    def measure_bus(self, label: str = "BusMeasure"):
        """
        Adds measurement gates to PR, AR, and DR registers.
        Order (MSB to LSB): PR (Page Index) | AR (Local Address) | DR (Data)
        """
        if self._defer_mode:
            self._record_op("MEASURE_BUS", label=label)
            return None

        from qiskit.circuit import ClassicalRegister

        # Determine sizes
        ar_size = self.AR.size if hasattr(self.AR, 'size') else (
            len(self.AR) if isinstance(self.AR, list) else 0)
        pr_size = self.PR.size if hasattr(self.PR, 'size') else (
            len(self.PR) if isinstance(self.PR, list) else 0)
        dr_size = self.DR.size

        cr = ClassicalRegister(ar_size + pr_size + dr_size, label)
        self._real_circuit.add_register(cr)

        # Measure Order for bitstring: [PR] [AR] [DR]
        # cr[0:dr] is LSB (DR)
        # cr[dr:dr+ar] is Middle (AR)
        # cr[dr+ar:total] is MSB (PR)
        current = 0
        self._real_circuit.measure(self.DR, cr[0:dr_size])
        current += dr_size

        if ar_size > 0:
            self._real_circuit.measure(self.AR, cr[current:current+ar_size])
            current += ar_size

        if pr_size > 0:
            self._real_circuit.measure(self.PR, cr[current:current+pr_size])
            current += pr_size

        return cr

    def reset_bus(self, qr_index: Optional[int] = None):
        """Adds reset instructions to PR, AR, QR and DR registers."""
        if self._defer_mode:
            self._record_op("RESET_BUS", qr_index=qr_index)
        else:
            if self.page_bits > 0:
                self._real_circuit.reset(self.PR)
            self._real_circuit.reset(self.AR)
            if qr_index is not None:
                self._real_circuit.reset(self.QR[qr_index])
            else:
                for q in self.QR:
                    self._real_circuit.reset(q)
            self._real_circuit.reset(self.DR)

    def measure_page(self, page_index: int, label: str = None):
        """Adds measurement gates to internal registers (PC, A, D) of a specific page."""
        if self._defer_mode:
            self._record_op("MEASURE_PAGE", page_index=page_index, label=label)
            return None

        from qiskit.circuit import ClassicalRegister
        if page_index >= len(self.pages):
            raise ValueError(f"Page index {page_index} out of range.")

        p = self.pages[page_index]
        label = label or f"Page{page_index}Measure"

        # PC, A, D
        pc_size = p.PC.size
        a_size = p.A.size
        d_size = p.D.size

        cr = ClassicalRegister(pc_size + a_size + d_size, label)
        self._real_circuit.add_register(cr)

        # Order: D (bottom), A (middle), PC (top/MSB)
        self._real_circuit.measure(p.D, cr[0:d_size])
        self._real_circuit.measure(p.A, cr[d_size:d_size+a_size])
        self._real_circuit.measure(p.PC, cr[d_size+a_size:])

        return cr


def q1ram_batch(label_or_func=None, label=None):
    """
    Decorator that executes the decorated function as a batch Q1RAM batch.
    Can be used as @q1ram_batch or @q1ram_batch(label="MemoryInit")
    """
    import functools

    def decorator(func, active_label=None):
        @functools.wraps(func)
        def wrapper(qram_instance: Q1RAM, *args, **kwargs):
            if not isinstance(qram_instance, Q1RAM):
                raise TypeError(
                    "First argument to @q1ram_batch function must be a Q1RAM instance.")

            label = active_label or func.__name__
            with qram_instance.batch(label=label):
                return func(qram_instance, *args, **kwargs)
        return wrapper

    if callable(label_or_func):
        # Case: @q1ram_batch
        return decorator(label_or_func, active_label=label)
    else:
        # Case: @q1ram_batch(label="...")
        target_label = label or label_or_func
        return lambda f: decorator(f, active_label=target_label)


class ExecutionResult:
    """Encapsulates the response from a batch execution."""

    def __init__(self, data: dict, address_bits: int, data_bits: int, operations: List[dict] = None):
        self.qasm = data.get("qasm", "")
        self.metadata = data.get("metadata", {})
        self.address_bits = address_bits
        self.data_bits = data_bits
        self.operations = operations or []

    def to_qiskit(self) -> 'QuantumCircuit':
        """Converts the result QASM to a Qiskit QuantumCircuit."""
        if not HAS_QISKIT:
            raise ImportError(
                "Qiskit is not installed. Cannot convert to QuantumCircuit.")
        return qasm3.loads(self.qasm)

    def integrate(self, target_circuit: 'QuantumCircuit', register_map: dict, **kwargs):
        """
        Integrates the generated circuit into a target Qiskit circuit using name-based mapping.

        Args:
            target_circuit: The existing QuantumCircuit to extend.
            register_map: Dictionary mapping source register names (e.g. "AR", "DQ") 
                          to target Qiskit Registers (or list of qubits).
                          Keys should be: 'AR', 'DR', 'A', 'D', 'DQ', 'RW', 'ANC'.
            **kwargs: Additional arguments passed to circuit.compose().
        """
        if not HAS_QISKIT:
            raise ImportError(
                "Qiskit is not installed. Cannot integrate circuit.")

        from qiskit.circuit import QuantumRegister, Qubit

        source_circuit = self.to_qiskit()

        # 1. Build the qubit mapping list required by compose()
        # compose(source, qubits=[...]) requires the list to match the order of source.qubits
        # source.qubits is ordered by the order of qregs in source.qregs

        final_qubit_map = []

        # Helper to normalize input to list of qubits
        def to_qubits(reg):
            if reg is None:
                return []
            if isinstance(reg, (list, tuple)):
                return list(reg)
            return list(reg)

        # Normalize keys in map for easy lookup
        reg_map_norm = {k.upper(): v for k, v in register_map.items()}

        used_ancillas = 0

        for reg in source_circuit.qregs:
            name_upper = reg.name.upper()

            # Identify target
            target_reg = None

            # Direct Name Match
            if name_upper in reg_map_norm:
                target_reg = reg_map_norm[name_upper]

            # Alias / Fallback Handling
            elif name_upper == "DIRECTION":
                target_reg = reg_map_norm.get("DQ")
            elif name_upper.startswith("ANC") or name_upper.startswith("AUX"):
                # Handle Ancilla
                # We pull from the 'ANC' pool in the map
                pool = to_qubits(reg_map_norm.get("ANC"))
                needed = reg.size

                if pool:
                    if used_ancillas + needed > len(pool):
                        # Not enough existing ancillas, create new ones
                        # Usually Q1RAM allocates enough, but dynamic expansion is safe
                        needed_new = (used_ancillas + needed) - len(pool)
                        new_r = QuantumRegister(
                            needed_new, f"auto_anc_{len(target_circuit.qregs)}")
                        target_circuit.add_register(new_r)

                        # Extend pool virtually
                        full_pool = pool + list(new_r)
                        target_reg = full_pool[used_ancillas: used_ancillas + needed]
                    else:
                        target_reg = pool[used_ancillas: used_ancillas + needed]

                    used_ancillas += needed
                else:
                    # Create completely new
                    new_r = QuantumRegister(
                        reg.size, f"auto_anc_{len(target_circuit.qregs)}")
                    target_circuit.add_register(new_r)
                    target_reg = list(new_r)

            if target_reg is None:
                raise ValueError(
                    f"Could not map source register '{reg.name}' to the target circuit. Provided map keys: {list(reg_map_norm.keys())}")

            # Verify size
            t_qubits = to_qubits(target_reg)
            if len(t_qubits) != reg.size:
                raise ValueError(
                    f"Size mismatch for register '{reg.name}'. Source: {reg.size}, Target: {len(t_qubits)}.")

            final_qubit_map.extend(t_qubits)

        # Perform integration
        encapsulate = kwargs.pop('encapsulate', True)
        if encapsulate:
            label = kwargs.pop('label', "Q1RAM")
            try:
                gate = source_circuit.to_gate()
                gate.name = label
                target_circuit.append(gate, final_qubit_map)
            except:
                # Fallback to compose if to_gate fails
                target_circuit.compose(
                    source_circuit, qubits=final_qubit_map, inplace=True, **kwargs)
        else:
            target_circuit.compose(
                source_circuit, qubits=final_qubit_map, inplace=True, **kwargs)

    def __str__(self):
        return f"ExecutionResult(depth={self.metadata.get('depth')}, instructions={self.metadata.get('instruction_count')})"

# Removed legacy qram_op to enforce new usage


class Batch:
    """
    Builder for Q1RAM batches (V2).
    Accumulates operations locally to be executed in a single batch.
    """

    def __init__(self, address_bits: int, data_bits: int, num_pages: int = 1, page_bits: int = 0, num_qr: int = 0, client: Optional[_APIClient] = None):
        self.address_bits = address_bits
        self.data_bits = data_bits
        self.num_pages = num_pages
        self.page_bits = page_bits
        self.num_qr = num_qr
        self.client = client or _APIClient()
        self.operations = []

    def _add_op(self, op_type: str, address=None, data=None, qr=None, qr_index=None):
        op = {"op": op_type}
        if address is not None:
            op["address"] = address
        if data is not None:
            op["data"] = data
        if qr is not None:
            op["qr"] = qr
        if qr_index is not None:
            op["qr_index"] = qr_index
        self.operations.append(op)
        return self

    # --- Primitive Operations ---
    def read(self, address: Union[List[int], int, None] = None):
        """
        Queue a READ operation.
        If address is None, assumes the Address Register (AR) is already initialized.
        """
        return self._add_op("READ", address=address if isinstance(address, list) else address)

    def write_all(self, data: Union[List[int], int, None] = None):
        """
        Queue a WRITE_ALL operation.
        If data is None, assumes DR is initialized.
        """
        return self._add_op("WRITE_ALL", data=data)

    def write(self, address: Union[List[int], int, None] = None, data: Union[List[int], int, None] = None):
        """
        Queue a WRITE operation.
        If address is None, assumes AR is initialized.
        If data is None, assumes Data Register (DR) is initialized.
        """
        return self._add_op("WRITE", address=address, data=data)

    # --- Stack Operations ---
    def push(self, data: Union[List[int], int, None] = None):
        """
        Queue a PUSH operation.
        If data is None, assumes DR is initialized.
        """
        return self._add_op("PUSH", data=data)

    def pop(self):
        """Queue a POP operation."""
        return self._add_op("POP")

    # --- Queue Operations ---
    def enqueue(self, data: Union[List[int], int, None] = None):
        """
        Queue an ENQUEUE operation.
        If data is None, assumes DR is initialized.
        """
        return self._add_op("ENQUEUE", data=data)

    def dequeue(self):
        """Queue a DEQUEUE operation."""
        return self._add_op("DEQUEUE")

    def save_ar_to_qr(self, qr_index: int = 0):
        """Queue a SAVE_AR_TO_QR operation."""
        return self._add_op("SAVE_AR_TO_QR", qr_index=qr_index)

    def restore_ar_from_qr(self, qr_index: int = 0):
        """Queue a RESTORE_AR_FROM_QR operation."""
        return self._add_op("RESTORE_AR_FROM_QR", qr_index=qr_index)

    def reset_bus(self, qr_index: Optional[int] = None):
        """Queue a RESET_BUS operation."""
        return self._add_op("RESET_BUS", qr_index=qr_index)

    def measure_bus(self, label: str = "BusMeasure"):
        """Queue a MEASURE_BUS operation."""
        op = {"op": "MEASURE_BUS", "label": label}
        self.operations.append(op)
        return self

    def measure_page(self, page_index: int, label: str = None):
        """Queue a MEASURE_PAGE operation."""
        op = {"op": "MEASURE_PAGE", "page_index": page_index, "label": label}
        self.operations.append(op)
        return self

    def build(self, layout=None, **kwargs) -> dict:
        """
        Compiles the batch into a BatchRequest data dictionary.
        """
        config = {
            "address_bits": self.address_bits,
            "data_bits": self.data_bits,
            "num_pages": self.num_pages,
            "page_bits": self.page_bits,
            "num_qr": self.num_qr,
            **kwargs
        }

        batch_data = {
            "config": config,
            "operations": self.operations
        }

        if layout:
            batch_data["layout"] = layout

        return batch_data

    def execute(self, layout=None, **kwargs) -> 'ExecutionResult':
        """
        Builds and executes the batch via the API client.
        """
        batch_data = self.build(layout=layout, **kwargs)
        return self.client.execute_batch(batch_data)
