# Chimera Mirrors — Writeup

**Category:** Reverse Engineering  
**Points:** 500  
**Author:** NotSaad💛  
**Flag format:** `Thryve{...}`

## TL;DR

The program is basically a tiny computer running another tiny computer.

It decrypts an **outer virtual machine (VM)**, and that VM decrypts and runs a collection of **inner VM programs**. The inner programs validate the flag. The first 48 inner programs each check exactly one character, so instead of reversing every mathematical operation by hand, I emulated the VM and tried all 256 possible byte values at every position.

That recovered:

```text
Thryve{d0ubl3_VM_1n_4_m1rr0r_0pc0d35_n3v3r_5t4y}
```

The remaining inner programs act as extra consistency checks, and the recovered flag passes all of them.

---

## 1. First look

There is only one file:

```bash
$ file chimera_mirror
chimera_mirror: ELF 64-bit LSB pie executable, x86-64, dynamically linked, stripped
```

It is stripped, so helpful function names are gone. Running it with a random value gives:

```bash
$ ./chimera_mirror
test
phase> desynchronized
```

The useful imported functions are fairly limited:

```text
fgets
snprintf
strlen
ptrace
strcspn
puts
```

Most of these are ordinary input/output functions. `ptrace` stands out because it is commonly used as an anti-debugging trick.

The program accepts the flag either through standard input or as its first command-line argument. It then passes the input and its length to the large function at `0x1280`.

---

## 2. The anti-debugging trick

The checker contains this call:

```c
ptrace(PTRACE_TRACEME, 0, 0, 0);
```

In normal execution, that succeeds. If the process is already being traced by GDB, `strace`, or a similar tool, it returns `-1`.

The binary turns that result into a value:

```c
debug_value = 0;
if (ptrace_result == -1)
    debug_value = 0x5a;
```

That value is later mixed into VM operations. In other words, simply tracing the binary changes its calculations. For the solver, I modeled normal execution, where `debug_value` is zero.

This also explains why `strace ./chimera_mirror` is not a reliable way to observe a successful run.

---

## 3. Finding the outer VM

The checker first decrypts `0x720` bytes from `.rodata`, starting at address `0x20c0`.

The decryption uses a small 32-bit scrambling function. It is the well-known `xorshift32` pattern:

```python
MASK = 0xffffffff

def u32(x):
    return x & MASK

def xs(x):
    x = u32(x)
    x = u32(x ^ (x << 13))
    x = u32(x ^ (x >> 17))
    x = u32(x ^ (x << 5))
    return x
```

The whole outer decryption can be reproduced as:

```python
def decrypt_outer(binary):
    encrypted = binary[0x20c0:0x20c0 + 0x720]
    output = bytearray(len(encrypted))

    state = 0x7b3a7bd4
    key = 0x61

    for i, byte in enumerate(encrypted):
        state = xs(state + 3 * i + 0xa5a5a5a5)
        stream_byte = (state >> ((i & 3) * 8)) & 0xff
        output[i] = byte ^ key ^ stream_byte
        key = (key + 0x1d) & 0xff

    return bytes(output)
```

The result is 228 instructions because every instruction is eight bytes long:

```text
+0  opcode
+1  destination register
+2  source register
+3  rotation/extra argument
+4  32-bit immediate value
```

The register numbers are masked with `& 7`, so the VM has eight 32-bit registers.

### Important outer opcodes

After following the native dispatch code, the main instructions are:

| Opcode | Meaning |
|---:|---|
| `0xbf` | Put an immediate value in a register |
| `0xef` | Test whether the input length equals an immediate value |
| `0x91` | Boolean AND of two registers |
| `0xcd` | Decrypt and execute an inner checker |
| `0x95` | XOR/add/rotate register operation |
| `0xb7` | Add and xorshift register operation |
| `0xdc` | Anti-debug/input guard operation |
| `0xa3` | Return the low bit of a register |

The start of the decrypted program is especially helpful:

```text
000: MOV    r0, 0x00000001
001: LEN    r1, 0x00000030
002: AND    r0, r1
...
005: CHECK  r1, 0x0000003a
006: AND    r0, r1
007: CHECK  r1, 0x00000019
008: AND    r0, r1
...
227: RET    r0
```

`0x30` is 48 in decimal, so the correct input must be exactly **48 bytes** long.

The check numbers are deliberately shuffled. Every result is ANDed into `r0`, meaning one failed check makes the final answer false. The outer VM eventually invokes every inner checker numbered `0` through `87` exactly once.

A lot of the rotate, guard, and mixing instructions are noise. Every `CHECK` instruction takes outer register `r0` as its source, and on the valid path that register remains `1`.

---

## 4. The VM inside the VM

The `CHECK` opcode does not directly check a character. It looks up another encrypted bytecode program.

The relevant tables are:

| Address | Contents |
|---:|---|
| `0x27e0` | Per-check 32-bit decryption seed |
| `0x29c0` | Per-check program length |
| `0x2ac0` | Per-check offset into the blob |
| `0x2bc0` | Encrypted inner-program blob |

There is metadata for 116 programs, although the outer VM only executes checkers `0` through `87`. The rest are decoys.

Each selected program is decrypted with another per-check xorshift stream. In Python:

```python
from struct import unpack_from

def rol(x, n):
    n &= 31
    x &= 0xffffffff
    return ((x << n) | (x >> ((-n) & 31))) & 0xffffffff

def inner_meta(binary, check_id):
    length = unpack_from('<H', binary, 0x29c0 + 2 * check_id)[0]
    offset = unpack_from('<H', binary, 0x2ac0 + 2 * check_id)[0]
    seed = unpack_from('<I', binary, 0x27e0 + 4 * check_id)[0]
    return offset, length, seed

def decrypt_inner(binary, check_id):
    offset, length, seed = inner_meta(binary, check_id)
    encrypted = binary[0x2bc0 + offset:0x2bc0 + offset + length]
    output = bytearray(length)

    state = (
        ((check_id + 1) * 0x045d9f3b)
        ^ ((check_id + 1) * 0x9e3779b9)
        ^ seed
        ^ rol(0x7b805a1f, (check_id * 7) % 31)
    ) & 0xffffffff

    key = (-0x7d * check_id) & 0xffffffff

    for i, byte in enumerate(encrypted):
        state = xs(state + check_id * 0x11 + 0x7f4a7c15 + i)
        stream_byte = (state >> ((i & 3) * 8)) & 0xff
        output[i] = byte ^ (key & 0xff) ^ stream_byte
        key = (key + 0x11) & 0xffffffff

    return bytes(output)
```

The inner VM also uses eight 32-bit registers and eight-byte instructions.

### Inner opcodes

| Opcode | Meaning |
|---:|---|
| `0x0a` | Move immediate into register |
| `0x0f` | Add immediate |
| `0x21` | Return success |
| `0x26` | XOR three registers and an immediate |
| `0x30` | Load one input byte |
| `0x59` | Add and rotate left |
| `0x71` | Rotate left |
| `0x76` | Add values and apply xorshift32 |
| `0x7d` | Compare register with immediate; fail if unequal |
| `0x93` | Subtract immediate |
| `0xa7` | Rotate right |
| `0xab` | XOR immediate |
| `0xd2` | Multiply by an odd immediate |

---

## 5. The important pattern

After decrypting the inner programs, check `0` looks like this:

```text
00: MOV    r5, 0x2c510785
01: IN     r0, input[0]
02: XOR    r0, 0x80bdcd5f
03: ADD    r0, 0xe011960b
04: MUL    r0, 0x58fce6c1
05: ROL    r0, 4
06: MIX    r4, ...
07: XOR    r0, 0xdc6869dd
08: MUL    r0, 0xd691687f
09: ROR    r0, 2
10: ADD    r0, 0xa74821c3
11: EQ     r0, 0xf2d032f4
12: OK
```

Check `1` has the same general shape but loads `input[1]`. This continues through check `47`, which loads `input[47]`.

So the scary-looking math is really just a complicated way to ask:

> “Is this one character the character I expect?”

All operations use 32-bit arithmetic, meaning values wrap around after `0xffffffff`.

It would be possible to invert the additions, XORs, rotations, and odd multiplications. However, each input character has only 256 possible values. Trying all 256 is much simpler, and it takes less than a second for the whole flag.

---

## 6. Emulator and recovery

The inner registers are initialized from eight constants at `0x53f0`. They are mixed with the check number and the selected outer register before the inner program begins.

Here is the core concrete emulator used by the solver:

```python
BASE_REGS = list(unpack_from('<8I', binary, 0x53f0))

def ror(x, n):
    return rol(x, -n)

def fields(ins):
    return (
        ins[0],
        ins[1] & 7,
        ins[2] & 7,
        ins[3] & 31,
        int.from_bytes(ins[4:8], 'little'),
    )

def run_inner(check_id, user_input, outer_source=1, debug_value=0):
    code = decrypt_inner(binary, check_id)

    # For every real CHECK instruction, outer_source is outer r0.
    salt = debug_value ^ outer_source ^ check_id
    initial_add = (salt + check_id) & 0xffffffff
    regs = [xs(value + initial_add) for value in BASE_REGS]

    for pc in range(0, len(code), 8):
        op, a, b, c, imm = fields(code[pc:pc + 8])

        if op == 0x0a:       # MOV
            regs[a] = imm
        elif op == 0x0f:     # ADD
            regs[a] = (regs[a] + imm) & 0xffffffff
        elif op == 0x21:     # OK
            return 1
        elif op == 0x26:     # XOR3
            regs[a] = (imm ^ regs[a] ^ regs[b] ^ regs[c & 7]) & 0xffffffff
        elif op == 0x30:     # IN
            if imm >= len(user_input):
                return 0
            regs[a] = user_input[imm]
        elif op == 0x59:     # ROLADD
            regs[a] = rol(regs[a] + regs[b] + imm, c)
        elif op == 0x71:     # ROL
            regs[a] = rol(regs[a], b)
        elif op == 0x76:     # MIX
            regs[a] = xs(regs[b] + regs[a] + salt + imm)
        elif op == 0x7d:     # EQ
            if regs[a] != imm:
                return 0
        elif op == 0x93:     # SUB
            regs[a] = (regs[a] - imm) & 0xffffffff
        elif op == 0xa7:     # ROR
            regs[a] = ror(regs[a], b)
        elif op == 0xab:     # XOR
            regs[a] = (regs[a] ^ imm) & 0xffffffff
        elif op == 0xd2:     # MUL
            regs[a] = (regs[a] * (imm | 1)) & 0xffffffff
        else:
            return 0

    return 0
```

Recovery is then tiny:

```python
flag = bytearray(b'?' * 48)

for position in range(48):
    matches = []

    for candidate in range(256):
        flag[position] = candidate
        if run_inner(position, flag):
            matches.append(candidate)

    assert len(matches) == 1
    flag[position] = matches[0]

print(flag.decode())
```

Output:

```text
Thryve{d0ubl3_VM_1n_4_m1rr0r_0pc0d35_n3v3r_5t4y}
```

I also ran the recovered 48-byte input through all 88 real inner checks. Every check returned `1`, including checks `48` through `87`, which combine multiple characters and serve as extra validation.

---

## 7. Final verification

```bash
$ printf '%s\n' 'Thryve{d0ubl3_VM_1n_4_m1rr0r_0pc0d35_n3v3r_5t4y}' | ./chimera_mirror
phase> synchronization achieved
```

## Flag

```text
Thryve{d0ubl3_VM_1n_4_m1rr0r_0pc0d35_n3v3r_5t4y}
```

## Takeaway

The challenge looks intimidating because it stacks several layers together:

1. stripped native code,
2. anti-debugging,
3. encrypted outer bytecode,
4. an outer VM,
5. encrypted inner bytecode,
6. a second VM,
7. lots of noisy 32-bit math.

But once those layers are separated, the final weakness is straightforward: the first 48 inner programs validate one byte at a time. A small emulator turns the “mesmerizing symphony played by math” into only `48 × 256 = 12,288` quick guesses.
