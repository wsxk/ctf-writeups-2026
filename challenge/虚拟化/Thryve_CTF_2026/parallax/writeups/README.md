# Parallax Writeup

**Category:** Reverse Engineering  
**Points:** 500  
**Author:** NotSaad💛

## TL;DR

The program is a small custom virtual machine. It decrypts about 11 KB of hidden
bytecode, changes the meaning of its instructions after every operation, and then
uses that bytecode to check a 45-character input.

After recreating the VM and solving its repeated three-character checks, the flag
is:

```text
Thryve{Man_Am_1_n0t_th2_b2st_auth0r?_NotSaad}
```

---

## 1. First look at the file

The release contained one file:

```bash
$ file parallax
parallax: ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped
```

It is a normal Linux x86-64 program, although the challenge description says the
original machine "never used the same instruction set twice." That line turns out
to be a hint about the changing instruction table inside the program, not about
the ELF's real CPU architecture.

Running it gives us one prompt:

```bash
$ ./parallax
phase> hello
desynchronized
```

The input must be exactly `0x2d`, or 45, characters long. Anything else is rejected
immediately.

---

## 2. The strings are bait

Running `strings` looks promising at first:

```text
Thryve{static_strings_are_a_trap}
Thryve{patch_the_last_jump}
Thryve{nice_try_wrong_vm}
```

Unfortunately, all three are fake flags. The first one even politely tells us
that static strings are a trap.

There are also a few strings that are actually useful:

```text
/proc/self/status
TracerPid:
desynchronized
synchronization achieved
phase>
```

The program reads `/proc/self/status` and checks `TracerPid`. A nonzero tracer PID
means a debugger is attached. Instead of simply quitting, the program uses the
result to disturb its VM state, so debugging it naively makes it decode the wrong
instructions. For the solve, it was easier to emulate the VM rather than fight
the anti-debug check.

---

## 3. Decrypting the hidden program

The main checker allocates `0x2c7c` bytes. It then decrypts the same number of
bytes from `.rodata`, starting at virtual/file offset `0x20c0`.

The cipher is just XOR with bytes produced by a xorshift generator. The initial
64-bit state is:

```text
0xdd44d5bae067208d
```

Every eight output bytes, the state is updated like this:

```c
state ^= state << 13;
state ^= state >> 7;
state ^= state << 17;
```

The eight little-endian bytes of that state are XORed with the next eight bytes
of encrypted data.

Here is the equivalent Python:

```python
from pathlib import Path

elf = Path("parallax").read_bytes()
cipher = elf[0x20c0:0x20c0 + 0x2c7c]

state = 0xdd44d5bae067208d
mask64 = (1 << 64) - 1
code = bytearray()

for i, byte in enumerate(cipher):
    if i % 8 == 0:
        state ^= state << 13
        state &= mask64
        state ^= state >> 7
        state ^= state << 17
        state &= mask64

    key_byte = (state >> (8 * (i % 8))) & 0xff
    code.append(byte ^ key_byte)
```

The native program also performs an FNV-style integrity check over the decrypted
data. A small reversing gotcha is that it compares the final XOR value *before*
the last multiplication. That value is `0x60b315e5`, confirming that the
decryption is correct.

The beginning of the decrypted blob now looks structured rather than random:

```text
0d 00 03 14 80 ca 0e 03 b3 03 01 f0 00 07 df 9b ...
```

This is bytecode for the program's custom VM.

---

## 4. The custom VM

The VM has eight 32-bit registers, `r0` through `r7`, a bytecode program counter,
an error accumulator, and a value called the **phase**.

Its useful operations are:

| Decoded opcode | Meaning |
|---:|---|
| 0 | Halt |
| 1 | Put a 32-bit constant in a register |
| 2 | Load one input character into a register |
| 3 | XOR two registers |
| 4 | Add two registers |
| 5 | Multiply a register by a constant |
| 6 | Rotate a register left |
| 7 | Subtract two registers |
| 8 | Apply a byte-by-byte substitution table |
| 9 | Apply a 32-bit mixing function with a constant |
| 10 | Assert that a register equals a constant |
| 11 | XOR a register with a constant |
| 12 | Add a constant to a register |
| 13 | Swap two registers |
| 14 | Do nothing |
| 15 | Invalid instruction/error |

### Why is it called Parallax?

A raw byte from 0 to 15 does **not** have one permanent meaning. It is first
translated through one of four 16-byte instruction tables:

```python
decoded_opcode = opcode_table[phase * 16 + raw_byte]
```

After every instruction, the phase changes:

```python
phase = (
    phase
    + ((r0 ^ r3 ^ program_counter) & 3)
    + (decoded_opcode & 1)
) & 3
```

So the same raw byte can mean `LOAD` in one phase, `XOR` in another, or even an
invalid operation in a third. It is like reading the same symbol through four
different decoder rings, and changing rings after every symbol.

This is what the challenge description means by never using the same instruction
set twice. It also explains why patching one final jump is not enough: if any
earlier value is wrong, `r0`, `r3`, or the program counter eventually changes the
phase and the rest of the byte stream turns into nonsense.

---

## 5. The two nonlinear-looking operations

The substitution opcode applies a 256-byte S-box separately to each byte of a
32-bit register:

```python
def subst(x, sbox):
    return sum(
        sbox[(x >> shift) & 0xff] << shift
        for shift in range(0, 32, 8)
    )
```

The mixing opcode first XORs in its immediate value and then uses this common
32-bit avalanche function:

```python
def mix(x):
    x ^= x >> 16
    x = x * 0x7feb352d & 0xffffffff
    x ^= x >> 15
    x = x * 0x846ca68b & 0xffffffff
    x ^= x >> 16
    return x
```

It looks one-way, but it is reversible. Both multiplication constants are odd,
so they have modular inverses modulo `2**32`. Right-shift XORs can also be undone.

```python
def unxorshr(y, amount):
    x = y
    shift = amount
    while shift < 32:
        x ^= y >> shift
        shift += amount
    return x & 0xffffffff

def unmix(x):
    x = unxorshr(x, 16)
    x = x * pow(0x846ca68b, -1, 1 << 32) & 0xffffffff
    x = unxorshr(x, 15)
    x = x * pow(0x7feb352d, -1, 1 << 32) & 0xffffffff
    x = unxorshr(x, 16)
    return x
```

I verified this with random words:

```python
assert unmix(mix(x)) == x
```

---

## 6. Recognizing the repeated checks

Once the correct phases are followed, the bytecode contains the same basic
13-instruction check over and over:

```text
LOAD    r1, input[a]
LOAD    r2, input[b]
MULI    r1, constant_1
XORI    r2, constant_2
SBOX    r2
ADD     r1, r2
ROL     r1, rotation
LOAD    r2, input[c]
MULI    r2, constant_3
XOR     r1, r2
MIXI    r1, constant_4
ADDI    r1, constant_5
ASSERT  r1, expected
```

Each assertion ties together three flag characters. For example, the first check
uses input positions 19, 10, and 36. Solving it gives:

```text
input[19] = '_'
input[10] = '_'
input[36] = '_'
```

The next check uses positions 4, 18, and 7. Position 4 is already known from the
`Thryve{` prefix, and the equation produces:

```text
input[4]  = 'v'
input[18] = 't'
input[7]  = 'M'
```

The checks deliberately use characters out of order, so simply reading the
constants does not reveal the flag.

---

## 7. Solving a three-character check efficiently

Brute-forcing all three printable characters would require about
`95 ** 3 = 857,375` tests per check. That is not enormous, but reversing `mix`
lets us reduce it to only `95 ** 2 = 9,025` combinations.

For a check of the form above, undo the final addition and `mix` first. Then try
the first two characters and look up whether the required third-character
product exists:

```python
def rol32(x, n):
    n &= 31
    return ((x << n) | (x >> ((32 - n) & 31))) & 0xffffffff

def solve_triplet(m1, xor2, rotation, m2, mix_constant,
                  add_constant, expected, sbox, allowed):
    # Work backwards through ADDI and MIXI.
    before_mix = (
        unmix((expected - add_constant) & 0xffffffff)
        ^ mix_constant
    )

    # Map every possible third-character product back to its character.
    third_products = {
        (char * m2) & 0xffffffff: char
        for char in allowed[2]
    }

    answers = []
    for first in allowed[0]:
        first_part = first * m1 & 0xffffffff

        for second in allowed[1]:
            second_part = subst(second ^ xor2, sbox)
            summed = (first_part + second_part) & 0xffffffff
            left = rol32(summed, rotation)

            third = third_products.get(left ^ before_mix)
            if third is not None:
                answers.append((first, second, third))

    return answers
```

Known characters, such as the `Thryve{` prefix and final `}`, are passed as
one-item `allowed` lists. Unknown characters use the printable ASCII range.

I automated the process as follows:

1. Start with the known prefix, suffix, and placeholder bytes elsewhere.
2. Emulate the VM until its first failed assertion.
3. Read that check's three input indexes and constants from the decoded
   instructions.
4. Solve the three-character equation.
5. Insert the newly discovered characters.
6. Restart emulation from the beginning, now following the correct phases for
   longer.
7. Repeat until every assertion passes.

Restarting is important. A wrong placeholder can eventually alter the current
phase, at which point the following raw bytes decode as the wrong instructions.

Some snapshots from the solver show the flag filling in out of order:

```text
Thryve{???_????????_????????????????_???????}
Thryve{M??_???????t_????????????????_???????}
Thryve{Man_A?_1_n?t_th??b???_???????_??t????}
Thryve{Man_Am_1_n0t_th2_b?st_auth0r?_NotSaad}
Thryve{Man_Am_1_n0t_th2_b2st_auth0r?_NotSaad}
```

With the finished input, the emulator reaches the end of all `0x2c7c` bytecode
bytes with no VM error and all 181 assertions passing.

---

## 8. Final verification

The best confirmation is to give the recovered flag to the original binary:

```bash
$ printf '%s\n' 'Thryve{Man_Am_1_n0t_th2_b2st_auth0r?_NotSaad}' | ./parallax
phase> synchronization achieved

$ echo $?
0
```

Therefore, the flag is:

```text
Thryve{Man_Am_1_n0t_th2_b2st_auth0r?_NotSaad}
```

## Takeaways

- Do not trust obvious flag-looking strings in a reverse engineering challenge.
- Anti-debugging does not always exit; sometimes it quietly corrupts later state.
- A custom VM becomes much less scary once its state, instruction formats, and
  dispatch table are written down.
- Operations that look like hashes may actually be permutations and therefore
  reversible.
- When a VM changes instruction mappings based on program state, solving one
  check at a time and replaying from the start is often simpler than trying to
  symbolically execute everything at once.
