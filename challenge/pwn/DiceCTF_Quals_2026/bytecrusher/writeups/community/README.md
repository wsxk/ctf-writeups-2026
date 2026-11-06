# ByteCrusher

**Category:** Pwn | **Difficulty:** Hard (500 pts, 0 solves) | **Flag:** `dice{pwn3d_4nd_coRuSh3d}`

## Overview

You get a binary that "crushes" strings — it takes your input, skips characters based on a "crush rate", and gives you the shorter version. You get 16 free trials of this service, then it asks for feedback. The feedback function uses `gets()`, which is the classic "please hack me" function in C.

## The Binary

The program has four functions that matter:

- **`main()`** — Calls `free_trial()`, then `get_feedback()`, then exits. There's an `admin_portal()` function that reads the flag, but it's gated behind `COMPILE_ADMIN_MODE` which is hardcoded to 0. It never gets called normally.
- **`free_trial()`** — Loops 16 times. Each iteration: reads a string (up to 32 bytes), asks for a "crush rate" and "output length", then runs `crush_string()` on it.
- **`crush_string()`** — Takes the input and copies every Nth character (where N is the crush rate) into an output buffer.
- **`get_feedback()`** — Reads feedback using `gets()` into a 32-byte buffer. No size limit. Classic buffer overflow.

Protections are maxed out: Full RELRO, Stack Canary, NX, PIE, SHSTK, and IBT. So you can't just smash the stack blindly — you need to know the canary value and the correct address to jump to.

## The Bugs

### Bug 1: Out-of-Bounds Read via crush_string()

Here's the crush function:

```c
void crush_string(char *input, char *output, int rate, int output_max_len) {
    if (rate < 1) rate = 1;
    int out_idx = 0;
    for (int i = 0; input[i] != '\0' && out_idx < output_max_len - 1; i += rate) {
        output[out_idx++] = input[i];
    }
    output[out_idx] = '\0';
}
```

It walks through the input buffer jumping `rate` bytes at a time. The loop only stops when it hits a null byte (`\0`). If you set the rate high enough (say, 73), it jumps from `input[0]` straight to `input[73]` — completely skipping over the null terminator at `input[31]`. Now it's reading memory it was never supposed to touch.

On the stack, the memory layout looks like:

```
input_buf  [0-31]   <- our input (null at byte 31)
crushed    [32-63]  <- output buffer
canary     [72-79]  <- stack canary (secret value that detects overflow)
saved rbp  [80-87]  <- saved frame pointer
return addr [88-95] <- where the function returns to
```

So with rate=73, we read `input[0]` (which we control, it's 'A') and then `input[73]` which is canary byte 1. The program happily prints this back to us. We just leaked a secret byte from the stack.

### Bug 2: Buffer Overflow in get_feedback()

```c
void get_feedback() {
    char buf[16];
    gets(buf);  // no size limit lol
}
```

`gets()` reads until a newline with absolutely no bounds checking. The buffer is only 32 bytes from the frame pointer, but we can write as much as we want. This lets us overwrite the canary, saved frame pointer, and return address.

## The Exploit

### Step 1: Leak the Stack Canary (iterations 0-6)

The canary is 8 bytes. Byte 0 is always `0x00` (by design, to make accidental overwrites harder). We need bytes 1-7.

For each byte, we use a crush rate that lands exactly on it:
- Rate 73 → reads offset 73 → canary byte 1
- Rate 74 → reads offset 74 → canary byte 2
- Rate 75 → reads offset 75 → canary byte 3
- ... and so on up to rate 79 → canary byte 7

Each iteration gives us one byte. Seven iterations, seven bytes, full canary leaked.

### Step 2: Leak the Return Address (iterations 7-12)

Same trick, but we aim further down the stack. The return address sits at offsets 88-93 (we only need the first 6 bytes since the top 2 are always 0x00 in userspace).

- Rate 88 → return address byte 0
- Rate 89 → return address byte 1
- ... up to rate 93 → byte 5

This tells us the exact runtime address of `main`, which lets us calculate where `admin_portal` lives despite PIE randomization.

### Step 3: Burn Remaining Iterations (13-15)

We only needed 13 of our 16 iterations. The last 3 just get dummy input.

### Step 4: Overflow get_feedback()

Now we know the canary and the PIE base address. We construct a payload for `gets()`:

```
[24 bytes of padding] [8 bytes: correct canary] [8 bytes: fake rbp] [8 bytes: admin_portal address]
```

When `get_feedback()` returns, instead of going back to `main`, it jumps straight to `admin_portal()`, which opens `flag.txt` and prints the flag.

### One Nice Detail

The binary has a `getchar()` loop after each `scanf()` that drains any leftover characters from stdin. This means each of the 16 iterations is completely independent — no messy I/O state to manage between them. Keeps the exploit clean.

## Running It

```bash
python3 solve.py remote
```

```
[+] Canary: 0xc474b5ad7a1b1200
[+] Leaked ret: 0x00005bfd2206c5ec
[+] PIE base:   0x00005bfd2206b000
[+] admin_portal: 0x00005bfd2206c2a9
[+] FLAG: dice{pwn3d_4nd_coRuSh3d}
```

## Key Takeaways

- **Out-of-bounds reads from stride-based loops** — when a function walks memory with a configurable step size, it can skip over null terminators and leak adjacent stack data. Always check what happens when the stride is larger than the buffer.
- **Stack canary leaks make "impossible" overflows possible** — the canary is just a secret value. If you can read it through a side channel (or in this case, a direct OOB read), the protection evaporates.
- **PIE is only as strong as your address secrecy** — once you leak any code pointer, you can calculate every other address in the binary. One leak defeats the whole scheme.
- **`gets()` is never safe** — it's been removed from the C standard for a reason. Even with every other protection enabled, it gives attackers an unlimited write primitive.
