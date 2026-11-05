"""CSC429 stage-6 deterministic generators.

One generator per slot topic.  Data-representation answers are computed with
exact integer/struct operations and the assembly answer is verified by
simulating all three programs.  Descriptive topics use a bank of marking
points; no LLM is called.
"""
from __future__ import annotations

import argparse
import json
import random
import struct
import tempfile
from pathlib import Path

from src import config
from src.subjects.csc429.planner import build_plan

SUBJECT = "CSC429"
TRACKING = config.TRACKING_DIR / "csc429"
VALIDATION_PATH = TRACKING / "generator_validation.json"

FIGURE_KINDS = ("von_neumann", "cpu_datapath", "cache_mapping")
GENERATOR_IDS = (
    "csc429.computer_generations_history",
    "csc429.data_representation",
    "csc429.cpu_organization",
    "csc429.memory_cache",
    "csc429.interrupts_io",
    "csc429.buses_interconnection",
    "csc429.parallel_architectures",
    "csc429.assembly",
)

# ---------------------------------------------------------------------------
# Descriptive marking-point banks
# ---------------------------------------------------------------------------
BANK: dict[tuple[str, int], list[dict]] = {
    ("computer_generations_history", 5): [
        {
            "stem": "Computer generations are distinguished by their main technology.",
            "parts": [
                {"marks": 2, "text": "State the main technology of the first and third generations.",
                 "answer": "First generation: vacuum tubes. Third generation: integrated circuits."},
                {"marks": 3, "text": "Explain ONE major limitation of first-generation computers.",
                 "answer": "They used thousands of vacuum tubes, so they were very large, generated a lot of heat, consumed high power and were unreliable."},
            ],
        },
        {
            "stem": "John von Neumann contributed the stored-program concept.",
            "parts": [
                {"marks": 2, "text": "Name TWO computers inspired by von Neumann's architecture.",
                 "answer": "Any two of: IAS machine, EDVAC, EDSAC, MANCHESTER Mark I."},
                {"marks": 3, "text": "Describe the stored-program concept.",
                 "answer": "Instructions and data are stored together in the same memory; the CPU fetches and executes instructions from memory, so a program can be changed without rewiring the machine."},
            ],
        },
        {
            "stem": "The integrated circuit was an important milestone in computer history.",
            "parts": [
                {"marks": 2, "text": "Define an integrated circuit.",
                 "answer": "A small semiconductor chip containing many transistors and other electronic components fabricated together."},
                {"marks": 3, "text": "State THREE advantages of integrated circuits over discrete transistors.",
                 "answer": "Smaller size, lower power consumption, higher speed/reliability, and lower cost in large quantities."},
            ],
        },
    ],
    ("cpu_organization", 5): [
        {
            "stem": "The CPU contains a control unit and an arithmetic logic unit.",
            "parts": [
                {"marks": 2, "text": "Explain the function of the control unit.",
                 "answer": "It fetches and decodes instructions and generates control signals that coordinate the datapath and other components."},
                {"marks": 3, "text": "Explain the function of the ALU.",
                 "answer": "It performs arithmetic and logical operations on operands and records status flags such as zero, carry, overflow and sign."},
            ],
        },
        {
            "stem": "The program counter and instruction register are important CPU registers.",
            "parts": [
                {"marks": 2, "text": "Differentiate the program counter and the instruction register.",
                 "answer": "The PC holds the address of the next instruction; the IR holds the instruction currently being decoded/executed."},
                {"marks": 3, "text": "Describe the fetch-decode-execute cycle.",
                 "answer": "Fetch the instruction at the PC into the IR and increment the PC; decode the opcode and operands; execute the operation and write back the result."},
            ],
        },
    ],
    ("cpu_organization", 10): [
        {
            "stem": "The machine cycle is the basic sequence of CPU operations.",
            "parts": [
                {"marks": 2, "text": "List the phases of the machine cycle.",
                 "answer": "Fetch, decode, execute (and write-back/store)."},
                {"marks": 3, "text": "Explain the role of the PC, IR, MAR, MBR and CU during the fetch phase.",
                 "answer": "PC -> MAR; memory is read into MBR and then IR; the CU decodes the instruction; the PC is incremented to point to the next instruction."},
                {"marks": 5, "text": "Explain what happens during the execute phase and how the ALU and registers are used.",
                 "answer": "The CU issues control signals; operands are read from registers or memory; the ALU performs the operation; the result and status flags are written back to a register or memory."},
            ],
        },
        {
            "stem": "A CPU uses several registers during instruction execution.",
            "parts": [
                {"marks": 5, "text": "List FIVE CPU registers and state the function of each.",
                 "answer": "PC (next instruction address), IR (current instruction), MAR (memory address), MBR/MDR (memory data), AC/accumulator (ALU result); general-purpose registers, stack pointer and status flags are also acceptable."},
                {"marks": 5, "text": "Explain how the control unit and ALU cooperate to execute an arithmetic instruction.",
                 "answer": "The CU decodes the instruction and selects operands; the ALU performs the arithmetic operation; the CU writes the result/status back and advances the PC."},
            ],
        },
        {
            "stem": "The control unit and ALU are the main components of a CPU.",
            "parts": [
                {"marks": 3, "text": "Describe the control unit's role in instruction execution.",
                 "answer": "It fetches, decodes and sequences instructions and generates control signals for the datapath."},
                {"marks": 3, "text": "Describe the ALU's role and the meaning of status flags.",
                 "answer": "The ALU performs arithmetic/logic operations; status flags record conditions such as zero, carry, overflow and sign."},
                {"marks": 4, "text": "Explain how the PC and IR are used in the machine cycle.",
                 "answer": "The PC supplies the instruction address to memory; the fetched instruction is placed in the IR for decoding, and the PC is incremented for the next fetch."},
            ],
        },
    ],
    ("memory_cache", 10): [
        {
            "stem": "A computer uses a memory hierarchy to balance speed, size and cost.",
            "parts": [
                {"marks": 3, "text": "Describe the memory hierarchy from registers to secondary storage.",
                 "answer": "Registers -> cache -> main memory -> secondary storage; speed and cost per bit decrease while capacity increases down the hierarchy."},
                {"marks": 3, "text": "Explain why cache memory improves performance.",
                 "answer": "Cache holds recently used data close to the CPU, so many accesses are satisfied without waiting for slower main memory."},
                {"marks": 4, "text": "Compare SRAM and DRAM.",
                 "answer": "SRAM uses flip-flops, is faster, more expensive and needs more area; DRAM uses capacitors, is denser, cheaper and needs refresh."},
            ],
        },
        {
            "stem": "Cache memory stores recently accessed data and instructions.",
            "parts": [
                {"marks": 2, "text": "Define cache hit and cache miss.",
                 "answer": "A hit is a request found in cache; a miss is a request not found there, so the block must be fetched from a lower level."},
                {"marks": 4, "text": "Explain spatial locality and temporal locality.",
                 "answer": "Spatial locality: nearby addresses are likely to be accessed soon. Temporal locality: the same address is likely to be accessed again soon."},
                {"marks": 4, "text": "Compare direct-mapped, set-associative and fully associative mapping.",
                 "answer": "Direct-mapped: one possible line per block. Set-associative: a block maps to a set and can occupy any line in that set. Fully associative: a block can occupy any line."},
            ],
        },
        {
            "stem": "A cache uses tags and line numbers to identify blocks.",
            "parts": [
                {"marks": 3, "text": "Explain the purpose of the tag, line/index and offset fields of a cache address.",
                 "answer": "The tag identifies the block stored in a line; the index selects the set/line; the offset selects the word/byte inside the block."},
                {"marks": 3, "text": "State what happens on a cache miss.",
                 "answer": "The requested block is fetched from main memory, a line is selected/replaced, the tag and valid bit are updated, and the access is retried."},
                {"marks": 4, "text": "Explain ONE advantage and ONE disadvantage of direct-mapped cache.",
                 "answer": "Advantage: simple and fast indexing. Disadvantage: conflict misses because several blocks can map to the same line."},
            ],
        },
    ],
    ("interrupts_io", 10): [
        {
            "stem": "Multiple interrupts can arrive while the CPU is servicing another interrupt.",
            "parts": [
                {"marks": 3, "text": "Explain nested interrupts.",
                 "answer": "A higher-priority interrupt can interrupt a lower-priority ISR; the CPU saves the lower ISR context and services the higher-priority one first."},
                {"marks": 3, "text": "Describe how interrupt priority determines the order of service.",
                 "answer": "The interrupt controller compares priorities and presents the highest-priority pending request to the CPU first."},
                {"marks": 4, "text": "Explain the sequence of events when a higher-priority interrupt arrives during an ISR.",
                 "answer": "The CPU finishes the current instruction, saves the current context, acknowledges the higher-priority interrupt and jumps to its ISR; the lower ISR resumes after the higher one returns."},
            ],
        },
        {
            "stem": "The CPU can use programmed I/O, interrupt-driven I/O or DMA.",
            "parts": [
                {"marks": 2, "text": "Describe programmed I/O.",
                 "answer": "The CPU repeatedly checks the device status and transfers data itself, so it wastes time polling."},
                {"marks": 3, "text": "Describe interrupt-driven I/O.",
                 "answer": "The device signals the CPU with an interrupt when it is ready; the CPU services the device in an ISR instead of polling."},
                {"marks": 5, "text": "Explain how DMA improves I/O performance and state ONE advantage over interrupt-driven I/O.",
                 "answer": "A DMA controller transfers a block directly between the device and memory while the CPU continues other work; one interrupt is needed at completion, so there is less CPU overhead per transfer."},
            ],
        },
        {
            "stem": "Interrupts can be maskable or non-maskable.",
            "parts": [
                {"marks": 3, "text": "Differentiate maskable and non-maskable interrupts.",
                 "answer": "Maskable interrupts can be disabled/delayed by the CPU; non-maskable interrupts cannot be ignored and are used for critical events."},
                {"marks": 3, "text": "Explain what an interrupt handler (ISR) does.",
                 "answer": "It saves context, identifies the device/cause, services the request, clears the interrupt and restores context."},
                {"marks": 4, "text": "Describe TWO methods for handling multiple interrupts.",
                 "answer": "Priority-based nesting and polling/sequential service; nested interrupts allow a higher-priority request to pre-empt a lower-priority ISR."},
            ],
        },
    ],
    ("buses_interconnection", 10): [
        {
            "stem": "A computer uses system interconnection and CPU interconnection.",
            "parts": [
                {"marks": 3, "text": "Differentiate system interconnection and CPU interconnection.",
                 "answer": "System interconnection connects the CPU, memory and I/O devices; CPU interconnection connects components inside the processor, such as cores and cache."},
                {"marks": 4, "text": "Describe the address bus, data bus and control bus.",
                 "answer": "Address bus carries the address; data bus carries data/instructions; control bus carries control and timing signals."},
                {"marks": 3, "text": "Explain how bus width and bus timing affect performance.",
                 "answer": "A wider data bus transfers more bits per cycle; faster timing/clocking reduces the time per transfer, both increasing bandwidth."},
            ],
        },
        {
            "stem": "Buses connect the CPU, memory and I/O devices.",
            "parts": [
                {"marks": 2, "text": "Define a bus.",
                 "answer": "A shared set of electrical lines carrying addresses, data and control signals between components."},
                {"marks": 4, "text": "Compare synchronous and asynchronous bus timing.",
                 "answer": "Synchronous uses a common clock and fixed timing; asynchronous uses handshaking, so it is more flexible but has more overhead."},
                {"marks": 4, "text": "Explain bus arbitration and why it is needed.",
                 "answer": "Arbitration decides which master gets the bus when several request it; it prevents conflicting simultaneous transfers."},
            ],
        },
    ],
    ("parallel_architectures", 10): [
        {
            "stem": "Flynn's taxonomy classifies computer architectures by instruction and data streams.",
            "parts": [
                {"marks": 4, "text": "Describe SISD, SIMD, MISD and MIMD.",
                 "answer": "SISD: one instruction/one data stream. SIMD: one instruction/ multiple data streams. MISD: multiple instructions/one data stream. MIMD: multiple instructions/multiple data streams."},
                {"marks": 2, "text": "Give ONE example of SIMD and ONE example of MIMD.",
                 "answer": "SIMD: GPU/vector processor. MIMD: multicore CPU or cluster."},
                {"marks": 4, "text": "Explain the difference between shared-memory and distributed-memory MIMD.",
                 "answer": "Shared-memory MIMD uses one address space accessible by all processors; distributed-memory MIMD gives each processor local memory and communicates by messages."},
            ],
        },
        {
            "stem": "Multicore processors are common in modern computers.",
            "parts": [
                {"marks": 2, "text": "Define multicore processing.",
                 "answer": "A single processor package contains multiple independent cores that can execute instructions concurrently."},
                {"marks": 4, "text": "Explain TWO benefits of multicore processing.",
                 "answer": "Higher throughput on parallel workloads and better performance per watt; it can also improve responsiveness by running tasks concurrently."},
                {"marks": 4, "text": "Describe NUMA and ONE challenge in a distributed-memory system.",
                 "answer": "NUMA: memory access time depends on which node owns the data. Challenge: inter-node communication/synchronisation overhead and programming complexity."},
            ],
        },
    ],
}

# ---------------------------------------------------------------------------
# Data representation
# ---------------------------------------------------------------------------
def _bin(value: int, bits: int = 8) -> str:
    return format(value & ((1 << bits) - 1), f"0{bits}b")


def _hex(value: int, digits: int = 2) -> str:
    return format(value, f"0{digits}X")


def _octal(value: int) -> str:
    return format(value, "o")


def _sign_magnitude(value: int, bits: int = 8) -> str:
    if not -(1 << (bits - 1)) < value < (1 << (bits - 1)):
        raise ValueError("value does not fit in sign-magnitude byte")
    sign = "1" if value < 0 else "0"
    return sign + format(abs(value), f"0{bits - 1}b")


def _ones_complement(value: int, bits: int = 8) -> str:
    if value >= 0:
        return _bin(value, bits)
    return _bin((~abs(value)) & ((1 << bits) - 1), bits)


def _twos_complement(value: int, bits: int = 8) -> str:
    return _bin(value & ((1 << bits) - 1), bits)


def _ieee_hex(value: float) -> str:
    return struct.pack(">f", float(value)).hex().upper()


def _ieee_decimal(hex_value: str) -> float:
    return struct.unpack(">f", bytes.fromhex(hex_value))[0]


def _ieee_fields(value: float) -> str:
    bits = f"{struct.unpack('>I', struct.pack('>f', float(value)))[0]:032b}"
    return (f"sign={bits[0]}, exponent={bits[1:9]}, "
            f"mantissa={bits[9:]} -> {_ieee_hex(value)}")


def _data_question(slot: dict, rng: random.Random, kind: str) -> dict:
    marks = int(slot["marks"])
    parts: list[dict] = []
    verification: dict = {"kind": kind}
    if marks == 5:
        if kind == "base":
            dec = rng.randint(10, 250)
            binary = rng.randint(1, 255)
            parts = [
                {"marks": 2, "text": f"Convert {dec} to binary. Show your workflow.",
                 "answer": f"{dec} = {_bin(dec)}₂."},
                {"marks": 3, "text": f"Convert {_bin(binary)}₂ to decimal. Show your workflow.",
                 "answer": f"{_bin(binary)}₂ = {binary}₁₀."},
            ]
            verification.update({"dec": dec, "binary_value": binary})
        elif kind == "signed":
            value = -rng.randint(1, 120)
            parts = [
                {"marks": 2, "text": f"Represent {value} in 8-bit sign-magnitude form.",
                 "answer": f"{_sign_magnitude(value)} (sign bit 1, magnitude {abs(value)})."},
                {"marks": 3, "text": f"Represent {value} in 8-bit two's complement form.",
                 "answer": f"{_twos_complement(value)}."},
            ]
            verification.update({"value": value,
                                 "sign_magnitude": _sign_magnitude(value),
                                 "twos": _twos_complement(value)})
        elif kind == "ieee":
            value = rng.choice([-27.15625, 43.046875, -156.15625, 204.9375,
                                81.21875, -9.5, 12.25, 0.5])
            parts = [
                {"marks": 5, "text": f"Convert {value} to IEEE 754 single-precision format. Give the result in hexadecimal and show the sign, exponent and mantissa fields.",
                 "answer": f"{_ieee_fields(value)}."},
            ]
            verification.update({"value": value, "hex": _ieee_hex(value)})
        else:
            raise ValueError(f"unknown 5-mark data kind: {kind}")
    elif marks == 10:
        if kind == "bases":
            values = rng.sample(range(16, 240), 4)
            parts = [
                {"marks": 2, "text": f"Convert {values[0]} to binary.",
                 "answer": f"{values[0]} = {_bin(values[0])}₂."},
                {"marks": 2, "text": f"Convert {_bin(values[1])}₂ to hexadecimal.",
                 "answer": f"{_bin(values[1])}₂ = {_hex(values[1])}₁₆."},
                {"marks": 3, "text": f"Convert {_hex(values[2])}₁₆ to octal.",
                 "answer": f"{_hex(values[2])}₁₆ = {_octal(values[2])}₈."},
                {"marks": 3, "text": f"Convert {_octal(values[3])}₈ to decimal.",
                 "answer": f"{_octal(values[3])}₈ = {values[3]}₁₀."},
            ]
            verification.update({"values": values})
        elif kind == "signed":
            left = rng.randint(-90, 90)
            right = rng.randint(-90, 90)
            if left >= 0 and right >= 0:
                right = -rng.randint(1, 90)
            result = left - right
            if not -128 <= result <= 127:
                left = rng.randint(-60, 60)
                right = -rng.randint(1, 60)
                result = left - right
            parts = [
                {"marks": 5, "text": f"Calculate {left} - ({right}) using 8-bit sign-magnitude. Show the complete workflow and the result in byte form.",
                 "answer": f"{left} - ({right}) = {result}. Sign-magnitude result: {_sign_magnitude(result)}."},
                {"marks": 5, "text": f"Calculate {left} - ({right}) using 8-bit two's complement. Show the complete workflow and the result in byte form.",
                 "answer": f"{left} - ({right}) = {result}. Two's complement result: {_twos_complement(result)}."},
            ]
            verification.update({"left": left, "right": right, "result": result})
        elif kind == "ieee":
            value = rng.choice([-27.15625, 43.046875, -156.15625, 204.9375,
                                81.21875, -9.5, 12.25, 0.5])
            hex_value = _ieee_hex(value)
            parts = [
                {"marks": 5, "text": f"Convert {value} to IEEE 754 single precision in hexadecimal. Show the sign, exponent and mantissa.",
                 "answer": f"{_ieee_fields(value)}."},
                {"marks": 5, "text": f"Convert the IEEE 754 single-precision value {hex_value} to decimal.",
                 "answer": f"{hex_value} = {_ieee_decimal(hex_value)!r}."},
            ]
            verification.update({"value": value, "hex": hex_value})
        else:
            raise ValueError(f"unknown 10-mark data kind: {kind}")
    else:
        raise ValueError(f"unsupported data-representation marks: {marks}")
    for index, part in enumerate(parts):
        part.setdefault("label", chr(ord("a") + index))
    return {
        "number": slot["slot"],
        "part": slot["part"],
        "kind": "structured",
        "marks": marks,
        "topic": slot["topic"],
        "generator_id": slot["generator_id"],
        "stem": "Answer the following data-representation questions. Show your complete workflow.",
        "parts": parts,
        "verification": verification,
    }

# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
ASSEMBLY_TEMPLATES = (
    {
        "id": "sum_product_difference",
        "expr": "(A + B) * (C - D) / E",
        "func": lambda v: (v["A"] + v["B"]) * (v["C"] - v["D"]) / v["E"],
        "test": {"A": 6, "B": 2, "C": 4, "D": 1, "E": 2},
        "zero": ["PUSH A", "PUSH B", "ADD", "PUSH C", "PUSH D", "SUB",
                 "MUL", "PUSH E", "DIV", "POP Z"],
        "one": ["LOAD A", "ADD B", "STORE X", "LOAD C", "SUB D", "STORE Y",
                "LOAD X", "MUL Y", "STORE X", "LOAD X", "DIV E", "STORE Z"],
        "three": ["ADD X, A, B", "SUB Y, C, D", "MUL X, X, Y",
                  "DIV Z, X, E"],
    },
    {
        "id": "product_sum_difference",
        "expr": "A * B + C - D",
        "func": lambda v: v["A"] * v["B"] + v["C"] - v["D"],
        "test": {"A": 3, "B": 4, "C": 5, "D": 2},
        "zero": ["PUSH A", "PUSH B", "MUL", "PUSH C", "ADD", "PUSH D",
                 "SUB", "POP Z"],
        "one": ["LOAD A", "MUL B", "STORE X", "LOAD X", "ADD C", "SUB D",
                "STORE Z"],
        "three": ["MUL X, A, B", "ADD X, X, C", "SUB Z, X, D"],
    },
    {
        "id": "difference_product_quotient",
        "expr": "(A - B) * C + D / E",
        "func": lambda v: (v["A"] - v["B"]) * v["C"] + v["D"] / v["E"],
        "test": {"A": 7, "B": 2, "C": 3, "D": 8, "E": 4},
        "zero": ["PUSH A", "PUSH B", "SUB", "PUSH C", "MUL", "PUSH D",
                 "PUSH E", "DIV", "ADD", "POP Z"],
        "one": ["LOAD A", "SUB B", "STORE X", "LOAD X", "MUL C", "STORE X",
                "LOAD D", "DIV E", "ADD X", "STORE Z"],
        "three": ["SUB X, A, B", "MUL X, X, C", "DIV Y, D, E",
                  "ADD Z, X, Y"],
    },
    {
        "id": "sum_product_difference_2",
        "expr": "A + B * C - D",
        "func": lambda v: v["A"] + v["B"] * v["C"] - v["D"],
        "test": {"A": 2, "B": 3, "C": 4, "D": 5},
        "zero": ["PUSH B", "PUSH C", "MUL", "PUSH A", "ADD", "PUSH D",
                 "SUB", "POP Z"],
        "one": ["LOAD B", "MUL C", "ADD A", "SUB D", "STORE Z"],
        "three": ["MUL X, B, C", "ADD X, A, X", "SUB Z, X, D"],
    },
    {
        "id": "sum_over_difference",
        "expr": "(A + B) / (C - D)",
        "func": lambda v: (v["A"] + v["B"]) / (v["C"] - v["D"]),
        "test": {"A": 6, "B": 2, "C": 5, "D": 2},
        "zero": ["PUSH A", "PUSH B", "ADD", "PUSH C", "PUSH D", "SUB",
                 "DIV", "POP Z"],
        "one": ["LOAD A", "ADD B", "STORE X", "LOAD C", "SUB D", "STORE Y",
                "LOAD X", "DIV Y", "STORE Z"],
        "three": ["ADD X, A, B", "SUB Y, C, D", "DIV Z, X, Y"],
    },
)


def _assembly_question(slot: dict, rng: random.Random) -> dict:
    template = rng.choice(ASSEMBLY_TEMPLATES)
    expected = template["func"](template["test"])
    parts = [
        {"marks": 6, "label": "a",
         "text": "Write a zero-address program for the expression.",
         "answer": "\n".join(template["zero"])},
        {"marks": 6, "label": "b",
         "text": "Write a one-address program for the expression.",
         "answer": "\n".join(template["one"])},
        {"marks": 8, "label": "c",
         "text": "Write a three-address program for the expression.",
         "answer": "\n".join(template["three"])},
    ]
    stem = (
        f"Write appropriate programs using zero-, one- and three-address "
        f"instructions to compute Z = {template['expr']}. Registers A, B, C, "
        "D and E must not be modified; X, Y and Z are temporary registers; "
        "the final answer must be stored in Z. Available instructions: "
        "zero-address PUSH, POP, ADD, SUB, MUL, DIV; one-address LOAD, STORE, "
        "ADD, SUB, MUL, DIV; three-address ADD, SUB, MUL, DIV.")
    return {
        "number": slot["slot"],
        "part": slot["part"],
        "kind": "assembly",
        "marks": int(slot["marks"]),
        "topic": slot["topic"],
        "generator_id": slot["generator_id"],
        "stem": stem,
        "parts": parts,
        "expression": template["expr"],
        "programs": {
            "zero": template["zero"],
            "one": template["one"],
            "three": template["three"],
        },
        "test_values": template["test"],
        "expected_value": expected,
        "template_id": template["id"],
    }

# ---------------------------------------------------------------------------
# Paper assembly
# ---------------------------------------------------------------------------
def _labelled(parts: list[dict]) -> list[dict]:
    for index, part in enumerate(parts):
        part.setdefault("label", chr(ord("a") + index))
    return parts


def _history_diagram_question(slot: dict) -> dict:
    return {
        "number": slot["slot"],
        "part": slot["part"],
        "kind": "structured",
        "marks": int(slot["marks"]),
        "topic": slot["topic"],
        "generator_id": slot["generator_id"],
        "stem": "Study {figure} and answer the following questions.",
        "parts": _labelled([
            {"marks": 2,
             "text": "Name the computer organization shown in the figure "
                     "and state its two key principles.",
             "answer": "Von Neumann architecture. Instructions and data are "
                       "stored in the same memory, and the CPU executes "
                       "instructions sequentially unless a branch changes "
                       "the control flow."},
            {"marks": 3,
             "text": "Explain the function of the control unit and the "
                     "arithmetic logic unit in this organization.",
             "answer": "The control unit fetches and decodes instructions "
                       "and generates the control signals. The ALU performs "
                       "arithmetic and logical operations and records status "
                       "flags."},
        ]),
        "figure": {
            "kind": "von_neumann",
            "caption": "Stored-program computer organization.",
            "width_cm": 16.2,
        },
    }


def _cpu_diagram_question(slot: dict) -> dict:
    return {
        "number": slot["slot"],
        "part": slot["part"],
        "kind": "structured",
        "marks": int(slot["marks"]),
        "topic": slot["topic"],
        "generator_id": slot["generator_id"],
        "stem": "Study {figure} and answer the following questions.",
        "parts": _labelled([
            {"marks": 2,
             "text": "Identify the register that holds the address of the "
                     "next instruction and the register that holds the "
                     "instruction currently being decoded.",
             "answer": "PC holds the address of the next instruction; IR "
                       "holds the instruction currently being decoded."},
            {"marks": 3,
             "text": "Explain the roles of MAR and MBR during a memory read.",
             "answer": "The MAR holds the address to be accessed. The memory "
                       "places the selected word in the MBR, which then "
                       "supplies it to the CPU (for example, to the IR)."},
            {"marks": 5,
             "text": "Describe the fetch-decode-execute cycle using the "
                     "components shown in the figure.",
             "answer": "Fetch: PC -> MAR; memory read; MBR -> IR; PC is "
                       "incremented. Decode: the CU interprets the opcode in "
                       "IR and issues control signals. Execute: operands are "
                       "read, the ALU performs the operation, the result and "
                       "flags are written back, and the next instruction is "
                       "fetched."},
        ]),
        "figure": {
            "kind": "cpu_datapath",
            "caption": "CPU, memory and system bus organization.",
            "width_cm": 16.2,
        },
    }


def _cache_diagram_question(slot: dict) -> dict:
    return {
        "number": slot["slot"],
        "part": slot["part"],
        "kind": "structured",
        "marks": int(slot["marks"]),
        "topic": slot["topic"],
        "generator_id": slot["generator_id"],
        "stem": "Study {figure} and answer the following questions.",
        "parts": _labelled([
            {"marks": 2,
             "text": "The cache uses a 16-bit address split into a 4-bit "
                     "tag, a 3-bit line number and a 9-bit offset. For "
                     "address 0x1A2B, give the tag, line number and offset "
                     "in binary.",
             "answer": "0x1A2B = 0001 1010 0010 1011; tag = 0001, line = "
                       "101, offset = 000101011."},
            {"marks": 4,
             "text": "Using the cache state shown in the figure, determine "
                     "whether each address is a hit or a miss: (i) 0x1A2B, "
                     "(ii) 0x2A2B. Explain your reasoning.",
             "answer": "(i) Hit: tag 0001 and line 101; line 5 is valid with "
                       "tag 0001. (ii) Miss: tag 0010 and line 101; line 5 "
                       "is valid but its tag is 0001, so the tags do not "
                       "match."},
            {"marks": 4,
             "text": "Explain why the cache compares tags and how temporal "
                     "and spatial locality improve the hit rate.",
             "answer": "The tag identifies which memory block occupies a "
                       "line; comparing tags prevents returning data from a "
                       "different block. Temporal locality means recently "
                       "used data is likely reused, and spatial locality "
                       "means nearby addresses are likely used, so keeping "
                       "blocks in cache raises the hit rate."},
        ]),
        "figure": {
            "kind": "cache_mapping",
            "caption": "Direct-mapped cache organization and address fields.",
            "width_cm": 16.2,
            "data": {
                "address_bits": 16,
                "tag_bits": 4,
                "line_bits": 3,
                "offset_bits": 9,
                "addresses": ["0x1A2B", "0x2A2B"],
                "cache": {"line3": {"valid": 1, "tag": "0010"},
                          "line5": {"valid": 1, "tag": "0001"}},
            },
        },
    }


def _take_descriptive(slot: dict, pools: dict, rng: random.Random) -> dict:
    key = (slot["topic"], int(slot["marks"]))
    pool = pools.get(key)
    if not pool:
        raise ValueError(f"descriptive bank exhausted for {key}")
    variant = pool.pop(rng.randrange(len(pool)))
    parts = []
    for index, part in enumerate(variant["parts"]):
        parts.append({
            "label": chr(ord("a") + index),
            "marks": int(part["marks"]),
            "text": part["text"],
            "answer": part["answer"],
        })
    if sum(part["marks"] for part in parts) != int(slot["marks"]):
        raise AssertionError(f"bank marks do not match slot {slot['slot']}")
    return {
        "number": slot["slot"],
        "part": slot["part"],
        "kind": "structured",
        "marks": int(slot["marks"]),
        "topic": slot["topic"],
        "generator_id": slot["generator_id"],
        "stem": variant["stem"],
        "parts": parts,
    }


def generate_paper(plan: dict | None = None, seed: int = 1) -> dict:
    if plan is None:
        plan = build_plan(seed)
    if plan["subject"] != SUBJECT:
        raise ValueError("plan belongs to another subject")
    rng = random.Random(int(plan["seed"]))
    pools = {
        key: list(variants) for key, variants in BANK.items()
    }
    data5 = ["base", "signed", "ieee"]
    data10 = ["bases", "signed", "ieee"]
    history_diagram_used = False
    questions: list[dict] = []
    for slot in plan["slots"]:
        generator_id = slot["generator_id"]
        marks = int(slot["marks"])
        if generator_id == "csc429.assembly":
            question = _assembly_question(slot, rng)
        elif generator_id == "csc429.data_representation":
            kinds = data5 if marks == 5 else data10
            if not kinds:
                raise ValueError("data-representation kind pool exhausted")
            kind = kinds.pop(rng.randrange(len(kinds)))
            question = _data_question(slot, rng, kind)
        elif generator_id == "csc429.cpu_organization" and marks == 10:
            question = _cpu_diagram_question(slot)
        elif generator_id == "csc429.memory_cache" and marks == 10:
            question = _cache_diagram_question(slot)
        elif (generator_id == "csc429.computer_generations_history"
              and marks == 5 and not history_diagram_used):
            question = _history_diagram_question(slot)
            history_diagram_used = True
        else:
            question = _take_descriptive(slot, pools, rng)
        questions.append(question)

    topic_marks: dict[str, int] = {}
    for question in questions:
        topic_marks[question["topic"]] = (
            topic_marks.get(question["topic"], 0) + question["marks"])
    part_marks: dict[str, int] = {}
    for question in questions:
        part_marks[question["part"]] = (
            part_marks.get(question["part"], 0) + question["marks"])
    paper = {
        "subject": SUBJECT,
        "seed": int(plan["seed"]),
        "generated_by": "src.subjects.csc429.generators",
        "planner": "src.subjects.csc429.planner",
        "total_marks": sum(part_marks.values()),
        "part_marks": part_marks,
        "topic_marks": topic_marks,
        "question_count": len(questions),
        "slot_count": len(questions),
        "questions": questions,
        "style_profile": {
            "part_a_questions": 10,
            "part_b_questions": 1,
            "computed_data_questions": sum(
                1 for question in questions
                if question.get("generator_id") ==
                "csc429.data_representation"),
            "assembly_questions": sum(
                1 for question in questions
                if question.get("generator_id") == "csc429.assembly"),
            "figure_questions": sum(
                1 for question in questions if question.get("figure")),
        },
        "generator_ids": list(GENERATOR_IDS),
    }
    return paper


def _simulate_zero(lines: list[str], values: dict[str, float]) -> float:
    stack: list[float] = []
    registers = dict(values)
    for line in lines:
        op, *args = line.replace(",", " ").split()
        if op == "PUSH":
            stack.append(float(registers[args[0]]))
        elif op == "POP":
            registers[args[0]] = stack.pop()
        elif op == "ADD":
            right, left = stack.pop(), stack.pop()
            stack.append(left + right)
        elif op == "SUB":
            right, left = stack.pop(), stack.pop()
            stack.append(left - right)
        elif op == "MUL":
            right, left = stack.pop(), stack.pop()
            stack.append(left * right)
        elif op == "DIV":
            right, left = stack.pop(), stack.pop()
            stack.append(left / right)
        else:
            raise ValueError(f"unknown zero-address op {op}")
    return registers["Z"]


def _simulate_one(lines: list[str], values: dict[str, float]) -> float:
    registers = dict(values)
    ac = 0.0
    for line in lines:
        op, *args = line.replace(",", " ").split()
        if op == "LOAD":
            ac = float(registers[args[0]])
        elif op == "STORE":
            registers[args[0]] = ac
        elif op in {"ADD", "SUB", "MUL", "DIV"}:
            operand = float(registers[args[0]])
            if op == "ADD":
                ac += operand
            elif op == "SUB":
                ac -= operand
            elif op == "MUL":
                ac *= operand
            else:
                ac /= operand
        else:
            raise ValueError(f"unknown one-address op {op}")
    return registers["Z"]


def _simulate_three(lines: list[str], values: dict[str, float]) -> float:
    registers = dict(values)
    for line in lines:
        first, left, right = [part.strip() for part in line.split(",")]
        op, dest = first.split()
        if op == "ADD":
            registers[dest] = registers[left] + registers[right]
        elif op == "SUB":
            registers[dest] = registers[left] - registers[right]
        elif op == "MUL":
            registers[dest] = registers[left] * registers[right]
        elif op == "DIV":
            registers[dest] = registers[left] / registers[right]
        else:
            raise ValueError(f"unknown three-address op {op}")
    return registers["Z"]


def validate_paper(paper: dict, plan: dict | None = None) -> list[str]:
    problems: list[str] = []
    if paper.get("total_marks") != 100:
        problems.append("total marks must be 100")
    if paper.get("part_marks") != {"A": 80, "B": 20}:
        problems.append(f"unexpected part marks: {paper.get('part_marks')}")
    questions = paper.get("questions", [])
    part_a = [q for q in questions if q["part"] == "A"]
    part_b = [q for q in questions if q["part"] == "B"]
    if len(part_a) != 10 or len(part_b) != 1:
        problems.append("part question counts are wrong")
    if [q["marks"] for q in part_a] != [5, 5, 5, 5, 10, 10, 10, 10, 10, 10]:
        problems.append("Part A marks pattern is wrong")
    for question in questions:
        if sum(part["marks"] for part in question.get("parts", [])) != question["marks"]:
            problems.append(f"{question['number']} part marks do not sum")
        for part in question.get("parts", []):
            if not part.get("text") or not part.get("answer"):
                problems.append(f"{question['number']} has empty content")
        if question.get("generator_id") not in GENERATOR_IDS:
            problems.append(f"{question['number']} has unknown generator")
    figure_questions = [q for q in questions if q.get("figure")]
    if len(figure_questions) < 3:
        problems.append("paper must contain at least three diagram questions")
    for question in figure_questions:
        figure = question["figure"]
        if figure.get("kind") not in FIGURE_KINDS:
            problems.append(f"{question['number']} has unknown figure kind")
        if not figure.get("caption"):
            problems.append(f"{question['number']} figure has no caption")
        if "{figure}" not in question.get("stem", ""):
            problems.append(f"{question['number']} stem has no figure token")
    assembly = part_b[0] if part_b else None
    if assembly is not None:
        if assembly.get("topic") != "instruction_set_assembly":
            problems.append("B1 topic must be instruction_set_assembly")
        if assembly.get("marks") != 20:
            problems.append("B1 must be 20 marks")
        if sum(part["marks"] for part in assembly.get("parts", [])) != 20:
            problems.append("B1 parts must total 20 marks")
        values = assembly.get("test_values") or {}
        expected = assembly["expected_value"]
        programs = assembly.get("programs") or {}
        for key, simulator in (
                ("zero", _simulate_zero), ("one", _simulate_one),
                ("three", _simulate_three)):
            try:
                actual = simulator(programs[key], values)
            except Exception as error:
                problems.append(f"B1 {key} program failed: {error}")
                continue
            if abs(actual - expected) > 1e-9:
                problems.append(
                    f"B1 {key} program gives {actual}, expected {expected}")
    blob = json.dumps(paper, ensure_ascii=False).lower()
    for marker in ("todo", "tbd", "placeholder", "not implemented"):
        if marker in blob:
            problems.append(f"forbidden marker in paper: {marker}")
    if plan is not None:
        if paper.get("seed") != plan.get("seed"):
            problems.append("paper seed does not match plan seed")
        plan_slots = {slot["slot"]: slot for slot in plan.get("slots", [])}
        for question in questions:
            slot = plan_slots.get(question["number"])
            if slot is None:
                problems.append(f"{question['number']} is not in the plan")
            elif (slot["topic"] != question["topic"]
                  or slot["marks"] != question["marks"]):
                problems.append(
                    f"{question['number']} does not match the plan")
    return problems


def validate_seeds(start: int = 1, end: int = 20,
                   path: Path | None = None) -> dict:
    results = []
    coverage: dict[str, int] = {generator_id: 0 for generator_id in GENERATOR_IDS}
    data_kinds: dict[str, int] = {}
    assembly_templates: dict[str, int] = {}
    figure_kinds: dict[str, int] = {}
    for seed in range(int(start), int(end) + 1):
        plan = build_plan(seed)
        paper = generate_paper(plan)
        problems = validate_paper(paper, plan)
        if generate_paper(plan) != paper:
            problems.append("generator is not deterministic")
        for question in paper["questions"]:
            coverage[question["generator_id"]] = (
                coverage.get(question["generator_id"], 0) + 1)
            if question["generator_id"] == "csc429.data_representation":
                kind = str(question.get("verification", {}).get("kind", "?"))
                key = f"{question['marks']}:{kind}"
                data_kinds[key] = data_kinds.get(key, 0) + 1
            if question["generator_id"] == "csc429.assembly":
                template = str(question.get("template_id", "?"))
                assembly_templates[template] = (
                    assembly_templates.get(template, 0) + 1)
            if question.get("figure"):
                kind = str(question["figure"].get("kind", "?"))
                figure_kinds[kind] = figure_kinds.get(kind, 0) + 1
        results.append({
            "seed": seed,
            "problems": problems,
            "total_marks": paper["total_marks"],
            "question_count": paper["question_count"],
            "generator_ids": sorted({q["generator_id"]
                                     for q in paper["questions"]}),
        })
        if not problems:
            sample = TRACKING / f"generator_seed_{seed:02d}.json"
            sample.write_text(json.dumps(paper, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    expected_data = {"5:base", "5:signed", "5:ieee",
                     "10:bases", "10:signed", "10:ieee"}
    expected_assembly = {item["id"] for item in ASSEMBLY_TEMPLATES}
    report = {
        "subject": SUBJECT,
        "papers_total": len(results),
        "papers_valid": sum(1 for row in results if not row["problems"]),
        "coverage": coverage,
        "missing_generators": [key for key, value in coverage.items()
                               if value == 0],
        "data_kinds": data_kinds,
        "missing_data_kinds": sorted(expected_data - set(data_kinds)),
        "assembly_templates": assembly_templates,
        "missing_assembly_templates": sorted(
            expected_assembly - set(assembly_templates)),
        "figure_kinds": figure_kinds,
        "missing_figure_kinds": sorted(
            set(FIGURE_KINDS) - set(figure_kinds)),
        "results": results,
    }
    target = Path(path) if path is not None else VALIDATION_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default="")
    ap.add_argument("--validate", action="store_true")
    args = ap.parse_args()
    if args.validate:
        report = validate_seeds()
        print(json.dumps({
            "papers_total": report["papers_total"],
            "papers_valid": report["papers_valid"],
            "missing_generators": report["missing_generators"],
            "coverage": report["coverage"],
        }, indent=2))
        return
    plan = build_plan(args.seed)
    paper = generate_paper(plan)
    problems = validate_paper(paper, plan)
    if args.out:
        Path(args.out).write_text(
            json.dumps(paper, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "seed": paper["seed"],
        "total_marks": paper["total_marks"],
        "question_count": paper["question_count"],
        "problems": problems,
    }, indent=2))
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
