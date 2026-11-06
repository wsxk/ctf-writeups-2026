# squ1rrel-o-tron

**Category:** Rev | **Difficulty:** Hard | **Flag:** `squ1rrel{why_run_l1nux_0n_4_pr1nt3r_wh3n_y0u_c4n_run_l1nux_0n_4_pdf}`

## TL;DR

A 3.9MB PDF that literally boots a RISC-V Linux VM (via TinyEMU compiled to JavaScript) inside Adobe Acrobat. The VM runs a challenge binary that uses two **custom, non-standard RISC-V instructions** implemented only in the patched emulator. Recover those instruction semantics from the asm.js source, extract the SBOX from the binary's initialization data, reimplement the 4096-round mixing function in Python, and answer 5 challenge-response rounds to get the flag.

## What We're Given

- **`linux.pdf`** — a 3.9MB, 1-page PDF. Yes, really.
- **`server.py`** — the challenge server source. It generates a random 32-byte nonce, calls `F(nonce)` to get a 16-byte expected response, and gives you 5 rounds with 5 seconds each. If you answer all 5 correctly, you get the flag. The catch: `F` is defined as `raise NotImplementedError`. The actual implementation lives somewhere inside the PDF.

The flavor text says: *"Back in high school, they only let me keep PDFs on my school computer account. Fortunately, you can do a lot more with PDFs than just read them."* That's the author telling you straight up: the PDF IS the computation.

## Initial Recon

First instinct with any mystery file: `file` and `strings`.

```
$ file linux.pdf
linux.pdf: PDF document, version 1.3, 1 page
```

Boring so far. But `pdfinfo linux.pdf` says `JavaScript: yes`. That's interesting. PDFs can embed JavaScript that runs when the file is opened in a full PDF reader like Adobe Acrobat — not just a browser's basic PDF viewer. This is a legitimate (if terrifying) feature.

Extracting the embedded JavaScript reveals something wild: 3.7 megabytes of code. The first line is:

```
/*! pako 2.1.0 ...*/
```

Pako is a JavaScript port of zlib — a decompression library. Something is being decompressed at runtime. Scrolling further, you start to see strings like:

```js
Module["_virt_machine_run"]
Module["_vm_start"]
Module["_fs_import_file"]
```

And then: `"use asm"` — the marker for asm.js, Mozilla's old subset of JavaScript designed to compile C code into high-performance JS.

At this point the picture crystallizes: this is **TinyEMU** — Fabrice Bellard's compact RISC-V emulator — compiled to JavaScript via Emscripten. The PDF boots a whole computer when opened.

## The "Oh No" Moment

Digging into the JS further, there's a variable called `embedded_files` containing 14 named entries, each a base64+zlib-compressed blob. After decoding them, you find:

| File | What it is |
|---|---|
| `bbl32.bin` | Berkeley Bootloader — the M-mode RISC-V firmware (54KB) |
| `kernel-riscv32.bin` | An actual Linux kernel, RISC-V 32-bit (3.25MB!) |
| `vm_32.cfg` | TinyEMU config: riscv32, 128MB RAM, 9p rootfs |
| `root/files/0000000000000001..9` | rootfs entries: busybox, init script, and... `chall` |

The `chall` file is a stripped RISC-V ELF binary sitting in `/root/chall` inside the VM's filesystem. This is what the server actually runs to compute `F(nonce)`. The PDF isn't just decoration — it IS the black box.

So to solve this, we need to understand what `chall` does. But there's an immediate problem.

## The Vulnerability / Trick

### Dead End #1: Just run it under QEMU

The obvious move is: extract the `chall` ELF, run it under `qemu-riscv32`, and trace what it does.

```bash
$ echo "0000000000000000000000000000000000000000000000000000000000000000" | qemu-riscv32 ./chall
# silence, then exit code 1
```

QEMU exits immediately. Running with `-d in_asm` to get execution traces produces... nothing. The binary crashes before a single instruction gets logged.

Why? Because `chall` uses **custom, non-standard RISC-V instructions**. QEMU sees them as illegal instructions and throws SIGILL immediately. These opcodes don't exist in any standard RISC-V specification.

### Dead End #2: Maybe the bootloader handles them?

A natural guess: RISC-V has a well-defined trap mechanism. When an illegal instruction fires, execution jumps to the machine-mode trap handler. BBL (the Berkeley Bootloader) already intercepts some traps to emulate multiply/divide instructions. Maybe the custom opcodes are handled there?

Disassembling `bbl32.bin` with Capstone: the illegal-instruction handler at `0x80002a1c` only handles standard M-extension opcodes (mul/div). Nothing custom. Dead end.

### The actual answer: the emulator was patched

The custom opcodes aren't emulated in firmware or the kernel. They're handled in the JavaScript emulator itself — in the asm.js code inside the PDF.

RISC-V instruction decoding uses a hierarchical scheme: the bottom 7 bits are the opcode, then funct3, then funct7. Standard opcode `0x33` (binary `0110011`) is for integer register-register instructions. The asm.js emulator has a `switch` statement that dispatches on opcode, and inside the `case 51` branch (0x33), after all the standard ADD/SUB/SLL/etc. cases, there are two extra handlers:

```js
case 51: {
  k = f >>> 25;           // funct7 field
  j = reg[rs1];           // rs1 value
  h = reg[rs2];           // rs2 value
  i = (f & 28672) == 0;   // funct3 == 0?

  if (k == 126 && i) {
    // funct7=0x7E: STATE = rs1
    STATE = j;
    f = 0;
  } else if (k == 127 && i) {
    // funct7=0x7F: the actual mixing transform
    // ...
  }
}
```

Two custom R-type instructions, funct7=0x7E and funct7=0x7F. The first one (`0x7E`) just sets a global state variable to the value of register rs1. The second one (`0x7F`) is where all the interesting computation happens.

### The mixing transform (custom insn 0x7F)

The transform takes `j` (rs1), `h` (rs2), and a persistent `STATE` value, and produces a new register value plus an updated STATE. Here's what it does, step by step:

```js
n = STATE
// 1. Single-byte SBOX lookup using XOR of all three inputs
o_byte = SBOX[(h ^ j ^ n) & 0xff]
// 2. Spread that byte to all four byte positions of a 32-bit word
o = (o_byte | (o_byte << 8) | (o_byte << 16) | (o_byte << 24)) ^ j
// 3. Rotate left by a key-dependent amount
m_shift = (n ^ h) & 31
rotated = rotl32(o, m_shift)
// 4. Mix with a word-expanded SBOX of h, multiplied by h
m = (rotated + sbox_word(h) * h) & 0xFFFFFFFF
// 5. XOR with state
o2 = m ^ n
// 6. Final result: SBOX-expand o2, XOR with m
result = sbox_word(o2) ^ m
// 7. Update STATE for next call
STATE = sbox_word((m + n) & 0xFFFFFFFF) ^ o2
```

Where `sbox_word(x)` applies the SBOX to each byte of `x` independently and packs them back into a 32-bit word.

This is a custom keyed transformation — essentially a nonlinear mixing primitive with stateful carry. Not anything standard, entirely bespoke.

### Extracting the SBOX

The asm.js code references SBOX values as `d[10304 + byte]` — indexing into the heap array `d`. The heap is initialized from a base64 blob in the `memoryInitializer` field of the Emscripten module. Decoding that blob gives a 17568-byte array. Scanning for a 256-byte region containing all values 0..255 exactly once (the hallmark of a substitution box — it's a permutation) turns up the SBOX starting at raw offset 10296.

The SBOX starts:
```
6c 39 78 ce 3d f6 83 dd 30 f4 f5 5f 13 8e 35 1c ...
```

Not AES's S-box. Completely custom.

### What chall actually does

Disassembling the `chall` ELF with Capstone (using `CS_ARCH_RISCV | CS_MODE_RISCV32 | CS_MODE_RISCVC` for compressed instruction support), the main function:

1. Reads 64 ASCII hex characters from stdin (the nonce)
2. Hex-decodes to 32 bytes, treated as 8 little-endian 32-bit words `buf[0..7]`
3. Fires custom insn `0x7E` with `buf[0]` to initialize STATE
4. Runs a nested loop:
   - Outer: `a2` starts at 0, increments by `0x19f3dc31`, stops when `a2 == 0x3dc31000`
   - Inner: iterates over all 8 words, applying custom insn `0x7F` with each word and its neighbor
   - Because `gcd(0x19f3dc31, 2^32) = 1`, the outer loop wraps exactly **4096 times** before hitting the target
5. Hex-encodes the first 16 bytes of the result (first 4 words) and prints them

So F takes 32 bytes in, does 4096 × 8 = 32,768 calls to the custom transform, and outputs the first 16 bytes.

## Building the Exploit

With all the pieces understood, the solve script is a straightforward Python reimplementation.

**Step 1: The SBOX.** Hardcoded as a hex string extracted from the memoryInitializer blob:

```python
SBOX = bytes.fromhex(
    '6c3978ce3df683dd30f4f55f138e351c'
    '4d936fc71b198043c6f0cb2fd147befa'
    # ... all 256 bytes
)
```

**Step 2: Helper functions.** `sbox_word` applies the SBOX byte-by-byte across a 32-bit word. `rotl32` is a standard left-rotate that masks properly to 32 bits:

```python
def sbox_word(x):
    b0 = SBOX[x & 0xff]
    b1 = SBOX[(x >> 8) & 0xff]
    b2 = SBOX[(x >> 16) & 0xff]
    b3 = SBOX[(x >> 24) & 0xff]
    return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

def rotl32(x, n):
    n &= 31
    if n == 0:
        return x & MASK
    return ((x << n) | (x >> (32 - n))) & MASK
```

**Step 3: The F function.** This directly mirrors the disassembled chall logic, with the custom instruction semantics plugged in:

```python
def F(nonce: bytes) -> bytes:
    buf = [int.from_bytes(nonce[4*i:4*i+4], 'little') for i in range(8)]
    state = buf[0]   # custom_126: initialize STATE

    a2 = 0
    while True:
        running_key = a2
        for i in range(8):
            w = buf[i]
            k = buf[(i + 1) % 8]
            # custom_127(j = w ^ running_key, h = k)
            j = (w ^ running_key) & MASK
            h = k
            n = state
            o = SBOX[(h ^ j ^ n) & 0xff]
            o = ((o << 8) | o | (o << 16) | (o << 24)) & MASK
            o = o ^ j
            m_shift = (n ^ h) & 31
            rotated = rotl32(o, m_shift)
            m = (rotated + (sbox_word(h) * h)) & MASK
            o2 = m ^ n
            result = (sbox_word(o2) ^ m) & MASK
            state = (sbox_word((m + n) & MASK) ^ o2) & MASK
            buf[i] = result
            running_key = (running_key + 0x9f0ce81c) & MASK
        a2 = (a2 + 0x19f3dc31) & MASK
        if a2 == 0x3dc31000:
            break

    return b''.join(x.to_bytes(4, 'little') for x in buf[:4])
```

Note the loop termination condition: we check `a2 == 0x3dc31000` AFTER incrementing, which is exactly what the binary does. Getting this backwards would produce a 4097-iteration loop instead of 4096. (Ask me how I know to call this out specifically.)

**Step 4: Connect and solve.** The server protocol is simple — it sends `round N: <64-hex-chars>` and expects back 32 hex chars (the first 16 bytes of F's output), repeated 5 times:

```python
def solve(host='challs.squ1rrel.dev', port=5002):
    s = socket.create_connection((host, port), timeout=30)
    f = s.makefile('rwb')
    banner = f.readline()
    for _ in range(5):
        line = f.readline().decode().rstrip()
        nonce_hex = line.split()[-1]
        nonce = bytes.fromhex(nonce_hex)
        out = F(nonce)
        f.write((out.hex() + '\n').encode())
        f.flush()
    print(s.recv(4096).decode())
```

Each call to `F` takes roughly 90ms in Python (4096 rounds × 8 words = ~33,000 transform calls). Well under the 5-second round limit.

## Running It

```
$ python3 solve.py
banner: squ1rrel-o-tron challenge -- 5 rounds, 5s each
< round 1: a3f2c1...
> 7e4b9d...
< round 2: 02fb8e...
> c1a734...
< round 3: ...
...
final: squ1rrel{why_run_l1nux_0n_4_pr1nt3r_wh3n_y0u_c4n_run_l1nux_0n_4_pdf}
```

Five rounds, all correct, flag on the first try.

The flag is a riff on the old joke about running Linux on a toaster — "why run Linux on a printer when you can run Linux on a PDF." Which is, frankly, exactly the right energy for this challenge.

## Key Takeaways

**The core trick:** PDFs support embedded JavaScript via `/JS` Open Actions, and that JavaScript can do essentially anything a browser can do — including running a RISC-V emulator compiled to asm.js, which in turn boots a real Linux kernel. This isn't a theoretical attack; TinyEMU-in-a-PDF is a real demo Fabrice Bellard has published.

**The rev angle:** The hard part wasn't understanding "Linux in a PDF." The hard part was recognizing that the emulator was *patched* to add custom instructions that don't exist in any public documentation. The tell is that the binary SIGILLs on QEMU — illegal instructions signal "this only runs in a custom emulator."

**Finding custom opcodes in emulators:** When you see `case 51` (opcode 0x33) in an asm.js RISC-V emulator's dispatch table and the funct7 values are outside the standard range (0x00–0x20 for typical opcodes), those are your custom instructions. The semantics are right there in the JavaScript.

**SBOX extraction from memoryInitializer:** Emscripten-compiled binaries often store lookup tables in the `memoryInitializer` base64 blob. A 256-byte region containing every value 0x00–0xFF exactly once is almost certainly an S-box. Scan for it programmatically.

**Tools worth knowing:**
- `pdfinfo` — quick check for PDF JavaScript presence
- Capstone — Python-friendly disassembler; supports RISC-V including compressed (`CS_MODE_RISCVC`)
- pako — if you see it in extracted JS, there's something being decompressed at runtime worth looking at

**Gotcha on loop counts:** The outer loop increment `0x19f3dc31` and target `0x3dc31000` look arbitrary. But `gcd(0x19f3dc31, 2^32) = 1`, which means the sequence visits all 2^32 values before repeating. The target was chosen so the loop terminates after exactly 4096 steps. Computing this upfront (or just trusting the disassembly) saves you from wondering if your reimplementation is wrong.

If you want to dig deeper into PDF JavaScript abuse, look at Bellard's original [jslinux](https://bellard.org/jslinux/) and [TinyEMU](https://bellard.org/tinyemu/) projects — the PDF challenge is basically those jammed into a `/JS` Open Action. For RISC-V custom instruction extensions, the RISC-V ISA manual chapter on custom encodings is the reference (opcode spaces `0x0B`, `0x2B`, `0x5B`, `0x7B`, and the "custom" funct7 ranges in `0x33`/`0x3B` are explicitly reserved for vendor use).
