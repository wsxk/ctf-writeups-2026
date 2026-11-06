# Message Store

**Category:** Pwn | **Difficulty:** Hard (500 pts, 1 solve) | **Flag:** `dice{w0w...ru5t_1snt_s4f3??}`

## Overview
A Rust binary with a "100% safe" message store that lets you set a message, set its color, and print it. The color index is not bounds-checked, allowing an out-of-bounds function pointer call.

## Solution

### Vulnerability
The `set_message_color` function accepts any `usize` as a color index without checking bounds against the 7-entry color function table at `0x2f08e8`. This allows calling arbitrary function pointers from the GOT or other memory.

### Exploitation Primitive
Setting color index to **3356** reads from the memcpy GOT entry (`0x2f71c8`). When `print_message` is called, the color function becomes `memcpy`, called as:

```
memcpy(rsp+0x18, BUFFER_ptr, 0x1000)
```

This copies 0x1000 bytes onto the stack starting at rsp+0x18, overflowing past the return address at offset 0x60.

### The UTF-8 Constraint
Before the color function is called, `from_utf8_lossy` processes BUFFER. If ANY byte is invalid UTF-8, the function returns `Cow::Owned` with replacement characters, causing memcpy to copy corrupted heap data instead of the original BUFFER. **The entire 0x1000-byte payload must be valid UTF-8.**

This rules out most ROP gadget addresses since they contain bytes > 0x7f. However, multi-byte UTF-8 sequences can span across 8-byte boundaries in the payload.

### SROP Solution
Instead of building a complex ROP chain with UTF-8-safe gadgets, we use **Sigreturn-Oriented Programming (SROP)**:

1. **ROP preamble** (3 gadgets, all UTF-8-safe): set `rax=15` and call `syscall` for sigreturn
2. **SROP frame**: sets all registers for `execve("/bin/sh", NULL, NULL)` — rax=59, rdi=BUFFER+0x178, rsi=0, rdx=0, rip=syscall
3. **"/bin/sh\0"** placed at BUFFER offset 0x178

The key trick: the `rdi` value (0x2f9fb0) has bytes [0xB0, 0x9F] which are UTF-8 continuation bytes. By setting `r15` (the adjacent field before `rdi` in the signal frame) to `0xE000000000000000`, the last byte of r15 (0xE0) forms a valid 3-byte UTF-8 sequence with rdi's first two bytes: `E0 B0 9F` = U+0C1F.

See `solve.py` for the full exploit code.

## Key Takeaways
- Rust's `unsafe` blocks and FFI can introduce the same memory safety bugs as C/C++
- `from_utf8_lossy` creates a subtle data integrity constraint — the exploit payload must be valid UTF-8 or the Cow::Owned path corrupts the data
- SROP is powerful when normal ROP gadgets are constrained — it sets ALL registers from a single frame
- Multi-byte UTF-8 sequences spanning field boundaries can "fix" high bytes in adjacent values
- No PIE + No canary + known GOT layout = classic exploitation, but the UTF-8 constraint makes it uniquely challenging
