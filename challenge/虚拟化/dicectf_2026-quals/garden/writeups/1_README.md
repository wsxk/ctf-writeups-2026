# pwn_garden

**Category:** Pwn | **Difficulty:** Hard | **Flag:** `dice{m1tig4ti0ns_nev3r_w0rk_y0u_escap3d_th3_w4ll3d_g4Rd3n}`

## Overview
A custom stack-based VM ("Garden VM") with a mark-compact garbage collector. The GC has a null-reference bug that corrupts object headers during compaction, leading to out-of-bounds access on both the managed heap and glibc heap.

## Solution

### Vulnerability: Null-Reference GC Corruption
The GC's `mark_reachable()` follows null references (ref=0) to address 0 of the managed heap (zeroed reserved area). This creates a fake "object" at offset 0 with `{length=0, mark_word=0}`. During compaction, `memmove` copies this 4-byte fake object first, corrupting the header of the first real object.

### Exploit Chain

**1. Cascading Memmove** — Set up a sacrificial array (SAC) with `entries[0]=0xFFFF`, a large array (BIG, 196 entries) with `entries[195]=0x00040005`, and an off-heap object (OH). After null-ref GC:
- SAC's header gets corrupted to `{0,0}` (length=0)
- SAC's entry `0xFFFF` cascades into BIG's header → BIG.length = 0xFFFF (OOB!)
- BIG's entry `0x00040005` cascades into OH's header → OH stays a valid off-heap object

**2. OOB Expansion** — Use BIG's OOB write to set OH.obj_size = 0x10000, giving 256KB of OOB access on the glibc heap via GET/SET_OFFHEAP_NUM.

**3. Libc Leak** — Create 70+ extra objects so the GC's internal `ctx.objs` allocation exceeds 0x410 bytes. When freed, it goes to the unsorted bin, leaving main_arena pointers near OH's data buffer. Read OH.data[40:41] for the leak.

**4. FSOP (House of Apple 2)** — Build a fake FILE structure in OH's data buffer on the glibc heap:
- Fake FILE with `_flags="$0\x00\x00"`, `_mode=1`, `vtable=_IO_wfile_jumps`
- Fake `_IO_wide_data` with `_IO_write_base=0`, `_IO_write_ptr=1`, `_IO_buf_base=0`
- Fake wide vtable with `__doallocate = system`
- Overwrite `_IO_list_all` to point to our fake FILE

**5. Trigger** — When the program exits, `_IO_flush_all` iterates the FILE list, hits our fake FILE, calls `_IO_wfile_overflow` → `_IO_wdoallocbuf` → `system("$0")` → shell.

### Stack Management
The VM only has DUP, SWAP, DROP, DUP_X1. A STORE OBJ array pattern was used to hold references (OH, BIG, computed values) and access them via GET_ELEM_OBJ/SET_ELEM_OBJ.

See `solve.py` for the full exploit code.

## Key Takeaways
- GC null-reference bugs can cascade through mark-compact compaction
- House of Apple 2: `_wide_data->_wide_vtable` is NOT validated by glibc's vtable check
- `system("$0")` is a neat trick — `$0` expands to the shell name when run via `system()`
- STORE array pattern enables complex operations with limited stack manipulation primitives
