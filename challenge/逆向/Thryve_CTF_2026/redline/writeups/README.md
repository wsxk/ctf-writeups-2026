# RedLine Writeup

**Challenge:** RedLine  
**Category:** Reverse Engineering  
**Points:** 500  
**Author:** `.effie`

> The old access relay only reports two states: red and black.  
> Can you recover what it is hiding?

## Short version

The program turns every bit of a 36-character credential into a pair of opposite
values, runs those values through a few thousand tiny logic gates, and compares
320 resulting bits with a hard-coded answer.

Instead of trying to understand one enormous formula by hand, I extracted the
gate list, recreated the circuit with Z3, and asked Z3 which credential makes all
320 comparisons true.

The result was:

```text
ThryveCTF{red_black_relays_dont_lie}
```

## First look

There was only one provided file:

```bash
$ file redline
redline: ELF 64-bit LSB executable, x86-64, statically linked, stripped
```

`stripped` means the useful function names have been removed. `statically
linked` explains why the binary is fairly large: it contains its own copy of
much of the C library.

Running it shows the basic interface:

```text
THRYVE ACCESS RELAY
credential: test
relay trace: BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB...
consensus: REJECTED
```

The `R` and `B` characters are the two states mentioned in the description.

## Strings, including some bait

A strings search finds the normal interface text:

```bash
strings -a -tx redline | grep -Ei 'THRYVE|credential|relay|consensus'
```

It also finds these very tempting values:

```text
ThryveCTF{local_colors_are_not_enough}
ThryveCTF{red_black_decoy_trace}
```

Neither is accepted. They are deliberate decoys, which is a good reminder that
finding flag-shaped text inside a reversing challenge does not necessarily mean
the challenge is solved.

## Finding the actual checker

The string `THRYVE ACCESS RELAY` is stored at virtual address `0x479019`.
Looking for code that references that address leads to the program's main logic
around `0x401780`.

The relevant behavior, translated from assembly into plain English, is:

1. Read at most 128 bytes.
2. Remove the newline.
3. Require exactly **36 characters**.
4. Require every character to be printable.
5. Convert the input to individual bits.
6. Run a hard-coded Boolean circuit.
7. Print part of the circuit state as red/black pairs.
8. Compare 320 circuit outputs with a hard-coded target.

If every comparison matches, it prints `ACCEPTED`.

## What is dual-rail encoding?

The interesting trick is how each input bit is stored. The program does not
store just one value. It stores the value and its opposite next to each other:

| Original bit | Stored pair |
|---|---|
| `0` | `(0, 1)` |
| `1` | `(1, 0)` |

This is commonly called **dual-rail encoding**.

For a layman-friendly picture, imagine that every logical bit has two lamps.
Exactly one lamp should be on. If the first lamp is on, the bit is 1; if the
second lamp is on, the bit is 0. The relay later prints these two lamps as `R`
or `B`, which is why the trace is twice as long as the number of displayed
logical bits.

There are 36 input characters and 8 bits per character:

```text
36 * 8 = 288 input bits
```

Those become logical wires numbered `0` through `287`.

The bits of each character are inserted least-significant bit first. In other
words, bit 0 of the first character becomes wire 0, bit 1 becomes wire 1, and
so on.

## The circuit table

The checker does not contain one long, obvious series of calls. Instead, it has
a table of gate descriptions in `.data.rel.ro` starting at virtual address
`0x4a14a0` (file offset `0xa14a0`).

Each record is 16 bytes and has roughly this shape:

```c
struct gate {
    uint64_t function;
    uint16_t a;
    uint16_t b;
    uint16_t c;
    uint16_t padding;
};
```

The table is `0xb9c0` bytes long, so it contains:

```text
0xb9c0 / 16 = 2972 gates
```

Only five function addresses appear in the records. Disassembling those small
functions reveals their jobs:

| Address | Operation | Meaning |
|---|---|---|
| `0x401bb0` | NOT | `b = !a` |
| `0x401bd0` | XOR | `c = a XOR b` |
| `0x401c00` | NAND | `c = !(a AND b)` |
| `0x401c30` | fan-out | copy `a` into `b` and `c` |
| `0x401c60` | paired flip | XOR two wires with the same pseudo-random bit |

Their counts are:

```text
NOT          1184
XOR          1451
NAND          161
fan-out       165
paired flip    11
-----------------
total        2972
```

The paired-flip operation looks alarming because it uses a pseudo-random bit.
However, it flips two related wires by the same amount. The rest of the circuit
is built so that these masks cancel rather than changing the final accepted
credential. For symbolic execution, each flip can simply be represented by a
fresh Boolean variable.

## What must match?

After evaluating all 2,972 gates, the program checks 320 selected wires.

The selected wire numbers are stored at file offset `0x7ec00` as 320 little-
endian 16-bit integers. The expected values are a 40-byte bit field stored at
file offset `0x7ef20`:

```text
320 bits / 8 = 40 bytes
```

The target bytes are:

```text
04 33 a2 45 6e a6 b8 a5 ef 88 d3 35 3f e7 d0 c8
2f b2 59 25 96 7d f6 04 02 90 bc f2 64 01 62 f9
dd ac 5c 93 43 94 2f e0
```

Each bit is read least-significant bit first, just like the credential bits.

## Rebuilding it with Z3

Z3 is an SMT solver. In simple terms, I describe the unknown bits and all the
rules they must obey, then Z3 finds values that satisfy every rule at once.

Here is the solver used for the challenge:

```python
#!/usr/bin/env python3
import struct
import z3

data = open("redline", "rb").read()

# One Boolean variable for each of the 288 input bits.
inputs = [z3.Bool(f"x{i}") for i in range(288)]
wires = {i: inputs[i] for i in range(288)}
random_masks = []

GATE_TABLE_OFFSET = 0xA14A0
GATE_TABLE_SIZE = 0xB9C0

for i in range(GATE_TABLE_SIZE // 16):
    function, a, b, c = struct.unpack_from(
        "<QHHH", data, GATE_TABLE_OFFSET + i * 16
    )

    if function == 0x401BB0:          # NOT a -> b
        wires[b] = z3.Not(wires[a])

    elif function == 0x401BD0:        # XOR a,b -> c
        wires[c] = z3.Xor(wires[a], wires[b])

    elif function == 0x401C00:        # NAND a,b -> c
        wires[c] = z3.Not(z3.And(wires[a], wires[b]))

    elif function == 0x401C30:        # fan-out a -> b,c
        wires[b] = wires[a]
        wires[c] = wires[a]

    elif function == 0x401C60:        # flip a and b together
        mask = z3.Bool(f"mask{len(random_masks)}")
        random_masks.append(mask)
        wires[a] = z3.Xor(wires[a], mask)
        wires[b] = z3.Xor(wires[b], mask)

    else:
        raise ValueError(f"unknown gate function: {function:#x}")

solver = z3.Solver()

# Add the 320 hard-coded output comparisons.
checked_wires = struct.unpack_from("<320H", data, 0x7EC00)
target = data[0x7EF20:0x7EF20 + 40]

for i, wire_number in enumerate(checked_wires):
    expected = (target[i // 8] >> (i % 8)) & 1
    solver.add(wires[wire_number] == bool(expected))

# The original program requires each of the 36 bytes to be printable.
for character in range(36):
    value = z3.Sum([
        z3.If(inputs[character * 8 + bit], 1 << bit, 0)
        for bit in range(8)
    ])
    solver.add(value >= 0x21, value <= 0x7E)

# We know the required flag format. These constraints are not strictly part of
# the circuit, but they make the intended credential explicit.
prefix = b"ThryveCTF{"
for character, value in enumerate(prefix):
    for bit in range(8):
        solver.add(
            inputs[character * 8 + bit] == bool((value >> bit) & 1)
        )

for bit in range(8):
    solver.add(inputs[35 * 8 + bit] == bool((ord("}") >> bit) & 1))

assert solver.check() == z3.sat
model = solver.model()

answer = bytearray()
for character in range(36):
    value = 0
    for bit in range(8):
        if z3.is_true(model.eval(inputs[character * 8 + bit])):
            value |= 1 << bit
    answer.append(value)

print(answer.decode())
```

Running it gives:

```bash
$ python3 solve.py
ThryveCTF{red_black_relays_dont_lie}
```

I also asked Z3 whether a second printable input with the same known wrapper
could satisfy the circuit. It returned `unsat`, so the recovered input is
unique under those conditions.

## Verification

Finally, feed the recovered credential back to the original program:

```bash
$ printf '%s\n' 'ThryveCTF{red_black_relays_dont_lie}' | ./redline
THRYVE ACCESS RELAY
credential: relay trace: BRBRRBBRBRBRBRBRRBRBBRBRRBRBBRBRBRRBBRBRBRRBBRRBRBBRRBBRBRBRRBBRBRRBRBRBBRRBRBBRBRRBRBBRBRRBBRRBBRBRBRRBRBRBBRRBRBBRRBBRBRRBBRRB
consensus: ACCEPTED
```

## Flag

```text
ThryveCTF{red_black_relays_dont_lie}
```

## Takeaways

- Flag-looking strings can be decoys.
- A huge verifier can sometimes be much simpler when viewed as data rather than
  assembly.
- Dual-rail encoding makes the trace look strange, but it still represents
  ordinary Boolean values.
- Once a checker is reduced to logic gates and equality constraints, Z3 is an
  excellent substitute for hours of manual algebra.
