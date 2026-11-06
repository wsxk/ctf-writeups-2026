# Gaem

**Category:** Pwn | **Difficulty:** Hard | **Flag:** `squ1rrel{nptl_my_beloved_y0u_m4k3_th1s_g4m3_s0_ez}`

## TL;DR

A heap overflow in the pet rename function lets us overwrite a function pointer with `_IO_printf`, turning the "purr" call into a format string primitive. We use that primitive to corrupt the return address to a stack pivot gadget, pivot RSP into a BSS-resident ORW ROP chain, and read `flag.txt`. The spicy part: NPTL (pthreads init) silently dirtied the BSS at startup, so our chain had to land 2 bytes past where we first tried.

## What We're Given

A 64-bit static ELF named `gaem` and a remote service at `nc challs.squ1rrel.dev 5001`. The description says "It's like Dwarf Fortress but not at all like Dwarf Fortress," which is accurate — it's a tiny ASCII dungeon with a hero, three enemies, and two pets named Whiskers (cat) and Biscuit (dog).

```
$ file gaem
gaem: ELF 64-bit LSB executable, x86-64, statically linked, not stripped

$ checksec gaem
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    SHSTK:      Enabled
    IBT:        Enabled
```

Key properties to keep in mind as we go:
- **No PIE** — binary loads at a fixed 0x400000. All gadget addresses are known constants. No leak needed for code addresses.
- **NX** — can't inject shellcode. We need ROP.
- **Canary** — stack canary is present, so we can't just overwrite the return address directly with a linear overflow. We need another approach.
- **IBT (Indirect Branch Tracking)** — this is part of Intel CET (Control-flow Enforcement Technology). It means indirect `CALL` instructions will trap unless the target starts with an `endbr64` instruction. RETs are not checked by IBT (SHSTK handles RETs, but it's not enforced here at runtime).
- **Static binary** — everything is linked in, so we have a huge gadget surface to work with.

## Initial Recon

The game loop offers a main menu: `m`ove, `l`ook, `t`alk, `q`uit. Inside move mode you get `wasd` to walk, `e` to attack, `r` to rename a pet, and `q` to exit.

The interesting pieces after reverse engineering the binary:

**Pet struct** (allocated with `calloc(0x30)`, so initially zeroed):
```
[0x00..0x1f]  name (max 0x1f bytes + null terminator)
[0x20..0x27]  purr function pointer
[0x28..0x2b]  x coordinate
[0x2c..0x2f]  y coordinate
```

**Cat purr function** at `0x401a4e`:
```c
printf("A cat curls up and purrs: \"%s\"\n", 0);
```

**Dog purr function** at `0x401a2d`:
```c
printf("A dog wags and barks: \"%s\"\n", 0);
```

**Talk path** (`t` from main menu): reads up to 0x7f bytes of "spoken text" into a buffer on main's stack frame, then calls `pet->purr(spoken_text)`.

That call site at `0x401f15`:
```asm
mov rdi, r13    ; r13 = &spoken_text on stack
call qword [r12 + 0x20]   ; r12 = pet struct ptr; +0x20 = purr fn ptr
```

And here's the rename code that's about to ruin our day (in the best possible way):

```c
char var_158[0x30];
read_line(&var_158, 0x28);         // fgets reads up to 0x27 bytes + newline
strcpy(pet_struct, &var_158);      // copies until null — NO SIZE LIMIT
```

`read_line` reads up to `0x27` bytes (39 bytes), but the name field in the pet struct is only `0x1f` bytes (31 bytes). The `strcpy` will happily overwrite whatever comes after the name — which is the purr function pointer at offset `+0x20`.

## The Vulnerability / Trick

### Stage 1: Heap Overflow to Control the Function Pointer

The rename operation overflows the 0x1f-byte name field and reaches the purr function pointer 32 bytes in. Since there's no size check on `strcpy`, any rename payload that has 32+ non-null bytes will clobber the purr pointer.

We can't just point it at a `system("/bin/sh")` gadget or a raw syscall — IBT will kill us. The `CALL` instruction checks for `endbr64` at the target. But `_IO_printf` at `0x4056b0` starts with `endbr64`. It's a valid IBT call target, and it's sitting right there in our static binary.

So the plan: overwrite `purr` with `_IO_printf`, then use `t` (talk) to pass a format string as the first argument. Format string exploitation — where the server passes user input directly to `printf` as the format string, letting us read and write arbitrary memory.

### Stage 2: Format String to Corrupt the Return Address

When our hijacked purr calls `_IO_printf(spoken_text)`, the spoken text IS the format string. Printf walks up the stack reading "arguments," and we can use `%N$p` to read the Nth argument as a pointer, and `%N$hhn` to write one byte to the address stored in the Nth argument slot.

The stack when printf runs contains some very interesting data:
- `rename_buf` (the 39-byte buffer from the rename operation) sits on main's stack frame right where printf's arg slots are
- This means values we wrote during rename are now printf's "arguments" that `%N$hhn` can write through

By carefully crafting the rename payload to put the address of the return address into specific argument slots, we can overwrite the return address byte by byte without touching the stack canary at all.

The original return address at that call site is `0x401f1a`. We want to change it to `0x4018b8` — our stack pivot gadget. That means changing byte 0 from `0x1a` to `0xb8` (184 in decimal) and byte 1 from `0x1f` to `0x18` (total 280 chars printed, `280 & 0xff = 0x18`).

```python
TRIGGER_FMT = b'%184c%12$hhn%96c%13$hhn'
#              ^^^^^^^^^^^  write 0xb8 to retaddr[0]
#                           ^^^^^^^^^^ write 0x18 to retaddr[1] (184+96=280=0x118)
```

### Stage 3: Stack Pivot into a BSS ROP Chain

After printf returns, RIP becomes `0x4018b8`. What's there?

Here's a fun trick: at `0x4018b7` there's a `pop r12; pop rbp; ret` instruction (bytes: `41 5c 5d c3`). If you skip the first byte (`41` is the REX prefix for r12), you land at `0x4018b8` which is bytes `5c 5d c3`. In 64-bit mode, `5c` without a REX prefix is `pop rsp` (not `pop r12`). So `0x4018b8` = `pop rsp; pop rbp; ret`.

This is a classic "instruction misalignment" trick — finding a useful gadget hidden inside another instruction. The CPU doesn't know or care that we jumped into the middle of the previous instruction's bytes.

`pop rsp` loads a new value into the stack pointer. If we control what's at `[rsp]` when this executes, we redirect the entire stack to wherever we want. We'll point it at our pet struct (whose address we leaked earlier), which we've pre-loaded with a `leave; ret` gadget, whose RBP we've aimed at `CHAIN_BSS - 8` (our ROP chain in BSS, minus 8 for alignment). The `leave` instruction executes `rsp = rbp; pop rbp` — the second pivot that lands us executing right at the start of our ORW chain.

### Stage 4: Open-Read-Write ROP Chain

With RSP pointing into our chain, we do the classic CTF ORW (Open-Read-Write) to read `flag.txt`:

```
open("flag.txt", 0)     → rax = file descriptor
xchg edi, eax           → move fd into rdi for the next call
read(fd, READ_BUF, 0x200)  → flag bytes land in BSS
write(1, READ_BUF, 0x200)  → dump to stdout
```

One wrinkle: we need to set `rdx` (the length argument) for both `read` and `write`, but there's no clean `pop rdx; ret`. Instead there's `pop rdx; leave; ret` at `0x470843`. We use it with a fake `rbp` setup so the `leave` re-pivots us to the next gadget sequence. It's a little like a chain of dominoes — each `leave` re-aims `rsp` at the next section of the chain.

## Building the Exploit

Here's the full 5-phase strategy:

### Phase 1: Leak Stack and Heap Addresses

Move the hero adjacent to Whiskers (needs `ddssr` from starting position), then rename with `b'A'*32 + p64(PRINTF)[:3]`. The last 3 bytes of `_IO_printf`'s address overwrite the purr pointer — we only need 3 bytes because the upper bytes are already zero (address is `0x4056b0`, upper 5 bytes are `\x00\x00\x00\x40\x56` — wait, actually `\x4056b0` is `\xb0\x56\x40\x00\x00\x00\x00\x00`; the first non-null bytes are `\xb0\x56\x40`, 3 bytes, then the null terminator stops strcpy from going further).

Now talk with `b'|%7$p|%32$p|'` to leak:
- `%7$p` — a stack pointer that tells us where `rename_buf` lives on the stack
- `%32$p` — the cat struct pointer (Whiskers), which gives us the heap address

From these we compute `spoke_addr` (where our format string lives) and `ret_addr_loc` (where printf's return address sits on the stack, which we need to overwrite).

```python
spoke_addr   = arg7 + 0x30     # empirically: rename_buf to spoke is 0x30 bytes
ret_addr_loc = spoke_addr - 0x58
```

### Phase 2 & 3: Write "flag.txt" and the ROP Chain to BSS

Using the format string primitive repeatedly, we write individual bytes to BSS. Each write: rename with the target address at position 10 in the argument list, then talk with `%N$hhn` to write a value to it.

```python
def write_byte(p, addr, byte_val):
    payload = p64(addr) + b'B' * 24 + p64(PRINTF)[:3]
    rename_cat(p, payload)
    fmt = b'%10$hhn' if byte_val == 0 else f'%{byte_val}c%10$hhn'.encode()
    talk(p, fmt)
```

We write `flag.txt\0` to `FLAG_BSS = 0x4c8e00`, and the 224-byte ORW chain to `CHAIN_BSS = 0x4c8d02`. We skip writing zero bytes (`skip_zero=True`) because BSS is clean there and those bytes are already zero — which saves about 100 round trips to the server and keeps us inside the binary's alarm timeout.

**The NPTL gotcha:** We initially picked `CHAIN_BSS = BSS + 0x200 = 0x4c8d00`. But when we ran locally, the exploit kept segfaulting mysteriously. Checking the actual BSS at runtime revealed that `0x4c8b20..0x4c8be0` was full of non-zero data — pthreads/NPTL initialization writes lock state, TLS metadata, and malloc arena info into the BSS at startup. The flag in the challenge says it all: `nptl_my_beloved`. We shifted to `CHAIN_BSS = BSS + 0x202 = 0x4c8d02`, which is in a verified-clean region with no non-zero bytes and — critically — no `0x0a` bytes in any chain address (which would truncate our fgets-based writes).

### Phase 4: Pre-Set the Pet Struct for the Pivot

The trigger rename writes `p64(CHAIN_BSS-8)` as the first 8 bytes of the pet name via strcpy. But `CHAIN_BSS - 8 = 0x4c8cfa`, so `p64(0x4c8cfa) = \xfa\xcf\x4c\x00\x00\x00\x00\x00`. Strcpy stops at the first null byte — after writing only the first 3 bytes (`\xfa\xcf\x4c`), it stops. Bytes 3-7 of the pet struct need to be zero for the address to be correct, but the Phase 1 rename wrote `A`s there. We pre-zero them with `write_byte` calls.

Similarly, bytes 8-15 need to hold `LEAVE_RET = 0x4049f6` — our second pivot gadget. The trigger rename's strcpy stops before reaching byte 3, so it never touches bytes 8-15. We pre-write the value via `write_byte`.

### Phase 5: The Trigger

The trigger rename payload (35 bytes) is carefully constructed:

```python
trigger_rename = (
    p64(CHAIN_BSS - 8)   +   # bytes 0-7: fake rbp (only [0..2] written by strcpy)
    p64(LEAVE_RET)        +   # bytes 8-15: second pivot (pre-written, not touched by strcpy)
    p64(ret_addr_loc)     +   # arg12: address of retaddr[0] → target for %12$hhn
    p64(ret_addr_loc + 1) +   # arg13: address of retaddr[1] → target for %13$hhn
    p64(PRINTF)[:3]           # purr fn ptr overwrite at offset 32
)
```

Then we talk with `b'%184c%12$hhn%96c%13$hhn'`.

One more subtle piece: the rename also incidentally writes `ret_addr_loc + 8 = pet_ptr` into the stack slot right after the return address. When `pop rsp; pop rbp; ret` runs, it pops `pet_ptr` into RSP. That's our heap-allocated cat struct, which now holds `CHAIN_BSS-8` at offset 0 and `LEAVE_RET` at offset 8. The `pop rbp; ret` portion reads those and away we go.

## Running It

```
$ python3 solve.py
[*] Waiting for hero name prompt...
[*] === Phase 1: Leak stack and pet_ptr ===
[*] Leak: '|0x7fff4a2e6e68|0x55a3b2c4d010|'
[+] arg7         = 0x7fff4a2e6e68
[+] spoke_addr   = 0x7fff4a2e6e98
[+] ret_addr_loc = 0x7fff4a2e6e40
[+] pet_ptr      = 0x55a3b2c4d010
[*] Writing flag path (9B) to 0x4c8e00
[*] Writing ORW chain (224B) to 0x4c8d02
[*] === Phase 4: Pre-write pet_struct pivot values ===
[*]   Zeroing pet_struct[3..7]...
[*]   Writing LEAVE_RET to pet_struct[8..15]...
[*] === Phase 5: Trigger ===
[*] Trigger sent — waiting for flag...
[*] Received 512 bytes
[+] FLAG: squ1rrel{nptl_my_beloved_y0u_m4k3_th1s_g4m3_s0_ez}
```

It takes a while — we're making roughly 100+ round trips to write individual bytes to BSS. But it works.

## Key Takeaways

**The core chain:** heap overflow → function pointer hijack → format string → return address overwrite → stack pivot → ROP ORW.

**IBT is annoying but bypassable.** It blocks indirect calls to non-`endbr64` targets, so you can't just call a raw gadget. But large static binaries are full of functions that start with `endbr64` — `printf`, `malloc`, math functions, etc. If the target is a real function, it's probably IBT-safe.

**The "hidden gadget" trick.** `pop rsp; pop rbp; ret` at `0x4018b8` exists because those bytes happen to appear in the middle of a `pop r12; pop rbp; ret` instruction. Disassemblers won't show you this — you have to scan for the byte sequence `5c 5d c3` manually or use a gadget finder that checks all offsets.

**NPTL dirties the BSS.** Even though BSS is "zero-initialized" according to the ELF spec, the runtime (pthreads, NPTL, glibc's malloc) will write stuff there before `main` runs. Don't assume BSS is clean. Always check at runtime. The challenge author baked this into the flag itself as a gentle troll.

**The `pop rdx; leave; ret` double-pivot trick.** When you don't have a clean `pop rdx; ret` gadget, look for `pop rdx; leave; ret`. You can use it by setting up a fake `rbp` before the gadget, so the `leave` (`rsp = rbp; pop rbp`) lands you at the next section of your chain instead of crashing.

**Byte-by-byte BSS writes are slow.** Each write costs two server round trips (one rename, one talk). With 200 bytes to write, that's 400+ interactions. Always use `skip_zero=True` when your target region is already zeroed — it can cut the interaction count in half and keep you inside server-side timeout limits.

If you want to dig deeper into these techniques:
- Format string exploitation fundamentals: https://ctf101.org/binary-exploitation/format-string-vulnerabilities/
- Intel CET / IBT: https://www.intel.com/content/www/us/en/developer/articles/technical/technical-look-control-flow-enforcement-technology.html
- Stack pivoting in ROP: https://ir0nstone.gitbook.io/notes/types/stack/stack-pivoting
