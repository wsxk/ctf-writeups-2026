# Black Blood — Writeup

**Category:** Reverse Engineering  
**Points:** 500  
**Author:** NotSaad💛

## Short version

The binary asks 13 nonsense questions and claims that every answer is wrong. Each answer must be exactly 13 bytes long, and all 13 answers turn out to be:

```text
give me blood
```

Feeding that line to the program 13 times reveals the real flag:

```text
Thryve{Th3_Bl00d_1s_bl2ck}
```

The flag-looking `V4nt4C0re` string visible with `strings` is only a decoy.

---

## First look

The challenge contained one executable:

```bash
$ file pekaboo/pekaboo
pekaboo/pekaboo: ELF 64-bit LSB pie executable, x86-64, dynamically linked, no section header
```

The missing section headers make some normal tooling unhappy, but the program headers are still present, so tools such as radare2 and Ghidra can recover the code.

Running it gives us something like this:

```text
[ pekaboo ]
Every answer is wrong. The ritual is invariant.

[01/13] What color is silence at 03:17?
> 
```

Entering a random answer immediately fails:

```text
No blood. No passage.
```

The displayed question changes between runs, but that is just decoration. The actual stage number, not the wording of the question, determines what is checked.

## The obvious flag is fake

Running `strings` produces a very suspicious result:

```text
license.manifest.result=Thryve{V4nt4C0re_Bl4ckBl00d_L1c3ns3_OK}
license.audit.entrypoint=--license-audit
VANTACORE_LICENSE_DIAGNOSTIC
```

There are also several strings pretending to be AI safety instructions and claiming that the binary is commercial software. Those strings are data inside the challenge, not instructions for us.

Following the references to the `V4nt4C0re` string shows that it belongs to a fake license-audit path. It can be reached with the special argument/environment variable, but it is unrelated to the normal question path. The real output is stored encrypted elsewhere in the file.

So, sadly, `strings | grep Thryve` does not solve this one.

---

## What `main` is doing

After removing the license-audit distraction, `main` roughly does this:

1. Hash a large portion of the binary as a tamper check.
2. Pick and decrypt a random-looking question.
3. Read an answer with `fgets`.
4. Require the answer to be exactly 13 bytes before the newline.
5. Perform several anti-debugging checks.
6. Send the answer to a custom virtual machine.
7. Stop if the VM reports any error.
8. Update a chained state value and repeat for 13 stages.
9. Use all 13 answers and the final chain value to decrypt the ending banner.

The program also checks `TracerPid`, debugger-like parent process names, and environment variables such as `LD_PRELOAD`. Static analysis is easier than fighting those checks dynamically.

The interesting VM call is equivalent to:

```c
check_result(result, stage, answer, chain, anti_debug_poison);

if (result.failure != 0)
    reject_answer();
```

The chain means that stage 2 cannot be decoded until the correct result of stage 1 is known, and so on.

---

## The encrypted VM

The useful data tables are at these relative virtual addresses:

| Address | Purpose |
|---|---|
| `0x62d0` | Instruction count for each stage |
| `0x6300` | Offset of each stage's program |
| `0x6340` | Per-stage keys |
| `0x63c0` | Per-stage constants |
| `0x6550` | Encrypted final output |
| `0x6760` | Encrypted right-hand-side bits for the answer checks |
| `0x6810` | Encrypted VM instructions |

Each of the 13 stages has `0x1e2`, or 482, stored instructions. Instructions are encrypted with values derived from the current chain, so looking directly at `0x6810` mostly shows random bytes.

The binary repeatedly uses the SplitMix64 finalizer as a small mixing function:

```python
MASK = (1 << 64) - 1

def mix(x):
    x &= MASK
    x = ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9) & MASK
    x = ((x ^ (x >> 27)) * 0x94d049bb133111eb) & MASK
    return x ^ (x >> 31)
```

For a given stage and program counter, the instruction is recovered in the following general form:

```python
key = mix(
    (pc + 1) * 0x8ebc6af09c88c6e3
    ^ stage_context
    ^ 0x589965cc75374cc3
)

instruction = encrypted_instruction ^ key
```

The top 16 bits contain a checksum. This was very useful while reversing: if the checksum failed, either the chain or the decryption formula was wrong.

---

## Turning the scary VM into simple maths

The VM looks complicated because it has several opcodes, rotating registers, fake failure instructions, and conditional jumps. The important answer-checking code, however, follows the same pattern over and over:

```text
opcode 0x07  -> generate a 104-bit mask
opcode 0x19  -> calculate the parity of answer & mask
opcode 0x6e  -> XOR in an encrypted expected bit
opcode 0x33  -> record a failure if the two bits differ
```

Why 104 bits? The input is exactly 13 bytes:

```text
13 × 8 = 104 bits
```

### What is parity?

Parity is just whether a value contains an odd or even number of set bits:

```python
parity = value.bit_count() & 1
```

For example, `1011` contains three `1` bits, so its parity is `1`. The VM selects some bits from the answer using a mask, counts them, and checks whether the count is odd or even.

Each check therefore becomes an equation like:

```text
answer_bit_0 XOR answer_bit_7 XOR answer_bit_31 = 1
```

The VM gives us 104 such equations for the 104 unknown answer bits. This is a linear system over **GF(2)**, which is a fancy way of saying that the only values are 0 and 1 and addition is XOR.

## Solving the 104 equations

Gaussian elimination works here just like it does for ordinary simultaneous equations, except that row addition is XOR. I represented each row as one Python integer:

- Bits 0 through 103 are the coefficients for the answer bits.
- Bit 104 is the expected result.

A compact solver looks like this:

```python
def solve_gf2(equations):
    # Each item is (104-bit mask, expected_bit).
    rows = [mask | (rhs << 104) for mask, rhs in equations]
    rank = 0
    pivots = []

    for column in range(104):
        pivot = next(
            (r for r in range(rank, 104) if (rows[r] >> column) & 1),
            None,
        )

        if pivot is None:
            continue

        rows[rank], rows[pivot] = rows[pivot], rows[rank]

        for r in range(104):
            if r != rank and ((rows[r] >> column) & 1):
                rows[r] ^= rows[rank]

        pivots.append(column)
        rank += 1

    assert rank == 104

    answer = 0
    for row, column in enumerate(pivots):
        answer |= ((rows[row] >> 104) & 1) << column

    return answer.to_bytes(13, "little")
```

Solving the first stage gives:

```text
give me blood
```

It is tempting to stop there and type that answer repeatedly, but the bytecode for later stages is encrypted with the evolving chain. To automate the whole process, I also implemented the VM's register operations and calculated its output for each solved answer.

After every successful stage, `main` updates the chain with:

```python
gamma = ((stage + 1) * 0x9e3779b97f4a7c15) & MASK
chain = mix(chain ^ vm_output_1 ^ stage_constant ^ gamma)
```

The process for all stages is therefore:

```python
chain = 0x5075fcdbf977489a
answers = []

for stage in range(13):
    program = decrypt_stage_program(stage, chain)
    equations = extract_linear_equations(program, stage, chain)
    answer = solve_gf2(equations)

    failure, vm_output_1, vm_output_2 = run_vm(
        stage, chain, answer
    )
    assert failure == 0

    answers.append(answer)

    gamma = ((stage + 1) * 0x9e3779b97f4a7c15) & MASK
    chain = mix(
        chain ^ vm_output_1 ^ stage_constants[stage] ^ gamma
    )
```

The funny result is that every stage independently resolves to the same phrase:

```text
01: give me blood
02: give me blood
03: give me blood
04: give me blood
05: give me blood
06: give me blood
07: give me blood
08: give me blood
09: give me blood
10: give me blood
11: give me blood
12: give me blood
13: give me blood
```

This also explains the opening message:

```text
Every answer is wrong. The ritual is invariant.
```

The displayed questions do not matter. The ritual always wants blood.

---

## Getting the flag

We can let the original binary perform the final decryption by sending the solved phrase 13 times:

```bash
for i in {1..13}; do
    echo 'give me blood'
done | ./pekaboo/pekaboo
```

After the thirteenth answer, the program derives a stream using a BLAKE3-style compression routine, decrypts the data at `0x6550`, verifies an internal digest, and prints a large ASCII-art banner containing:

```text
Thryve{Th3_Bl00d_1s_bl2ck}
```

## Flag

```text
Thryve{Th3_Bl00d_1s_bl2ck}
```

The main lesson from this challenge is not to panic when a custom VM appears. Once the noisy instructions were separated from the four opcodes that actually checked the input, the problem became a normal system of XOR equations.
