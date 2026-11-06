#!/usr/bin/env python3
"""
Solve the 3-SAT problem using Z3 by extracting constraints from the binary.
"""
from z3 import *
import subprocess
import struct

BINARY = "/home/kali/Downloads/lactf2025/rev/threesatproblem/three_sat_problem"
INPUT_LEN = 0x4ff  # 1279

# Read the binary
with open(BINARY, 'rb') as f:
    binary_data = f.read()

# Input buffer is at 0x15060 (relative to segment start, .bss)
# In the check function, addresses are relative to RIP
# Let's look at the pattern more carefully

# Actually, let's just try brute-force with constraints
# From the analysis, bit 754 (offset 0x2f2) must be '1'

# Let me try a simpler approach - use the z3 to model the problem
# Since this is 3-SAT, we have 1279 binary variables

# Create Z3 boolean variables
bits = [Bool(f'b{i}') for i in range(INPUT_LEN)]

s = Solver()

# Constraint: bit 754 must be True (from the main function check: data_415352 & 1)
# 0x15352 - 0x15060 = 0x2f2 = 754
s.add(bits[754] == True)

# Now we need to extract the actual 3-SAT clauses from the binary
# Let me analyze the function more carefully

# From the disassembly, the check function at 0x1289 does:
# 1. Loads bytes from input buffer at various offsets
# 2. Computes NOT of each
# 3. Stores into local variables on stack
# 4. Then combines them with OR operations to form clauses

# Let's extract the pattern by looking at the return logic
# The function should return 1 only if ALL clauses are satisfied

# For now, let's try to solve by just running the binary with different inputs
# and see if we can find a pattern

# Actually, let me extract the clause structure by analyzing the binary
# Looking at the end of the function to see how the result is computed

# Dump the end of the check function
import os

# Let's use objdump to get the full function
result = subprocess.run(
    ['objdump', '-d', BINARY],
    capture_output=True, text=True
)
disasm = result.stdout

# Find the function and extract it
lines = disasm.split('\n')
in_func = False
func_lines = []

for line in lines:
    if '1289:' in line and 'push' in line:
        in_func = True
    if in_func:
        func_lines.append(line)
        if 'ret' in line.lower() and '12981' in line:
            break

print(f"Function has {len(func_lines)} lines of disassembly")

# Look for patterns that indicate clause checking
# In 3-SAT, typically we see: load var1, OR var2, OR var3, AND with accumulator
# Let's find OR patterns

or_count = 0
and_count = 0
for line in func_lines:
    if '\tor' in line.lower():
        or_count += 1
    if '\tand' in line.lower():
        and_count += 1

print(f"Found {or_count} OR operations and {and_count} AND operations")

# Let's look at the last 100 lines to understand the final check
print("\n=== Last 50 lines of function ===")
for line in func_lines[-50:]:
    print(line)
