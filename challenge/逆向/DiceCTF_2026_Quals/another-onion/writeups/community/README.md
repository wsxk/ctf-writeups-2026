# another-onion

**Category:** Reversing | **Difficulty:** Hard | **Flag:** `dice{5p33d_1s_a1s0_imp0rtant_1n_r3ver5e_3ngineer1ng}`

## Overview

You're given an "onion" binary that decrypts itself layer by layer. Each layer reads 2 key bytes from stdin, uses SHA-256 NI hardware instructions to derive a keystream, XOR-decrypts the next layer's code, then jumps to it. The example binary has 8 layers (16-byte key). Spin up an instance to get a real binary with 256 layers (512-byte key) — solve it within 30 minutes.

## Solution

### Understanding the Layers

Each layer follows the same structure:
1. **SHA-256 init loop** — reads 16-byte chunks from BSS through `sha256rnds2` hardware instructions (loop from `rax=-0x10` to `0xfff0`)
2. **Read 2 key bytes** — two `read(0, &byte, 1)` syscalls via `read@plt`
3. **SHA rounds with key** — mixes key bytes into SHA state
4. **XOR 128 bytes of buffer** at `0x90000000` using SHA output
5. **XOR-decrypt next layer's code** in `.text` using buffer content
6. **Jump/call to next layer**

The last layer calls `putc@plt` to print "Congratulations!" and a submission token.

### The Oracle

Wrong key bytes produce garbage code for the next layer. Right key bytes produce valid code containing exactly 2 `call read@plt` instructions (the next layer's read calls). This gives us a brute-force oracle: try all 65536 candidates per layer, check which one decrypts to valid code.

### Building a Fast Solver

The challenge name hints at it, and the flag confirms: **speed is everything**. At 65536 candidates per layer and 256 layers, you need thousands of candidates per second. Here's the evolution:

| Approach | Speed | 256-layer estimate |
|----------|-------|--------------------|
| Python subprocess | ~2/s | days |
| Ptrace fork injection | ~119/s | 6+ hours |
| JIT with fork-per-candidate | ~1000/s | 140 min |
| Shared BSS + parallel workers | ~3500/s | **~17 min** |

The winning approach (`solve_real.c`):

1. **JIT execution** — Map the binary's memory (`.text`, BSS, buffer) into the solver process at the same virtual addresses. Compile the solver at `0x10000000` to avoid overlap.

2. **Patch and execute** — Replace `read@plt` with a `fake_read()` that injects candidate bytes. Replace the tail `jmp`/`call` to next layer with `ret`/NOP. Execute each layer's code directly as a function call.

3. **Fork-per-candidate COW isolation** — Each candidate runs in a forked child. Copy-on-write means the child gets its own copy of modified pages without expensive memcpy.

4. **Shared BSS optimization** — The 16MB+ BSS is read-only during computation (only SHA state at `0x4f1080` gets written). Store BSS in `/dev/shm`, map it `MAP_SHARED` in the parent, then children remap it `MAP_PRIVATE` from the file. This reduces fork overhead from 16MB page-table setup to ~4KB.

5. **32 parallel workers** — Split the 65536 candidate space across 32 worker processes. Each worker forks JIT children independently. First worker to find the answer signals via shared memory.

### Adapting for the Real Binary

The real binary differed from the example in several ways:
- Uses `call` (0xe8) instead of `jmp` (0xe9) for layer transitions — tail patching needed 5-byte NOP instead of `ret` to avoid stack corruption
- BSS extends far beyond ELF MemSiz via kernel brk mapping (had to map up to `0x8000000`)
- 257 layer addresses spanning `0x400410` to `0x4dd860`

### The Solve

```bash
gcc -O2 -msha -msse4.1 -no-pie -Wl,-Ttext-segment=0x10000000 -o solve_real solve_real.c -lrt
./solve_real ./real_onion 512 32
```

All 256 layers solved in **1012 seconds (~17 minutes)**, well within the 30-minute limit. The binary printed a token, which we submitted to the instance to get the flag.

## Key Takeaways

- The flag says it all: `5p33d_1s_a1s0_imp0rtant_1n_r3ver5e_3ngineer1ng`. This challenge is fundamentally about building a fast brute-force engine, not just understanding the binary.
- **JIT execution** (mapping binary memory into your solver and running code directly) is massively faster than ptrace-based approaches.
- **Copy-on-write via fork** is the cheapest way to get memory isolation per candidate. Shared BSS + private remap makes fork nearly free.
- **SHA-NI instructions** (`sha256rnds2`, `sha256msg1`, `sha256msg2`) work even when not advertised in CPU flags — don't trust `/proc/cpuinfo`.
- Real vs example binaries can differ in subtle ways (`call` vs `jmp`, BSS size, address ranges) — build your solver to handle both.
