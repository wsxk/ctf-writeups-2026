# pekpek-stadium-64

**Category:** Reversing | **Author:** n1cogum | **Flag:** `zdk{httPS://YOuTu.8E/tS2HZ5jwSJw?si=nnTOse6QlJEcB0u_}`

## Description
> A dumped Nintendo 64 cartridge (`pekpek.v64`). Reverse the cart and recover the real flag.

## TL;DR
The N64 ROM contains an embedded GBA program with a convincing plaintext flag — a **decoy**. The real flag is encrypted inside the N64 executable using a chain of CRC32 calculations as keystream. The 16-byte key never actually matters: everything depends only on the key's 32-bit CRC state, which we recover from the known `zdk{` prefix plus a stored integrity CRC.

> Note: the flag is a YouTube link. Given the amount of trolling in the ROM, expecting a rickroll is entirely reasonable — the URL is the real intended flag.

## Initial Analysis

**Fix the byte order first.** The dump starts with the `.v64` magic `37 80 40 12` (byte-swapped). Swap every pair of bytes to get canonical `.z64` order beginning `80 37 12 40`; the header then reads title `PEKPEK64`.

`binwalk` on the normalized ROM finds an **ELF at `0x1D00`** (32-bit MSB MIPS-III) plus a small filesystem table near `0x18D0` naming `pekpek.elf.stripped` and `pekpek.elf.sym`. The `.sym` file (`SYMT` Libdragon symbol table) leaks the interesting routine names:

```
pekfs_crc32   pekfs_decode_offsets   unlock_cart_memory   sneswop_keystream   locker_ok
```

Those are far more interesting than the visible stadium minigame. Farther in, at `0x6B510`, is a **MIO0** compressed stream.

## The decoy

Decompressing the MIO0 stream yields a ~3.8 KB GBA program (header `PEKPEKKIOSK`) that includes a flag-shaped string:

```
zdk{w0mb0_c0mb0_7h47_41n7_f41c0}
```

It references the "Wombo Combo" clip and looks perfectly plausible — and it's wrong. The GBA program just draws a "TRANSFER PAK KIOSK" screen and loops on sound registers. Pure distraction from the N64-side locker.

## Vulnerability / Core Concept

The real routine is `unlock_cart_memory`:

1. Takes a 16-byte input, computes `C = CRC32(key)`.
2. Uses repeated CRC32 to produce 96 bytes of keystream.
3. XORs that keystream with a 96-byte encrypted locker at ROM offset `0x3460C`.
4. Reads a big-endian length from the first two decrypted bytes, then verifies a trailing CRC.

Because CRC32 can be continued from an existing CRC state, the whole keystream depends **only on `C`**, not the full 16-byte key:

```
S0 = C
Si = CRC32(BE32(S_{i-1}), init=C)   # each Si appended big-endian
```

So the effective secret is one 32-bit state, not 128 key bits. We know: the first two decrypted bytes are a length (1..90), the payload starts with `zdk{`, and a CRC after the payload must validate. That gives enough known keystream to constrain the first CRC words. Modeling the CRC update as 32-bit bit-vectors in Z3 and testing candidates against the trailing CRC leaves exactly one surviving state:

```
C = 0xAE00628B
```

## Exploitation

With `C` known, generate the keystream, XOR, parse `length || payload || CRC`, and validate (`solve.py`):

```python
state = 0xAE00628B
keystream = bytearray()
while len(keystream) < 96:
    state = zlib.crc32(struct.pack(">I", state), 0xAE00628B)
    keystream += struct.pack(">I", state)
plain   = bytes(a ^ b for a, b in zip(ciphertext, keystream))
size    = struct.unpack(">H", plain[:2])[0]
payload = plain[2:2+size]
assert zlib.crc32(payload, 0xAE00628B) == struct.unpack(">I", plain[2+size:6+size])[0]
```

```
$ python3 solve.py pekpek.v64
zdk{httPS://YOuTu.8E/tS2HZ5jwSJw?si=nnTOse6QlJEcB0u_}
```

`solve.py` accepts either the original `.v64` or a converted `.z64` (it normalizes byte order automatically).

> Excluded from this directory: `pekpek.v64` / `pekpek.z64` (~430 KB N64 ROMs), the extracted `embedded.elf`, `code.bin`, and the decompressed GBA `mio0_6b510.bin`. Only `solve.py` is included.

## Flag
`zdk{httPS://YOuTu.8E/tS2HZ5jwSJw?si=nnTOse6QlJEcB0u_}`

## Key Takeaways
- **N64 ROM byte order matters** — fixing `.v64` swapping makes every later step easier.
- **A flag-looking string is not automatically the flag**, especially when it sits in a suspiciously convenient second executable.
- **Leaked symbols** turn a big static binary into a short list of routines worth reversing.
- **CRC32 is an integrity check, not a KDF.** If a construction uses an unknown message only through its CRC state, the effective secret can be just 32 bits — recoverable with known plaintext and a second CRC.
