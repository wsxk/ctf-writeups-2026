# Hell Writeup

## Challenge information

**Category:** Reverse Engineering  
**Points:** 485  
**Flag format:** `Thryve{...}`

> A paranoid developer decided that standard string comparisons are too mainstream. Instead, he locked the flag behind a tangled web of Mixed Boolean-Arithmetic (MBA) equations.

## Short version

The binary checks a 12-character secret inside `Thryve{...}`. Each check mixes three neighboring characters using XOR, addition, and multiplication. I copied those checks into Z3, restricted the characters to printable ASCII, and got:

```text
m4th_m4dn3ss
```

Therefore, the flag is:

```text
Thryve{m4th_m4dn3ss}
```

## First look at the binary

The challenge gives us one small ELF file named `rev_hell`:

```bash
$ file rev_hell
rev_hell: ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped
```

`stripped` means most helpful function names have been removed. That makes the disassembly a little less friendly, but this binary is small enough that it is not a major problem.

Running `strings` immediately reveals a few useful messages:

```bash
$ strings -a rev_hell
Usage: %s [flag]
Thryve{
Invalid format!
Access Granted!
Access Denied!
```

The program expects the flag as its first command-line argument, rather than reading it from standard input. My copy did not initially have its executable bit set, so I fixed that with:

```bash
chmod +x rev_hell
```

Trying a fake flag confirms the expected usage:

```bash
$ ./rev_hell 'Thryve{aaaaaaaaaaaa}'
Access Denied!
```

## Finding the format checks

Looking at `main` in a decompiler or disassembler shows three basic format requirements:

1. The complete input must be exactly 20 characters long.
2. Its first seven characters must be `Thryve{`.
3. Its last character must be `}`.

Since the prefix is 7 characters and the closing brace is 1 character, that leaves a 12-character secret:

```text
Thryve{????????????}
       ^----------^
          12 bytes
```

The program copies those 12 bytes into a temporary buffer and passes that buffer to two functions.

## The scary-looking distraction

The first function, around address `0x1179`, contains several loops, shifts, XORs, divisions compiled into magic-number multiplications, and other unpleasant-looking arithmetic. It certainly looks like the promised MBA nightmare.

However, there is an important reversing lesson here: **always follow the result of a calculation**.

This function builds an accumulator in a local stack variable, but it never returns that accumulator and never writes it anywhere useful. `main` also ignores anything it might have calculated. In other words, all of the scary work has no effect on whether the flag is accepted.

It is basically a decoy.

## The real checker

The second function, around address `0x122d`, is the one that matters. It loops over all 12 secret characters. For each position `i`, it takes:

- the character at position `i`,
- the next character, at `(i + 1) % 12`, and
- the character after that, at `(i + 2) % 12`.

The `% 12` makes the positions wrap around. For example, after position 11 comes position 0 again, as if the characters were arranged in a circle.

The decompiled logic can be simplified to this:

```c
unsigned char target[12] = {
    0x67, 0xf8, 0x71, 0xec,
    0x32, 0x37, 0x3a, 0xb7,
    0x70, 0x19, 0x47, 0xf6
};

for (int i = 0; i < 12; i++) {
    unsigned char result =
        3 * ((secret[i] ^ secret[(i + 1) % 12])
             + secret[(i + 2) % 12]);

    if (result != target[i])
        return 0;
}

return 1;
```

Because `result` is only one byte, the arithmetic wraps around at 256. For example, decimal 300 becomes 44 because `300 mod 256 = 44`. Written mathematically, each condition is:

```text
3 * ((x[i] XOR x[(i+1) mod 12]) + x[(i+2) mod 12]) mod 256
    = target[i]
```

This gives us 12 equations for the 12 unknown characters.

## Solving the equations with Z3

Solving this by hand would be possible, but the XOR mixed with modular addition would make it annoying. Z3 is a constraint solver: we describe the rules, and it searches for values that satisfy every rule at once.

I represented each unknown character as an 8-bit bit-vector. That is especially convenient here because an 8-bit Z3 value naturally wraps around at 256, exactly like the `unsigned char` calculation in the binary.

Here is the complete solver:

```python
#!/usr/bin/env python3
from z3 import BitVec, Or, Solver, UGE, ULE, sat

target = bytes.fromhex(
    "67 f8 71 ec 32 37 3a b7 70 19 47 f6"
)

# Twelve unknown one-byte characters.
x = [BitVec(f"x{i}", 8) for i in range(12)]

s = Solver()

# Flags normally contain readable characters. This also removes junk solutions.
for c in x:
    s.add(UGE(c, 0x20), ULE(c, 0x7e))

# Reproduce the check performed by the binary.
for i, expected in enumerate(target):
    s.add(
        ((x[i] ^ x[(i + 1) % 12]) + x[(i + 2) % 12]) * 3
        == expected
    )

if s.check() == sat:
    model = s.model()
    secret = bytes(model.eval(c).as_long() for c in x)
    print(f"Thryve{{{secret.decode()}}}")
else:
    print("No solution found")
```

Running it gives:

```bash
$ python3 solve.py
Thryve{m4th_m4dn3ss}
```

With printable ASCII constraints, this solution is unique.

## Checking one equation by hand

As a quick sanity check, take the first three secret characters:

```text
x[0] = 'm' = 0x6d
x[1] = '4' = 0x34
x[2] = 't' = 0x74
```

The first equation becomes:

```text
3 * ((0x6d XOR 0x34) + 0x74) mod 256
= 3 * (0x59 + 0x74) mod 256
= 3 * 0xcd mod 256
= 0x267 mod 256
= 0x67
```

`0x67` is exactly the first target byte, so the first check passes. Z3 found characters that make all 12 checks pass in the same way.

## Final verification

The best confirmation is to give the recovered flag directly to the original program:

```bash
$ ./rev_hell 'Thryve{m4th_m4dn3ss}'
Access Granted!
```

## Flag

```text
Thryve{m4th_m4dn3ss}
```

## Takeaway

The main trick was not defeating complicated MBA expressions. It was noticing that the nastiest-looking function was irrelevant. Once that distraction was ignored, the actual checker reduced to a short set of byte equations that Z3 could solve almost instantly.
