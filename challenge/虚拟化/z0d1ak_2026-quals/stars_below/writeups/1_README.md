# stars-below

**Category:** Reversing | **Points:** 500 | **Author:** afish | **Flag:** `zdk{TH3_Lo4d3R_Dr34MS_IN_pA63_8ouNd4rIEs}`

## Description
> The drowned observatory still charts a sky.

## TL;DR
An SDL "drowned observatory terminal" that wants three inputs: an 8-digit route, a callsign derived from it, and a custom-Base32 ticket carrying the initial state of two reversible VMs. The headline trick is a **loader trap** — the imported function names a decompiler shows are deliberately wrong (shuffled relocations + `LD_BIND_NOT=1`). Once fixed, the route brute-forces from `8! = 40,320` possibilities and the two VMs run backward from their required final state.

The winning inputs:
```
Route:    16403752
Callsign: PELAGOS9
Ticket:   X7W2KW9NVJBMHQNM24X6WWAM7FFBZPA34ZE7EHY79UFDJSCZ6PSV8MSKRD
```

## Initial Analysis

A stripped, statically-flavored x86-64 ELF `stars_below`. `PUBLIC.md` documents a headless mode: `./stars_below --headless ROUTE CALLSIGN TICKET`. Bad input only prints *"the relay remains silent"* — a poor oracle, but headless mode lets us test a full answer without SDL.

## Vulnerability / Core Concept

**The loader-shaped trap.** Opening the binary, code that looks like `strstr()` behaves like `memcpy()`; "SDL" calls appear inside hashing and memory code. Linux normally calls imports through PLT stubs whose GOT entries the loader fills in on first use. `stars_below` **rearranges the `.rela.plt` relocation records** so PLT labels and real destinations disagree, then re-executes itself with `LD_BIND_NOT=1` so the loader never permanently caches a resolved entry — every call keeps going through the lazy resolver and the shuffled table. It also strips `LD_PRELOAD`/`LD_AUDIT`/`LD_BIND_NOW` to block casual bypasses. Parse `.rela.plt` yourself and match each PLT stub's pushed relocation index to the relocated symbol; the decompiler becomes believable. This is the flag's "loader dreams in page boundaries."

**The route.** The parser wants 8 digits, each `0..7`, no repeats — a permutation of `01234567`. A small table-driven 32-bit hash must equal `0xf06f770b`. Only `8! = 40,320` candidates, so reproduce the hash in Python and check all permutations → unique `16403752`.

**The callsign.** Each route digit indexes the string `AP9GLSEO`, spelling `PELAGOS9`. It's bound to the rest via BLAKE2s (note the domain strings include their terminating NUL):

```python
name_hash = blake2s(b"stars-below/name/v1\0" + bytes([len(name)]) + name).digest()
```

A "name guard" hash over `name_hash` + a salt matches the embedded guard, confirming route + callsign.

**The ticket.** Custom Base32 alphabet `87RJF2ACZLVUMXB3D6GH9WNSYP5QK4ET`, 58 symbols → 36 bytes = `32-byte payload || 4-byte MAC` (MAC = first 4 bytes of a keyed BLAKE2s). The 32-byte payload is eight little-endian `u32`s = the starting registers of **VM A**.

## Exploitation

Two custom bytecode interpreters, each **XOR-decrypted in 32-byte BLAKE2s keystream blocks**. VM A's key is derived from `name_hash`, the validated route hash `0xf06f770b` (as LE u32 — *not* the decimal `16403752`), and a salt. VM B's key additionally includes the hash of the decrypted VM A program, so a wrong route/callsign yields meaningless bytecode instead of a "wrong" message.

Both VMs are **rounds of reversible ARX**. Each round has a BLAKE2s-derived schedule: a register permutation of `0..7`, six round constants, six rotations. Example (VM A):

```
a = a + ROL(b XOR q[base], s[base])
c = c XOR (a * q[base+2])
d = ROR(d + c, s[base+1])
b = b XOR ROL(d + q[base+1], s[base+2])   # then swap regs p1,p6
```

VM B uses the mirrored ops and swaps `p0,p7`. Every op inverts (add↔sub, XOR self-inverse, ROL↔ROR; multiplication never needs inverting because its input register is still live going backward). **Gotcha:** each round uses a *different* register permutation — reusing round-0's numbers gives a self-consistent-but-wrong model. Compare a compact round function against a literal bytecode emulator to catch this.

The required VM B final state isn't a one-way check — it's generated from the callsign hash:

```python
target = blake2s(b"stars-below/target/v1\0" + name_hash + target_salt).digest()
```

Recovery: start from VM B's target state → undo VM B's 19 rounds → undo the A↔B bridge (`b_initial[i] = ROL(name_word[i], i+1) ^ a_final[perm[i]]`, perm `[0,2,6,3,5,1,4,7]`, XOR-invertible) → undo VM A's 24 rounds → serialize eight words = the ticket payload:

```
686a5e569650dcc9eecc2f5b1ad4cc0908e464cfea3c1f4f01a2c901dce88e6e
```

Append the 4-byte MAC (`a032fc14`), Base32-encode with the custom alphabet → the ticket. `solve_invariant.py` (Z3 over the 8 arithmetic invariants) and `vm.py` (literal emulator) are the helper tools used to validate the recovery.

```console
$ ./stars_below --headless 16403752 PELAGOS9 \
    X7W2KW9NVJBMHQNM24X6WWAM7FFBZPA34ZE7EHY79UFDJSCZ6PSV8MSKRD
zdk{TH3_Lo4d3R_Dr34MS_IN_pA63_8ouNd4rIEs}
```

> Excluded from this directory: the `stars_below` binary and its analysis blobs (`progA.bin`, `progB.bin`, etc.). Included: `solve_invariant.py` (route/invariant Z3 solver) and `vm.py` (VM emulator).

## Flag
`zdk{TH3_Lo4d3R_Dr34MS_IN_pA63_8ouNd4rIEs}`

## Key Takeaways
- **Don't trust import names in a hostile ELF** — the relocation table is the source of truth, and `LD_BIND_NOT` keeps a shuffled GOT effective all run.
- **A custom VM is less scary once grouped into repeated rounds.**
- **Reversible ARX (add, XOR, rotate, swap, careful mul) inverts** without a solver — walk it backward from the target.
- **Always diff a simplified model against a literal interpreter** — a reversible-but-inaccurate model fools its own self-test.
- **Domain separators often include their NUL byte** — miss it and every later hash/key is wrong.
