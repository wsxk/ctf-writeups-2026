# Trace

**Category:** Rev | **Author:** bekkaze | **Flag:** `HZ{K0MqQVOo_tr4c3_fl4g_Xv_Gk2Lk}`

## Challenge Description

A single stripped x86-64 ELF (`chall`). It is built like a line of locked rooms:
the first code block runs normally, but every later block is **encrypted**. Each
block deliberately crashes, and a signal handler hashes the code that just ran
and uses that exact hash to decrypt the next block.

> "You only get the next stage if you followed the intended path through the
> current one."

That also explains the hint about "watching too hard": ordinary debugging is
awkward because the program intentionally uses `SIGILL`, `SIGFPE`, and `SIGSEGV`
as normal control flow.

## Initial Analysis

```console
$ file chall
chall: ELF 64-bit LSB executable, x86-64, statically linked, stripped
$ checksec --file=chall
    RELRO: Partial | Stack: No canary | NX enabled | No PIE (0x400000)
$ echo test | ./chall
fail
```

The section table is the giveaway — six suspicious executable sections plus a
16-byte target:

```
trace_r0  0x48c000  size 0x23    (only this one disassembles cleanly)
trace_r1  0x48c023  size 0x03
trace_r2  0x48c026  size 0x0c
trace_r3  0x48c032  size 0x05
trace_r4  0x48c037  size 0x03
trace_r5  0x48c03a  size 0x105
trace_tgt 0x4b9b30  size 0x10
```

`main` (`0x40204f`) marks those pages RWX, installs one handler for signals
4/8/11, reads up to 63 bytes of input, calls `trace_r0`, then deliberately
writes through a null pointer to kick off the chain.

## The Vulnerability / Core Concept

The **signal handler is the real stage loader** (`0x401f67`). Simplified:

```c
uint64_t h = fnv1a64(current_stage_start, current_stage_size);
update_hidden_state(h);
xor_decrypt(next_stage_start, next_stage_size, h);
if (next == 5) xor_decrypt(trace_target, 16, h);
current_stage = next;
ctx->rip = next_stage_start;   // resume in the freshly decrypted stage
```

Two primitives:

- **Stage hash:** 64-bit **FNV-1a** over the plaintext of the current stage
  becomes the key for the next.
- **Stream cipher:** **SplitMix64** seeded with that hash, generating 8 key
  bytes at a time XORed into the next stage (`0x401ea2`).

Intended crash chain: `r0 -SIGSEGV-> r1 -SIGILL-> r2 -SIGFPE-> r3 -SIGSEGV->
r4 -SIGILL-> r5`. The tiny middle stages are literally just `ud2`, `div ecx`
(÷0), and null writes.

Starting from the already-plaintext `trace_r0`, we can statically walk the whole
chain: hash a stage, decrypt the next. Hashing `trace_r4` decrypts both
`trace_r5` and the 16-byte target.

The final stage (`trace_r5`) demands exactly **16 lowercase hex characters**,
parses them as two 32-bit words, appends two words of hidden state (accumulated
from the stage hashes: `s1_low=1fe7b575`, `s2_low=45188a4d`), runs all four
through an **8-round ARX mixer** (`0x401f0f`), and compares against the decrypted
target. Every operation in the mixer is reversible — rotations, XOR, add mod
2^32, and a multiply by the odd constant `0x9e3779b1` (invertible mod 2^32).

## Exploitation

Two scripts:

- **`decrypt.py`** — walks the FNV-1a/SplitMix64 stage chain, decrypts every
  `trace_r*` section and the target, and writes `chall.dec`. Recovers the target
  `a772101b00c1d4e32e8beb312ce210e7`.
- **`solve.py`** — recomputes the hidden state from the stage hashes and inverts
  the 8-round ARX mixer (applying the inverse round in reverse constant order),
  starting from the decrypted target:

```python
INV_M = pow(0x9e3779b1, -1, 1 << 32)
b = ror(ap, 5)
d = ror(cp ^ bp, 11)
c = ((bp - rol(d, 9)) & MASK32) ^ dp
a = ((((dp * INV_M) & MASK32) ^ ((rol(d, 7) + k) & MASK32)) - b) & MASK32
```

This recovers `4454141a 1ade29e1 1fe7b575 45188a4d`; the last two words match the
state derived from the hashes (a nice sanity check), and the first two form the
key:

```console
$ echo 4454141a1ade29e1 | ./chall
correct key. This handout build has no flag baked in — submit this key to the
live service to receive your HZ{...} flag.
```

The key was submitted to the live bearer-authenticated WebSocket service (token
supplied by the CTF platform) to return the flag:

```console
$ websocat -H='Authorization: Bearer <TOKEN>' 'wss://<HOST>/'
4454141a1ade29e1
HZ{K0MqQVOo_tr4c3_fl4g_Xv_Gk2Lk}
```

## Flag

```
Key:  4454141a1ade29e1
Flag: HZ{K0MqQVOo_tr4c3_fl4g_Xv_Gk2Lk}
```

## Key Takeaways

- Crashes as intentional control flow: don't fight the signals — recognize that
  the signal handler *is* the stage loader, and that rewriting `ctx->rip`
  resumes execution at the decrypted stage.
- A self-decrypting binary keyed on the hash of its own prior stage can be fully
  unrolled statically, since stage 0 ships in plaintext.
- ARX constructions built only from rotate / XOR / add / odd-multiply are always
  invertible — no brute force needed.
