# Roulette

**Category:** Reversing | **Difficulty:** Medium-Hard | **Flag:** `UMDCTF{I_R3ALLY-want-to-pl4y-the-p0werball,+but-my-d4d-said-no-so-im-b3tting-ill-win-on-POLYMARKETinstead}`

## TL;DR

A statically-linked stripped ELF that hides a 27-iteration loop behind a CRT (Chinese Remainder Theorem) computation and a custom bytecode VM. The twist: there's nothing to invert. Every input byte is deterministically computed by simulating the check forward — you just need to trace the bytecode VM manually and realize each iteration uniquely pins down the next 4 bytes of the flag.

## What We're Given

A single binary called `roulette` and the challenge description: *"lets go gambling! make the dumb roulette machine accept your bet."*

```
$ file roulette
roulette: ELF 64-bit LSB executable, x86-64, statically linked, stripped
```

Statically linked and stripped — so no imported symbols to guide us, and no debug info. This is going to be a pure reversing job.

## Initial Recon

Running the binary gives us:

```
$ ./roulette
submit roulette number: 17
rejected
```

Playing around with small numbers (0–36, because, roulette) hits a handful of decoy paths. Try a number ≤36 and you get "rejected". Hit 36 exactly and something says "JACKPOT". There's apparently a path that prints a "Tesla msg" too. These are all red herrings designed to make you think the input is a numeric roulette bet.

The real check triggers when the input length is exactly **106 bytes** (0x6a). The very first validation the binary does is:

```c
if (strcspn(input, "\n") != 0x6a)
    puts("rejected");
```

So the "number" we're submitting isn't a number at all — it's a 106-character string that has to pass a much more involved validation routine.

## The Vulnerability / Trick

There's no vulnerability here in the exploitable sense. This is a pure reversing challenge. The trick is recognizing that the check, despite looking intimidating, is **entirely deterministic and forward-computable**. Every byte of valid input can be derived by just... running the check logic yourself in Python and reading off what it expects.

Let's break down what the validation function actually does.

### Step 1: Split Input Into 27 uint32s

The 106 input bytes get sliced into 27 little-endian 32-bit integers. 27 × 4 = 108, so the last uint32 only has 2 real bytes from input — positions 106 and 107 are null (the null terminator from `fgets` and zero-initialized memory), which makes the last word well-defined.

### Step 2: Per-Iteration CRT Computation

For each iteration `i` from 0 to 26, the binary computes two values that depend on `i` and a running state variable `r15`:

```
a = rol(i*0x45d9f3b ^ 0x8aa115a0, (i%13)+3) % r8
rdi_5 = T_499de0[i] ^ a

b = rol(r15 ^ 0x28d88f59, (i%11)+5) % r10
arg3  = T_499d60[i] ^ b
```

Where `r8` and `r10` come from two lookup tables (`T_499ee0` and `T_499e60`), and `T_499de0` / `T_499d60` are two more lookup tables — all baked into the binary's data section.

Then it runs **Chinese Remainder Theorem** to combine these into a single 32-bit value:

```
rax_12 = CRT(rdi_5 mod r8, arg3 mod r10)
```

CRT — Chinese Remainder Theorem — is a way to combine two modular equations into one unique solution modulo the product of the two moduli. It's a common tool in number theory and shows up constantly in RSA-style crypto challenges. Here it's just mixing two lookup-table-derived values into one "seed" for the next step.

### Step 3: The Bytecode VM

This is the spicy part. The binary has a small bytecode interpreter. It reads 8-byte instructions from a blob at address `0x499be1`, with this layout:

- `byte[0]` = destination register
- `byte[1]` = source register  
- `bytes[3..6]` = 32-bit immediate
- `byte[7]` = opcode

There are 8 registers (R0..R7). The weird part: every instruction starts with an implicit `R[dst] = R[src]` move, *before* the opcode is even read. Then:

| Opcode | Operation |
|--------|-----------|
| 0, 1   | NOP (the implicit move already ran) |
| 2      | `R[dst] ^= R[src]` |
| 3      | `R[dst] ^= imm` |
| 4      | `R[dst] += R[src]` |
| 5      | `R[dst] += imm` |
| 6      | `R[dst] *= imm` |
| 7      | `R[dst] = rol(R[dst], imm)` |
| 8      | `R[dst] = rol(R[dst], R[src])` |
| 9      | `R[dst] >>= imm` |
| 0xff   | Halt — return R[6] |

"Real" opcodes (2-9) read their operand bytes from the *next* slot, so they consume 16 bytes total. NOP opcodes only consume 8. This means you have to be careful tracing through the bytecode — it's not a fixed-width instruction stream in the naive sense.

The VM starts with initial state: `R0 = rax_12`, `R1 = rbx` (a running accumulator), `R2 = i`. R3..R7 start at zero.

After tracing through all 28 slots of the bytecode, I noticed the constants being used: `0x9e3779b9`, `0x85ebca6b`, `0xc2b2ae35`, `0x27d4eb2f`, with shifts of 16 and 13. If you've done hash-related challenges before, those numbers scream **MurmurHash3 finalizer**. The VM is essentially running a hash-mixing step on the three inputs.

### Step 4: The Check

After the VM runs and produces output H (from R[6]):

```
input_uint32[i] == H ^ T_499ce0[i]
```

That's it. The expected input uint32 at position `i` is just `vm_output XOR table_entry`. And `vm_output` is a deterministic function of `(rax_12, rbx, i)` — all of which we know at the time we're computing iteration `i`.

After checking, `rbx` updates:

```
rbx = rol((rax_12 * 0x45d9f3b) ^ rbx ^ input_uint32[i], (i%5)+7) + r15 - 0x61c88647
r15 += 0x7f4a7c15
```

The running state flows forward iteration by iteration. There's no branching based on unknown data — it's all a one-way chain.

## Building the Exploit

The solve is refreshingly clean once the structure is clear. We just simulate the entire check forward in Python, computing what each `input_uint32[i]` must be, then write out the bytes.

First, rip the lookup tables directly from the binary file:

```python
with open('roulette', 'rb') as f:
    data = f.read()

def read(vaddr, n):
    off = vaddr - 0x499000 + 0x99000
    return data[off:off+n]

T_499d60 = list(struct.unpack('<27I', read(0x499d60, 27*4)))
T_499de0 = list(struct.unpack('<27I', read(0x499de0, 27*4)))
T_499e60 = list(struct.unpack('<27I', read(0x499e60, 27*4)))
T_499ee0 = list(struct.unpack('<27I', read(0x499ee0, 27*4)))
T_499ce0 = list(struct.unpack('<27I', read(0x499ce0, 27*4)))
```

The address math here is just converting virtual addresses to file offsets — the binary maps its data segment at 0x499000, which sits at file offset 0x99000.

Next, implement the CRT and the VM. The VM is the fun part — we traced through each slot of the bytecode and translated it into straight-line Python:

```python
def vm(r0, r1, r2):
    R = [0]*8
    R[0] = r0; R[1] = r1; R[2] = r2
    R[3] = R[1]                              # slot0 implicit mov
    R[3] = (R[3] + 0x6c8e9cf5) & MASK        # slot1 add imm
    R[3] = R[3] ^ R[0]                       # slot2 xor reg
    R[3] = rol(R[3], R[2] & 31)              # slot3 rol reg
    R[3] = (R[3] * 0x7feb352d) & MASK        # slot4 mul imm
    R[3] = (R[3] + 0x846ca68b) & MASK        # slot5 add imm
    R[4] = R[0]                              # slot6 implicit
    R[4] = rol(R[4], 7)                      # slot7 rol imm
    R[5] = R[1]                              # slot8 implicit
    R[5] = R[5] ^ R[4]                       # slot9 xor reg
    R[4] = R[2]                              # slot10 implicit
    R[4] = (R[4] * 0x9e3779b9) & MASK        # slot11 mul imm (MurmurHash3!)
    R[5] = (R[5] + R[4]) & MASK              # slot12 add reg
    R[4] = R[5]                              # slot13 implicit
    R[4] = R[4] >> 0x10                      # slot14 shr 16
    R[5] = R[5] ^ R[4]                       # slot15 xor reg
    R[5] = (R[5] * 0x85ebca6b) & MASK        # slot16 mul imm (MurmurHash3!)
    R[6] = R[5]                              # slot17 implicit
    R[6] = R[6] ^ R[3]                       # slot18 xor reg
    R[6] = rol(R[6], 0xb)                    # slot19 rol 11
    R[6] = (R[6] + 0xc2b2ae35) & MASK        # slot20 add imm (MurmurHash3!)
    R[7] = R[6]                              # slot21 implicit
    R[7] = R[7] >> 0xd                       # slot22 shr 13
    R[6] = R[6] ^ R[7]                       # slot23 xor reg
    R[6] = (R[6] * 0x27d4eb2f) & MASK        # slot24 mul imm (MurmurHash3!)
    R[7] = R[3]                              # slot25 implicit
    R[7] = rol(R[7], 3)                      # slot26 rol 3
    R[6] = R[6] ^ R[7]                       # slot27 xor reg
    R[6] = R[6] ^ 0xa5a5a5a5                 # slot28 xor imm
    return R[6]
```

Then the main loop:

```python
def solve():
    r15 = 0
    rbx = 0x8aa115a0
    out = bytearray()
    for i in range(27):
        r8  = T_499ee0[i]
        r10 = T_499e60[i]
        # Build the two CRT residues
        a     = rol((i*0x45d9f3b) & MASK ^ 0x8aa115a0, (i%13)+3) % r8
        rdi_5 = T_499de0[i] ^ a
        b     = rol(r15 ^ 0x28d88f59, (i%11)+5) % r10
        arg3  = b ^ T_499d60[i]
        # Combine with CRT
        rax_12 = crt(rdi_5, r8, arg3, r10)
        # Run the VM
        out_vm = vm(rax_12, rbx, i)
        # The expected input uint32 is just output XOR table entry
        rdi_6 = out_vm ^ T_499ce0[i]
        out += rdi_6.to_bytes(4, 'little')
        # Update running state
        rbx = (rol(((rax_12*0x45d9f3b) & MASK) ^ rbx ^ rdi_6,
                   (i%5)+7) + r15 - 0x61c88647) & MASK
        r15 = (r15 + 0x7f4a7c15) & MASK
    print(f"final rbx={rbx:#x} (expect 0x6286239c)")
    return out

result = solve()
with open('input.bin', 'wb') as f:
    f.write(result[:106])
```

The sanity check on `rbx` at the end confirms we got it right — if the final accumulator doesn't match `0x6286239c`, something went wrong in the chain.

## Running It

```
$ python3 solve.py
final rbx=0x6286239c (expect 0x6286239c)
Total bytes: 108
Last bytes: 0000
Input (first 106): b'UMDCTF{I_R3ALLY-want-to-pl4y-the-p0werball,...'
```

The `rbx` matches exactly. Then pipe the binary input to the binary:

```
$ ./roulette < input.bin
submit roulette number: accepted
```

Flag: `UMDCTF{I_R3ALLY-want-to-pl4y-the-p0werball,+but-my-d4d-said-no-so-im-b3tting-ill-win-on-POLYMARKETinstead}`

Truly the words of a man who has been told no.

## Key Takeaways

**The main lesson:** A check that looks cryptographically complex — CRT! custom VM! hash mixing! running accumulators! — can still be trivially solvable if there's no actual unknowns. Every iteration's output is determined by previous state that we control or can compute ourselves. The check is a one-way chain, not a puzzle that requires inversion.

**Spot the pattern:** When you see constants like `0x9e3779b9`, `0x85ebca6b`, `0xc2b2ae35`, `0x27d4eb2f` with shifts of 16 and 13, you're looking at a MurmurHash3 finalizer (also called `fmix32`). Recognizing well-known mixing functions saves hours of "what does this math DO."

**Approach:** For challenges with "validate input" checks, always ask: "Is there a forward direction I can compute directly?" Inversion is hard. Forward evaluation is almost always easy. If the check is a deterministic function of your input, just figure out what input makes each check pass in sequence.

**CRT in disguise:** Chinese Remainder Theorem appearing in a reversing challenge usually isn't about breaking crypto — it's a mixing/combining step that maps two residues to one combined value. Treat it as a black box and implement it from the extended Euclidean algorithm.

**VM tracing tip:** For small bytecode VMs, don't bother writing a general interpreter. Trace through the bytecode once by hand (or with a debugger), translate each slot into a Python one-liner, and you're done. The code is readable, testable, and runs at Python speed.
