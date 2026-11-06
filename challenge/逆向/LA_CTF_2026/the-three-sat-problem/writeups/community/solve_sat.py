#!/usr/bin/env python3
"""
Extract 3-SAT clauses from the binary and solve with Z3.
"""
from z3 import *
import subprocess
import re

BINARY = "/home/kali/Downloads/lactf2025/rev/threesatproblem/three_sat_problem"
INPUT_BASE = 0x15060  # Base address of input buffer
INPUT_LEN = 0x4ff  # 1279

# Get the full disassembly
result = subprocess.run(['objdump', '-d', BINARY], capture_output=True, text=True)
disasm = result.stdout

# Extract the check function (0x1289 to 0x12981)
lines = disasm.split('\n')
func_lines = []
in_func = False
for line in lines:
    if '1289:' in line and 'push' in line:
        in_func = True
    if in_func:
        func_lines.append(line)
        if '12981:' in line and 'ret' in line:
            break

print(f"Function has {len(func_lines)} lines")

# Parse the disassembly to extract:
# 1. Memory references (input byte offsets)
# 2. Stack locations used for negated values
# 3. Clause structure (OR/AND pattern)

# Pattern for memory loads: mov 0xXXXX(%rip),%al or similar
# The address is RIP-relative, so we need to add it to the current instruction address

# First pass: collect all memory addresses referenced
mem_refs = []
addr_pattern = re.compile(r'\s*([0-9a-f]+):\s+.*mov\s+0x([0-9a-f]+)\(%rip\),%(\w+)')

for line in func_lines:
    match = addr_pattern.match(line)
    if match:
        inst_addr = int(match.group(1), 16)
        offset = int(match.group(2), 16)
        reg = match.group(3)
        # RIP-relative addressing: target = inst_addr + instruction_len + offset
        # For mov with this encoding, instruction length is typically 6 bytes
        # But we can approximate by looking at the actual target address in comments

# Let me use a different approach - extract from the comments
# The disassembly shows "# 15060 <stdin@GLIBC_2.2.5+0x10>" etc.
comment_pattern = re.compile(r'#\s+([0-9a-f]+)\s+<')

input_offsets = set()
for line in func_lines:
    match = comment_pattern.search(line)
    if match:
        addr = int(match.group(1), 16)
        if INPUT_BASE <= addr < INPUT_BASE + INPUT_LEN:
            offset = addr - INPUT_BASE
            input_offsets.add(offset)

print(f"Found {len(input_offsets)} unique input byte references")
print(f"Offsets range: {min(input_offsets)} to {max(input_offsets)}")

# Now let's analyze the clause structure more carefully
# The pattern at the end shows:
# - Load byte from memory/stack
# - OR with other bytes (forming clause)
# - AND with accumulator (combining clauses)

# Let me try a different approach: use the intermediate representation
# Parse the sequence of operations to extract clauses

# Actually, the simplest approach is to use the HLIL from Binary Ninja
# But since the function is huge, let's try angr with proper constraints

# For now, let's verify bit 754 constraint and try some heuristics
print(f"\nBit 754 (offset 0x{754:x} = {754}) must be '1' for success")
print(f"This corresponds to input buffer offset {754}")

# Create Z3 solver
solver = Solver()
bits = [Bool(f'b{i}') for i in range(INPUT_LEN)]

# Constraint from main: data_415352 & 1 must be set
# 0x415352 - 0x415060 = 0x2f2 = 754
solver.add(bits[754] == True)

# Now we need to extract the actual clause constraints
# Let me analyze the disassembly pattern more carefully

# The function structure:
# 1. First part: load inputs and compute negations, store on stack
# 2. Second part: evaluate clauses (OR operations)
# 3. Final part: AND all clause results together

# Let me extract the OR patterns from the end of the function
or_pattern = re.compile(r'\s*([0-9a-f]+):.*\bor\s+.*0x([0-9a-f]+)\(%rip\).*#\s+([0-9a-f]+)')
stack_or_pattern = re.compile(r'\s*([0-9a-f]+):.*\bor\s+(-?0x[0-9a-f]+)\(%rsp\),')

# Extract clauses by analyzing OR and AND patterns
# Each clause = (var1 OR var2 OR var3)
# Clauses are ANDed together

# Let's count clause patterns
clause_patterns = []
current_clause = []

for i, line in enumerate(func_lines):
    if '\tor ' in line.lower():
        # Part of a clause
        match = comment_pattern.search(line)
        if match:
            addr = int(match.group(1), 16)
            if INPUT_BASE <= addr < INPUT_BASE + INPUT_LEN:
                current_clause.append(addr - INPUT_BASE)
    if '\tand ' in line.lower() and current_clause:
        # End of clause (AND combines with result)
        if len(current_clause) >= 1:
            clause_patterns.append(current_clause)
        current_clause = []

print(f"\nFound {len(clause_patterns)} potential clause patterns")

# Since extracting exact clauses is complex, let's try angr again with better setup
print("\nTrying angr approach with better constraints...")
