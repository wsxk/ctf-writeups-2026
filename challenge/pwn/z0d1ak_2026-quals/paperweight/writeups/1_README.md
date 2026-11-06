# paperweight

**Category:** Pwn | **Points:** 436 | **Author:** afish | **Flag:** `zdk{THe_ScAN1iNE_s4NK_beL0W_e2_bIT5}`

## Description
> Every record sent to the Pelagic Archive sinks into cold storage. Its new chart plotter is rated for any pressure. Send a logbook below crush depth and recover what the tide brings back.

The flavor text maps cleanly onto the mechanics: the "logbook" is the PDF you upload, the "chart plotter" is the renderer, "below crush depth" means overflow it, and "recover what the tide brings back" is the read-back channel that leaks your crafted bytes.

Endpoint: `ncat --ssl paperweight-49d24fe5de11.chals.z0d1ak.org 1337` (TCP + TLS).

## TL;DR
The service renders attacker-supplied PDFs with the **poppler** library. A PDF **tiling pattern** containing an inline image with a pathological transformation matrix makes poppler allocate a bitmap far smaller than the number of bytes it then writes into it — a fully-controlled heap overflow. From there it's a textbook modern-libc pwn: turn the read-back command into a relative read to leak PIE and libc, hijack a C++ vtable, and pivot with `setcontext` into an `openat`/`read`/`write` ROP chain that reads the flag.

## Initial Analysis

The tarball ships a full runtime: the `chal` binary (PIE, stripped), the exact `libc.so.6` + `ld-linux-x86-64.so.2`, `libpoppler.so.156`, and a pile of its dependencies (`libfreetype`, `libfontconfig`, `libpng`, `libexpat`, `libz`, `libstdc++`, …). When a pwn challenge ships a huge real-world library, that library *is* the attack surface — the bug lives in poppler's PDF rendering, not in a toy parser.

`file` / `checksec` on `chal`:

```
ELF 64-bit PIE executable, x86-64, dynamically linked, stripped
RELRO: Full · Canary: Yes · NX: Yes · PIE: Yes · FORTIFY: Yes · SHSTK/IBT: Yes
RUNPATH: /opt/poppler/lib
```

Every mitigation is on — including CET (shadow stack / indirect-branch tracking). So the endgame can't be a GOT overwrite or a naive stack smash; it has to be a data-only corruption ending in a clean stack pivot.

Strings spell out the whole protocol in the author's nautical vocabulary:

```
dive ready
new dive
logbook recovered
plotter resurfaced
jettisoned
waterlogged logbook
*N12_GLOBAL__N_110DiveAnchorE     <-- a C++ class "DiveAnchor" in an anonymous namespace
PELAGIC-LEDGER
```

That `DiveAnchor` symbol is the key: it's a heap object allocated per dive that ends up sitting right next to the bitmap we overflow, so it becomes our leak source.

### The protocol

The service is a small single-letter command loop:

- `A <u32 len>` — allocate a scratch chunk, returns a 1-byte index
- `N` — start a **new dive** (allocates the `DiveAnchor` object, prints `logbook recovered`)
- `F <idx>` — free a scratch chunk (prints `jettisoned`)
- `P <u32 len> <bytes>` — submit a **PDF**; poppler renders it into a bitmap (prints `plotter resurfaced`)
- `S` — dump the rendered bitmap back to you (the read primitive)
- `T` — "surface"; triggers the final action that calls through the object (our control-flow hijack)

So `A`/`F` shape the heap, `P` drops a rendered image into a chunk, and `S` reads it back — a read/write primitive built out of PDF rendering.

## Vulnerability / Core Concept

### Under-allocated bitmap → heap overflow

PDF **tiling patterns** let you define a small cell (a "tile") that poppler repeatedly paints to fill a region. Inside a tile you can embed an **inline image** (`BI … ID … EI`) with an arbitrary color space, bit depth, and — crucially — an arbitrary **transformation matrix** (`cm`).

The catch: the buffer poppler reserves for a tile's output bitmap is computed from the *destination* geometry (how big the tile is on the page), but the number of source bytes it iterates over comes from the image's declared `/W`idth and `/H`eight. Make those two disagree and poppler writes more bytes than it reserved. That's the overflow.

The exploit uses a deliberately insane CTM (see `pdf_for()` in `solve.py`):

```
q 81.996651785714 0 0 4194304 -81.996651785714 0 cm
BI /W 10496 /H 1 /BPC 8 /CS /DeviceGray /F /ASCIIHexDecode ID
<hex pixels...> > EI Q
```

- The `x` scale is **negative** (`-81.99…`), so the image is sampled **backwards** — that's why the payload stores its row reversed (`pixels[::-1]`).
- The `y` scale is a huge `4194304` (2²²) to cancel a tiny 2⁻²² factor baked into poppler's coordinate math, so a `/H 1` image (one row) stretches across the whole tile.
- The fractional `81.996651785714` is a sub-pixel fudge so that after rounding, the destination row width lands *exactly* on `0x2900` (10496) bytes and every source byte maps one-to-one onto a destination byte.

Net effect: the bitmap chunk is only ~0x200 bytes, but we write a fully-controlled `0x2900`-byte "row" starting at its base and spilling into the heap objects that follow. `/ASCIIHexDecode` lets us embed raw arbitrary bytes (including NULs) as hex.

### Heap grooming

Before dropping the PDF, `start_dive()` sprays allocations and frees to line up tcache:

```python
for _ in range(8):
    io.send(b'A' + p32(0x200)); idx.append(io.recvn(1))
io.send(b'A' + p32(0x1000)); io.recvn(1)   # barrier so the 0x1000 sits between
io.send(b'N')                              # new dive -> allocates DiveAnchor et al.
for i in idx:
    io.send(b'F' + i)                      # free the eight 0x200s
```

Seven freed chunks fill `tcache[0x210]`; the eighth spills into the unsorted bin. After poppler does its own seven allocations while parsing the PDF, the under-sized 0x200-byte bitmap lands right after the `DiveAnchor` object — so the controlled row overlaps it. The bitmap's internal length/offset fields (the "Folio" slice in the solve, at displacement `FOLIO_FROM_DST = 0x1c70`) sit at a known offset; overwriting them turns the read-back (`S`) into an **arbitrary relative read**.

## Exploitation

Each dive gives one controlled overwrite plus one read-back, so the exploit chains three of them. The full script is `solve.py`.

**Dive 1 — leak PIE + heap.** Point the Folio slice at the neighboring `DiveAnchor`, read back its C++ vtable pointer and its own address. `vtable − 0x5c10` ⇒ PIE base; the self-pointer ⇒ heap base (and the exact address of our bitmap/Folio).

```python
anchor_vtable = u64(leak1[0x20:0x28]); anchor = u64(leak1[0x28:0x30])
pie = anchor_vtable - 0x5c10
dst = anchor - ANCHOR_FROM_DST            # our bitmap base
```

**Dive 2 — leak libc.** With the binary base and our own heap address known, aim the relative read at the executable's GOT and read `write@GOT`. Full RELRO makes the GOT read-only, but reading it is fine.

```python
got = pie + 0x5e80
corrupt(io, folio_row(got - folio)); io.send(b'S'); leak2 = io.recvn(0x100)
libc.address = u64(leak2[0x40:0x48]) - libc.sym.write
```

**Dive 3 — code execution.** Overwrite the object's vtable pointer with a fake vtable placed inside our own controlled buffer. The `T` command then calls a virtual method → we route it to `setcontext`.

**setcontext → ROP.** With NX + CET on, the classic move is the `setcontext` pivot: point a fake vtable entry at libc's `setcontext(+0x20 style)` and craft a fake `ucontext` in the controlled heap buffer whose saved `RSP`/`RIP` land on a ROP chain planted in the same buffer. Don't forget a valid `MXCSR` (`0x1f80`) at `ucontext+0x1c0`, or `setcontext` faults restoring FPU state.

The ROP chain is a straightforward `openat`/`read`/`write`:

```
openat(AT_FDCWD, "flag.txt", 0)     # -> fd 3
read(3, outbuf, 0x100)
write(1, outbuf, 0x100)             # flag comes back over the socket
_exit(0)
```

`AT_FDCWD` is `-100`; the path string, ROP chain, and fake ucontext all live at fixed offsets inside the same overflowed row, addressed via the heap base leaked in Dive 1.

### Running it

Because the challenge ships the exact `libc`/`ld`, offsets computed locally transfer straight to remote — the only change needed was the connection line (`remote(..., ssl=True)`):

```
$ REMOTE=1 python3 solve.py
[+] PIE    = 0x7ff1734c3000
[+] heap   = 0x55558ae01620 (folio 0x55558ae03290)
[*] Loaded 218 cached gadgets for './libc.so.6'
zdk{THe_ScAN1iNE_s4NK_beL0W_e2_bIT5}
```

First try on remote; the flag was simply `flag.txt` relative to the working directory.

### Files

- `solve.py` — full three-dive exploit.
- `genpdf.py` — minimal PDF/tiling-pattern generator used while probing the primitive.
- `inspect_pdf.py` — GDB harness that renders one crafted PDF and dumps the source row / heap around the overflow (how the offsets like `FOLIO_FROM_DST` were pinned down).
- Not included (reference only): the `chal` binary, `libc.so.6`, `ld-linux-x86-64.so.2`, `libpoppler.so.156` and its dependency `.so` files, and the crafted `*.pdf` artifacts (they are regenerated by `solve.py`).

## Flag
`zdk{THe_ScAN1iNE_s4NK_beL0W_e2_bIT5}`

(The flavor: "the **scanline** sank below its bits" — a nod to the image scanline whose byte count no longer matched its allocation.)

## Key Takeaways
- **When a pwn ships a big library, the library is the bug.** poppler is a real-world PDF renderer; the vuln is in how it sizes image buffers.
- **Tiling patterns + inline images + a hostile CTM** let you control allocation size (destination geometry) and written content (source `/W`/`/H`) *independently* — the exact recipe for a heap overflow with a chosen payload. The fractional scale factors defeat rounding so bytes map one-for-one.
- With every mitigation on (incl. CET), the endgame is the standard 2024-era libc pwn: relative-read leak, C++ vtable hijack, and **`setcontext` as a universal stack pivot** into an `openat`/`read`/`write` chain. Set a sane `MXCSR` or `setcontext` faults.
- **Read-back channels are leak channels.** Any feature that echoes processed data back (here, `S`) upgrades a relative-read bug into a free info leak.
- **Shipping the exact libc/ld is a gift** — develop offline against `./ld-linux --library-path . ./chal`, then flip one line to `remote(..., ssl=True)`.
