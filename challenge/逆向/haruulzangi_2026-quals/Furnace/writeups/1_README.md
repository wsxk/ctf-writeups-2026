# Furnace

**Category:** Rev | **Author:** ByamB4 | **Flag:** `HZ{r1ght_h34t_r1ght_s33d_4e8d3311afafa4fa4584739c27c1f770}`

## Challenge Description

A Minecraft (NeoForge) mod, `furnace-1.0.0.jar`. The mod is mostly a fancy UI:
it downloads a small encrypted "firmware" program, hands that program and our
128-bit key to a native library, and checks the result against a target supplied
by the server. Submit the right ignition key and the server returns an image
containing the flag.

## Initial Analysis

A JAR is a ZIP of compiled classes and resources:

```bash
unzip -l furnace-1.0.0.jar
```

Key entries: `Kiln.class`, `client/FurnaceScreen.class`, `client/SmeltApi.class`,
`natives/linux-x86-64/libfurnace.so`, and `furnace-client.properties` (the
endpoint + team token — redacted in this repo).

Inspect the bytecode without Minecraft:

```bash
javap -p -c -constants mn/haruulzangi/furnace/client/SmeltApi.class
```

`SmeltApi` stores its route names as integer arrays XOR-encoded with `0x5c`.
Decoding them:

```
/mc/firmware   /mc/target   /mc/smelt   target   key
```

The first two are GET; `/mc/smelt` expects `{"key":"<32 hex chars>"}`. The server
returns:

```json
{ "target": "3390ad96e04fdc789e2d27c000000000", "pin": "98aea14f1a7d95f0", "work": 38 }
```

`Kiln.class` declares `native long[] fireNative(byte[] firmware, long keyHi, long keyLo)`.
The checker (`FurnaceScreen.seated()`) requires:

1. `result[0] == targetHi` and `(result[1] & ~((1<<work)-1)) == targetLo` — i.e.
   the top 26 bits of the second word match, the **bottom 38 are ignored**.
2. `first 8 bytes of SHA-256(keyHi||keyLo) == pin`.

## The Vulnerability / Core Concept

The native transform is a tiny **reversible VM**. `libfurnace.so` is stripped but
must export the JNI entry `Java_mn_haruulzangi_furnace_Kiln_fireNative`. It uses
bitwise identities for add/sub which, once renamed, make the logic clear.

**Firmware encryption:** first 8 bytes are a seed; the rest is XORed with a
keystream generated in 32-byte blocks by a 4-word, 20-round ARX generator (see
`solve.py::stream`). Decrypting reveals the VM program.

**The VM:** header is a 16-byte opcode permutation (so opcodes aren't sequential)
followed by a big-endian length. It runs two 64-bit registers `a`/`b` (init from
key hi/lo) through 40 instructions from a 16-op set: xor/add/sub/mul immediates,
rol/ror, xor-shift left/right, register mixes, NOT, swap, and two
`mix = a ^= (rol/ror(b,n) + b*const)` ops.

**Everything is invertible:** add<->sub, rol<->ror, xor self-inverse, NOT/swap
self-inverse, multiply by the odd constant `0x0c67282807d34633` via its modular
inverse `0x65f48f17311924fb` mod 2^64, and xor-shift undone by the doubling-shift
trick. So each of the `2^38` possible full outputs maps backward to exactly one
candidate key.

**The search:** `work = 38` hides the bottom 38 output bits, so for each suffix
`s` in `[0, 2^38)` we form `out_lo = 0x9e2d27c000000000 | s`, run the VM
backward to a candidate key, and keep the one whose `SHA-256[:8]` equals the pin.
`2^38` ≈ 275 billion — too many for Python.

## Exploitation

- **`solve.py`** — full firmware decryptor, VM parser, forward emulator (verified
  against the real JNI library, see `TestKiln.java`), and inverse VM with a
  random-input self-test (`unfire(fire(x)) == x`).
- **`brute.cu`** — CUDA kernel implementing the inverse VM plus a one-block
  SHA-256 to sweep all `2^38` suffixes. On a Titan X it ran ~0.85 B/s and found:

```
suffix = 2dfd71ad37
key    = 5cc32427829aabb966286cdb5467786b
```

Verification: forward VM gives `3390ad96e04fdc789e2d27edfd71ad37` (correct fixed
prefix), and `SHA-256(key)[:16] == 98aea14f1a7d95f0` (the pin). Submitting the
key to `/mc/smelt` returned a 640x200 PNG (`face.png`) with the flag.

## Flag

```
HZ{r1ght_h34t_r1ght_s33d_4e8d3311afafa4fa4584739c27c1f770}
```

## Key Takeaways

- Multi-layer challenge (Java bytecode -> native ELF -> custom VM) yields to
  peeling one layer at a time and testing each against ground truth.
- An opcode permutation in the VM header is cheap obfuscation; recover the map
  first, then the program reads normally.
- A reversible transform + a "work factor" that hides low output bits turns a
  128-bit key search into a `2^work` suffix search — feasible on a GPU when the
  server also hands you a hash prefix (pin) to confirm the unique answer.
- Only ships the crypto ignition key; the flag lives server-side behind the
  smelt endpoint.
