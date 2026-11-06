# Dante's Trial

**Category:** Reversing | **Difficulty:** Hard | **Flag:** `srdnlen{W1H31l}`

## Overview
A GBA ROM (`dantestrial.gba`) built with the Butano engine contains a virtual machine that reads player input and hashes it with a custom FNV-1a variant. The correct input produces hash `0x73f3ebcbd9b4cd93`.

## Solution

### 1. Identify the VM
The ROM contains a custom bytecode interpreter with 16 opcodes, dispatched via a permutation table and XOR-encoded bytecodes. The 169-byte bytecode program at ROM offset 0x22654 encodes a simple loop: read input character → hash it → repeat until input exhausted.

### 2. Reverse the Hash Function
The hash function is a custom FNV-1a 64-bit variant:
- **Per character**: XOR with char, multiply by FNV prime, XOR with running index, multiply by FNV prime, S-box substitution XOR, multiply by golden ratio constant, XOR-shift mixing
- **Finalization**: XOR low 32 bits with index, multiply by FNV_PRIME (0x100000001B3), then MurmurHash3 fmix64

A critical subtlety: the finalization's multiply-by-FNV_PRIME is implemented via a shift-add chain in ARM Thumb code. The instruction `lsls r0, r6, #0x1f` (left shift by 31) was initially misread as a right shift, leading to a wrong multiplier of 691. Verification with Unicorn ARM emulation caught this bug.

### 3. Brute Force
With the corrected hash function verified against Unicorn emulation, an OpenMP-parallelized C brute force searched all printable ASCII strings:
- Lengths 1-5: exhausted, no match
- Length 6: found **`W1H31l`** matching hash `0x73f3ebcbd9b4cd93`

The brute force code (`brute2.c`) precomputes partial hash states and parallelizes the outer loop across CPU cores.

### Key Files
- `brute2.c` — Corrected C brute force with OpenMP
- `solve_correct.py` — Python hash implementation (verified against Unicorn)
- `vm_emu2.py` — VM bytecode emulator

## Key Takeaways
- **Always verify disassembly carefully** — ARM Thumb `lsls` vs `lsrs` is a single-bit difference that completely changes the computation
- **Use Unicorn emulation as ground truth** — when your static analysis disagrees with dynamic execution, trust the dynamic result
- **Shift-add chains encode multiplications** — a sequence of shifts, adds, and subtracts computes `x * constant` without a multiply instruction. Trace the math to recover the constant
- **Precompute partial states** for brute force — saves enormous time when the hash is iterative
