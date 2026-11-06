# Automaton

**Category:** Rev | **Difficulty:** Hard | **Author:** xyptonize | **Flag:** `HZ{TF98xY04_byt3c0d3_c0unt3rp4rt_L3XH5QDC}`

## Challenge Description

A WebAssembly module, `gate.wasm`, guards a channel: hand it the right token and
it opens, anything else and it stays shut. It does not compare your token to a
stored string — it runs the token through a little machine of its own and checks
the result. Recover the accepted token; that token *is* the flag.

Handout (see `challenge_README.md`): `gate.wasm`, plus `run.html` and
`runner.mjs` to test a candidate in a browser or with Node. The module exports
`get_input()` (address of a 64-byte input buffer) and `check(len)` (returns 1
for the accepting token, 0 otherwise). No network, no I/O, no anti-debug.

## Initial Analysis

Convert the module to text and dump its data:

```bash
wasm-objdump -x -s gate.wasm
wasm2wat --generate-names gate.wasm -o gate.wat
```

`check` first enforces the length:

```wat
local.get $p0
i32.const 42
i32.ne
br_if $B0      # required token is exactly 42 bytes
```

`get_input()` returns `1048787`, right after a single 211-byte data segment that
splits into three parts:

| Offset | Size | Purpose |
|---:|---:|---|
| 0  | 42  | Final byte sequence the correct input must produce |
| 42 | 9   | Tiny program that builds a 12-byte key |
| 51 | 160 | Encoded program for the main transformation VM |

## The Vulnerability / Core Concept

Everything is **reversible**, so instead of guessing an input and running the
machine forward, we start from the stored 42-byte target and undo every operation
in reverse order — that yields the unique accepting input.

Three layers:

1. **Key generator (9 bytes).** A 4-opcode mini-VM (multiply / xor-shift /
   xor-round-constant / emit-byte) run 12 times from initial state `c = 109`
   produces the 12-byte key `3a88c6adf6fd92edb25349da`.

2. **S-box.** That key feeds the standard RC4 key-scheduling algorithm, but the
   resulting `S` is used only as a deterministic 256-byte substitution table (a
   permutation, hence invertible).

3. **Main VM (160 bytes).** The program is obfuscated with a byte-at-a-time
   recurrence (`output = state ^ enc; state = (enc - 75*state + 59) & 0xff`,
   using the *old* state), decoding to 114 instructions from a 14-opcode set
   (opcodes 17–30): add/xor/rotate all bytes, S-box substitution, prefix and
   suffix add/xor/rotate/multiply chains, indexed adds, swaps, etc.

Every opcode has a clean inverse: add<->sub, xor is self-inverse, rol<->ror,
S-box<->inverse-S-box, multiply via modular inverse mod 256 (all multipliers are
odd), and the left-to-right chains are undone right-to-left (and vice versa).

## Exploitation

`solve.py` reproduces the key generator, builds the S-box and its inverse,
de-obfuscates and parses the 114-instruction program, then applies each opcode's
inverse from last to first starting at the 42-byte target:

```python
candidate = target
for opcode, arguments in reversed(program):
    candidate = undo(candidate, opcode, arguments)
print(bytes(candidate).decode("ascii"))
```

```console
$ python3 solve.py
HZ{TF98xY04_byt3c0d3_c0unt3rp4rt_L3XH5QDC}

$ node runner.mjs gate.wasm 'HZ{TF98xY04_byt3c0d3_c0unt3rp4rt_L3XH5QDC}'
Correct — that is the flag.
```

## Flag

```
HZ{TF98xY04_byt3c0d3_c0unt3rp4rt_L3XH5QDC}
```

## Key Takeaways

- When a checker *transforms* input and compares the result (rather than storing
  the answer), the winning move is usually to invert the transform end-to-end.
- WABT (`wasm2wat`, `wasm-objdump`, `wasm-decompile`) makes WASM reversing
  approachable; the interesting logic lives in the embedded *bytecode program*,
  not the exported functions.
- Chained byte operations are still invertible — just process them in the
  opposite direction so you never clobber a value before it is needed.
