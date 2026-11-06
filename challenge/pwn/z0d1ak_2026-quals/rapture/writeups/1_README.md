# Rapture

**Category:** Pwn | **Points:** 500 | **Author:** Abhi404 | **Flag:** `zdk{FREED_LN_The_de3P_BU7_n3VER_FOrgoT73N}`

## Description
> Rapture Deep Station is holding at 2000 fathoms.
> Take the station's master key with you.

## TL;DR
A "backup" feature snapshots a heap-manifest entry but copies only the pointer, not the payload it points to — so two entries end up owning the same chunk. Freeing one gives a use-after-free through the other, which we ride all the way to a libc leak, tcache poisoning past safe-linking, a stack leak via `environ`, and a ROP chain written straight onto `main`'s saved return address.

## Initial Analysis

The handout is three files:

```text
rapture
libc.so.6
ld-linux-x86-64.so.2
```

The supplied libc identifies itself as Ubuntu glibc 2.35. `checksec` on the binary shows nearly every mitigation turned on:

```text
Arch:       amd64
RELRO:      Full RELRO
Stack:      Canary found
NX:         NX enabled
PIE:        PIE enabled
SHSTK:      Enabled
IBT:        Enabled
Stripped:   No
```

What that buys the author:

- **Full RELRO** kills the usual GOT-overwrite trick.
- **NX** means no executing injected heap/stack bytes.
- **PIE** randomizes the binary's base.
- The **canary** catches ordinary stack-buffer overflows.
- The file advertises CET (shadow stack / IBT), but shadow-stack enforcement was **not** active in the supplied local/remote runtime, so a normal ROP chain works.

Helpfully, the binary is **not stripped**, so `main`, `manifest`, and `read_long` are all named.

The program manages up to 64 "ballast cells" via a menu:

```text
[1] Requisition ballast cell   (malloc)
[2] Recalibrate cell payload   (edit once)
[3] Jettison cell              (free)
[4] Inspect cell               (show once)
[5] Commit redundancy snapshot (copy an entry)
[6] Surface                    (exit)
```

Each manifest entry is `0x20` bytes:

```c
struct cell {
    char   *data;          // +0x00
    size_t  size;          // +0x08
    int     occupied;      // +0x10
    int     read_ticket;   // +0x14
    int     write_ticket;  // +0x18
    int     padding;       // +0x1c
};
struct cell manifest[64];
```

Allocations range 1..`0x408` bytes, and each fresh entry gets exactly one read ticket and one write ticket. That one-shot read/write limit is what makes the interface *look* safe.

## Vulnerability / Core Concept

The snapshot operation (menu 5) copies all `0x20` bytes of a source entry into an empty backup entry — effectively two 16-byte `movdqa`/`movaps` copies. Crucially it copies the raw `data` pointer; it does **not** allocate a fresh buffer.

Think of two luggage tags printed with the same locker number. Throwing one tag away doesn't empty the locker printed on the other. Here, jettisoning one entry genuinely frees the shared chunk while the second entry keeps pointing into it:

```text
allocate cell 0  ---> heap chunk X
snapshot 0 to 1  ---> cells 0 and 1 both point to X
free cell 0      ---> X returned to malloc
inspect cell 1   ---> read the freed chunk
edit cell 1      ---> write to the freed chunk
```

Because the snapshot also copies the read/write tickets, every new alias comes with its *own* fresh tickets, so the one-use limit never bites. That single duplicated pointer is the whole exploit primitive: a use-after-free with read and write.

## Exploitation

Full chain in [`solve.py`](./solve.py). Four phases:

**Phase 1 — leak libc.** glibc 2.35's tcache holds seven chunks per size class. The max request `0x408` produces a `0x410` chunk that still fits tcache. Allocate nine `0x408` cells, snapshot cell 7 into cell 9, then free cells 0..6 to fill the tcache bin. Freeing cell 7 (with cell 8 left as a guard so it can't merge into top) pushes it into the **unsorted bin**, whose `fd`/`bk` point into `main_arena`. Inspecting the dangling alias in cell 9 leaks that pointer:

```python
libc.address = u64(show(9)[:8]) - UNSORTED_FD   # 0x21ace0 in this libc
```

**Phase 2 — arbitrary allocation via tcache poisoning.** glibc safe-linking stores `encoded_next = real_next XOR (chunk_addr >> 12)`. When a chunk is the sole entry in its bin, its real next is NULL, so the stored word is just `chunk_addr >> 12` — which our dangling alias can read directly, defeating safe-linking. The `poison()` helper frees a chunk alone to recover that mask, then builds a two-entry `B -> A` tcache list and overwrites `B->next` with `target ^ mask`. The two-entry list matters: tcache tracks its count separately, so a single-entry list would zero out and ignore the poisoned pointer. Two allocations later, `malloc` returns `target`.

**Phase 3 — find the stack.** Poison an allocation over libc's `environ` to leak a stack pointer:

```python
env_cell = poison(libc.sym.environ, 0x28, 0, 1, 2, 3)
environ = u64(show(env_cell)[:8])
```

Rather than trust a fixed `environ`→saved-RIP delta (fragile across env/arg layout changes), the exploit reads a broad stack window and searches for the known return site — the instruction glibc returns to right after calling `main` (`libc_base + 0x29d90`):

```python
scan_start = (environ - 0x3f0) & ~0xf
scan_cell  = poison(scan_start, 0x3f8, 4, 5, 6, 7)
stack      = show(scan_cell)
return_site = libc.address + CALL_MAIN_RET
hits = [scan_start + off for off in range(0, len(stack) - 7, 8)
        if u64(stack[off:off + 8]) == return_site]
saved_rip = hits[0]
```

**Phase 4 — overwrite the saved return address.** Tcache entries must be 16-byte aligned, and a saved return address sits 8 bytes past a boundary, so the final poison targets `saved_rip - 8`. Pulling that fake entry from tcache clears its key field at `+8` (temporarily zeroing the saved RIP — harmless, we're still in the menu loop), and the follow-up edit writes 8 bytes of filler plus the ROP chain into the saved-RIP slot:

```python
rop_cell = poison(saved_rip - 8, 0x78, 10, 11, 12, 13)
chain = flat(ret, pop_rdi_ret, next(libc.search(b"/bin/sh\0")), libc.sym.system)
edit(rop_cell, (b"R" * 8 + chain).ljust(0x78, b"S"))
choose(6)   # main returns into the chain
```

No buffer smash, no canary touched — the return address is rewritten through the allocator. Choosing "Surface" returns `main` into `ret; pop rdi; "/bin/sh"; system` and pops a shell.

### Note on artifacts
The `rapture` binary, `libc.so.6`, `ld-linux-x86-64.so.2`, and the `core.*` dumps produced during development are intentionally not committed here. `solve.py` loads them from its own directory (place the handout alongside the script to reproduce).

### Running it

```bash
./solve.py            # local, uses the shipped loader + libc
./solve.py TEST       # repeatable self-check
./solve.py REMOTE SSL HOST=<host> PORT=1337
```

On the shell the flag lived at `/run/challenge/flag.txt`.

## Flag
`zdk{FREED_LN_The_de3P_BU7_n3VER_FOrgoT73N}`

## Key Takeaways
- A shallow pointer copy is not a backup. Duplicating a struct that owns a pointer, without duplicating the buffer, breaks ownership and hands you a UAF.
- A UAF read/write is enough on its own: unsorted-bin leak → libc, single-entry tcache read → defeat safe-linking, tcache poisoning → arbitrary allocation, `environ` → stack.
- Overwriting a saved return address through the allocator sidesteps the stack canary entirely.
- CET being *advertised* in `checksec` doesn't mean shadow-stack enforcement is active — test before assuming ROP is dead.
