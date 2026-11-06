# locked-in

**Category:** Reversing | **Difficulty:** Medium | **Flag:** `dice{y0u_w3r3_v3rY_l0Ck3d_1n!}`

## Overview
A statically-linked stripped ELF binary runs a custom stack-based VM with 16 concurrent threads to verify a 30-character flag.

## Solution

### Binary Structure
The binary (`locked_in`) implements a stack-based VM that loads bytecode from `flag_verifier.bin` (5420 uint64 values, 4276 instructions). The VM uses Linux futex syscalls for thread synchronization and a channel-based inter-thread communication system.

### VM Architecture
- 32 opcodes (0x00-0x1f): stack operations, arithmetic, control flow, threading, I/O
- 16 threads spawned at startup, each handling a different part of the verification
- Channels use 4 memory slots each: mutex, full flag, ready flag, data
- Key channel primitives: put, get, read, write, send (put+get)

### Verification Pipeline

**Input Processing (Threads 13, 15):**
Thread 13 reads 30 chars from stdin. Thread 15 XORs each byte with a position-dependent constant (scramble values). Bytes are processed in **reverse order** (position 29 first).

**Transformation Pipeline (Threads 10, 11, 9, 12):**
Each XORed byte goes through: `XOR 0x5a → rotate_left_1 → XOR 0x5a → bitmangle → XOR 0x5a`

The bitmangle (thread 9) uses an empirical formula:
- If LSB=0: `(val ^ 254) & 0xFF`
- If LSB=1: `((val*2) & 0xFF) ^ val`

**Base-4 State Machine (Threads 7, 6, 5):**
Thread 7 encodes each transformed byte as 4 base-4 digits (LSB first). Thread 6 applies each digit to a packed (high, low) accumulator:
- Digit 0: high--
- Digit 1: high++
- Digit 2: low *= 2
- Digit 3: low //= 2

After each digit, thread 5 checks `lookup_table[high] & low`. The logic is **inverted**: a zero result means the move is valid (the state advances), while non-zero means blocked (state reverts to previous).

**Final Check (Thread 8):**
After all 120 digits (30 bytes × 4 digits), the accumulator must equal `0xE00000002` (high=14, low=2).

### Key Constants
- **Initial accumulator:** `0x400020000` (high=4, low=0x20000)
- **Target:** `0xE00000002` (high=14, low=2)
- **XOR scramble values:** extracted via GDB breakpoint on the XOR handler
- **Lookup table:** 16 uint32 values extracted from memory stores during execution
- **Critical discovery:** `unlock_pi` on unowned mutex returns errno=EPERM=1, changing all scramble computations

### Solving
BFS through the state space: for each of the 24 unknown byte positions, try all printable ASCII values, compute the 4 base-4 digits, check if the path through the state machine is valid. The state space stays small (~100 states per position) because the lookup table constrains valid transitions.

Reference: `solve11.py` for the full solver.

## Key Takeaways
- Custom VM challenges benefit from hybrid static+dynamic analysis: use static analysis for structure, GDB for runtime values
- The `unlock_pi` returning EPERM=1 was a critical detail that changed all constant computations
- Channel-based inter-thread communication requires careful stack tracing to understand data flow
- Inverted validity checks (0 = valid) can be discovered by comparing GDB traces against expected behavior
- BFS over state machines is effective when the state space is bounded
