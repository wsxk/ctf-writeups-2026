# Soul Writeup

**Challenge:** Soul  
**Category:** Reverse Engineering  
**Points:** 500  
**Author:** NotSaad💛

> i made a dispatcher but i lost my key please help me find it :(((

## TL;DR

The program is a small custom virtual machine. Its bytecode is encrypted, and
the VM uses a 16-byte key both for a complicated-looking check and to decrypt
the flag.

The recovered key is:

```text
4ba317f09c2e886135d47a0fc1563be9
```

Running the binary with it gives:

```text
Thryve{0n3_7h1n9_4b0u7_m3_15_1_h47e_vm_d15p47ch3r5}
```

## First look

There was one executable in the archive:

```bash
$ file soul_dispatch
soul_dispatch: ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped
```

`stripped` means the helpful function names have been removed. Running it
without an argument is not very informative:

```bash
$ ./soul_dispatch
nope :3
```

A strings search reveals only a few useful messages:

```bash
$ strings -a -tx soul_dispatch | grep -E 'nope|ACCESS|%02x'
   3004 nope :3
   300c %02x
   3011 ACCESS GRANTED
```

The `%02x` string is the first good clue. Disassembly shows that the program
expects exactly one argument containing **32 hexadecimal characters**. It
parses those characters two at a time, producing a 16-byte key.

In other words, the intended invocation looks like this:

```bash
./soul_dispatch 00112233445566778899aabbccddeeff
```

That example is not the correct key, of course.

## The giant function is mostly a VM

The main function starts around virtual address `0x10c0`. Early in the
function, it fills an array at `0x5040` with the same default handler, then
replaces a handful of entries with different function pointers.

That array is the “dispatcher” from the challenge description. A dispatcher is
basically a large lookup table saying:

> If the next instruction is opcode X, call handler Y.

Normal processors do this in hardware for instructions such as `ADD` and
`MOV`. This challenge implements a tiny pretend processor in software.

The VM has:

- 16 one-byte registers, `r0` through `r15`;
- 512 bytes of VM memory;
- a program counter telling it which bytecode instruction comes next;
- a halt flag;
- an instruction limit of 10,000,000 steps.

The parsed key is placed at VM memory offsets `0x000` through `0x00f`. A
256-byte substitution table is copied to memory starting at `0x020`, and a
51-byte encrypted flag is copied to memory starting at `0x120`.

## The bytecode is encrypted too

The bytecode is stored in `.rodata` at file offset `0x3060` and is `0x819`
bytes long. Looking at the raw bytes does not reveal the instruction stream,
because each byte is XORed with a position-dependent pseudo-random byte.

The native dispatch loop performs roughly this calculation for byte position
`i`:

```python
MASK = (1 << 64) - 1

def keystream(i):
    x = ((i * 0x9e3779b97f4a7c15) & MASK) ^ 0xdeadbeef13371337
    x = ((x ^ (x >> 16)) * 0x45d9f3b37d3aff67) & MASK
    x = ((x ^ (x >> 16)) * 0x45d9f3b37d3aff67) & MASK
    return (x ^ (x >> 16)) & 0xff

decoded_byte = encrypted_byte ^ keystream(i)
```

The constants make this look scary, but there is no secret involved. The byte
position completely determines the keystream byte, so the entire VM program
can be decoded offline.

I extracted it with:

```python
from pathlib import Path

binary = Path("soul_dispatch").read_bytes()
encrypted = binary[0x3060:0x3060 + 0x819]
program = bytes(b ^ keystream(i) for i, b in enumerate(encrypted))
```

## Identifying the instructions

Each function placed in the dispatcher is small enough to understand by
following how it changes the VM registers, memory, and program counter. That
gives the following instruction set:

| Opcode | Name | Meaning |
|---:|---|---|
| `0xff` | `HALT` | Stop the VM |
| `0x7e` | `JMP` | Jump to a bytecode address |
| `0x42` | `MOVI` | Put a constant byte into a register |
| `0xd8` | `XORI` | XOR a register with a constant |
| `0x17` | `MOV` | Copy one register to another |
| `0x93` | `ADD` | Add one register to another |
| `0xa5` | `SUB` | Subtract one register from another |
| `0x2c` | `XOR` | XOR two registers |
| `0x0a` | `CMPEQ` | Compare two registers for equality |
| `0x8c` | `JZ` | Jump if a register is zero |
| `0x55` | `JNZ` | Jump if a register is not zero |
| `0x3e` | `LOAD` | Read a byte from a fixed memory offset |
| `0x6b` | `STORE` | Write a byte to a fixed memory offset |
| `0xf1` | `LOADX` | Read from a base offset plus an index register |
| `0xe5` | `STOREX` | Write to a base offset plus an index register |

Any unrecognized opcode calls the default handler, which simply stops the VM.

Once decoded, the beginning of the bytecode becomes quite readable:

```text
0000: LOAD   r0,  [000]
0004: LOAD   r1,  [001]
0008: LOAD   r2,  [002]
...
003c: LOAD   r15, [00f]
0040: XORI   r0,  b1
0043: XORI   r1,  f2
...
0070: LOADX  r0, r0, [020]
0075: LOADX  r1, r1, [020]
...
```

The first 16 instructions load the candidate key into the 16 VM registers.

## What the key check does

The checker performs eight similar rounds. Each round roughly does this:

1. XOR every register with a different constant.
2. Use each resulting byte as an index into the 256-byte table at memory
   offset `0x020`.
3. Shuffle several registers.
4. Add the registers together in a chain.

After the eight rounds, more constants are XORed into the registers and all 16
values are accumulated into `r0`. The VM continues only if the final byte is
zero.

This looks like a serious key-verification algorithm, but it ultimately checks
only one byte. Many random 16-byte inputs can satisfy a one-byte condition.
Those inputs will reach `ACCESS GRANTED`, but almost all will decrypt the flag
to garbage. Therefore, solving only the check is not enough; we want the
specific key that produces meaningful plaintext.

## The useful weakness: repeating-key XOR

The final VM loop is much simpler than the checker:

```text
07d0: MOVI   r0, 0
07d3: MOVI   r1, 0
07d6: LOADX  r2, r1, [000]    ; key[r1]
07db: LOADX  r3, r0, [120]    ; encrypted_flag[r0]
07e0: XOR    r3, r2
07e3: STOREX r3, r0, [120]
07e8: MOVI   r4, 1
07eb: ADD    r0, r4
07ee: ADD    r1, r4
...
```

In plain English, it does:

```python
for i in range(51):
    flag[i] ^= key[i % 16]
```

This is repeating-key XOR. The key is 16 bytes long, so key byte 0 encrypts
flag positions 0, 16, 32, and 48. Key byte 1 encrypts positions 1, 17, 33,
and 49, and so on.

The encrypted 51-byte blob is stored at file offset `0x3020`:

```text
1f cb 65 89 ea 4b f3 51 5b e7 25 38 a9 67 55 d0
14 97 75 c0 e9 19 d7 0c 06 8b 4b 3a 9e 67 64 81
7f 94 72 af ea 43 d7 05 04 e1 0a 3b f6 35 53 da
39 96 6a
```

## Recovering the key from the flag format

We know a real flag begins with `Thryve{`. With XOR, if we know a ciphertext
byte and its plaintext byte, the key byte is simply:

```text
key = ciphertext XOR plaintext
```

Applying that to the first seven bytes gives:

| Position | Cipher | Plain | Key |
|---:|---:|:---:|---:|
| 0 | `1f` | `T` | `4b` |
| 1 | `cb` | `h` | `a3` |
| 2 | `65` | `r` | `17` |
| 3 | `89` | `y` | `f0` |
| 4 | `ea` | `v` | `9c` |
| 5 | `4b` | `e` | `2e` |
| 6 | `f3` | `{` | `88` |

The last ciphertext byte is `0x6a`. Since the last flag character should be
`}`, it gives key byte 2 again:

```text
0x6a XOR ord('}') = 0x17
```

That agrees with the known prefix and confirms both the length and repeating
alignment.

Using those known key bytes already reveals this much:

```text
Thryve{?????????_4b0u7_?????????47e_vm_?????????r5}
```

For each remaining key position, I tried byte values that made all three
corresponding plaintext characters valid flag characters. The selected values
produce these vertical groups:

| Key index | Key byte | Plaintext positions separated by 16 bytes |
|---:|---:|:---|
| 7  | `61` | `0md` |
| 8  | `35` | `n31` |
| 9  | `d4` | `3_5` |
| 10 | `7a` | `_1p` |
| 11 | `0f` | `754` |
| 12 | `c1` | `h_7` |
| 13 | `56` | `11c` |
| 14 | `3b` | `n_h` |
| 15 | `e9` | `9h3` |

The table is read vertically because one key byte affects characters 16 bytes
apart. Reading the plaintext normally, from left to right, produces:

```text
0n3_7h1n9
m3_15_1_h47e
d15p47ch3r5
```

That completes the very on-theme message:

```text
0n3_7h1n9_4b0u7_m3_15_1_h47e_vm_d15p47ch3r5
```

The complete key is therefore:

```text
4b a3 17 f0 9c 2e 88 61 35 d4 7a 0f c1 56 3b e9
```

or, in the format expected by the program:

```text
4ba317f09c2e886135d47a0fc1563be9
```

## Small final solver

This script extracts the encrypted flag and decrypts it with the recovered key:

```python
#!/usr/bin/env python3
from pathlib import Path

binary = Path("soul_dispatch").read_bytes()
ciphertext = binary[0x3020:0x3020 + 0x33]
key = bytes.fromhex("4ba317f09c2e886135d47a0fc1563be9")

flag = bytes(c ^ key[i % 16] for i, c in enumerate(ciphertext))
print(flag.decode())
```

Output:

```text
Thryve{0n3_7h1n9_4b0u7_m3_15_1_h47e_vm_d15p47ch3r5}
```

## Final verification

The most important step is testing the key against the original binary:

```bash
$ ./soul_dispatch 4ba317f09c2e886135d47a0fc1563be9
ACCESS GRANTED
Thryve{0n3_7h1n9_4b0u7_m3_15_1_h47e_vm_d15p47ch3r5}
```

## Flag

```text
Thryve{0n3_7h1n9_4b0u7_m3_15_1_h47e_vm_d15p47ch3r5}
```

