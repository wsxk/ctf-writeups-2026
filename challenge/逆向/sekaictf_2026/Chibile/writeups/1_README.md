# Chibile

**Category:** rev | **Author:** ELJoOker | **Difficulty:** Hard | **Flag:** `SEKAI{Th4nk5_F0R_Pl4y1ng_My_Chibi_G4m3__5t4y_tun3d_f0r_my_n3xt_0n3}`

## Challenge Description

Official challenge text was not recorded. The attachment is a small anime quiz/game shipped with a fake anti-cheat stack. Files provided:

```
Chibile_Launcher.exe    # launcher
chibile.exe             # the raylib game / client (contains crypto + protocol)
eac_nocrt.dll           # user-mode "anti-cheat" DLL (packed) -> UM attestation
eac_shield.sys          # "kernel driver" -> KM attestation
raylib.dll              # game engine
PROTOCOL.md             # crib for how the two final secrets are decoded
```

`PROTOCOL.md` (included here) is a large hint: it documents how two 12-character secrets are derived from a baked half-key `BK`, and the `lh_*` / `c_*` values returned by the server.

## Initial Analysis

`strings` on the three binaries surfaces the whole flow:

```
CHIBILE-GATE-V1
SECRET ROOM UNLOCKED
AC HANDSHAKE FAILED
CONNECTING TO SERVER...
ACCESS GRANTED / ACCESS DENIED
secret-room
CHIBILE-R3-20260615
```

So the game has a hidden `secret-room` gate, an anti-cheat handshake, and then a networked two-phase protocol. The solve breaks into three independent reversing tasks:

1. Recover the hidden **secret-room phrase** from `chibile.exe`.
2. Produce valid **user-mode + kernel-mode attestations** so the server completes Phase 1.
3. Decode the two 12-char codes from the Phase-1 response (per `PROTOCOL.md`) and submit them in Phase 2 to receive a flag PNG.

Rather than run a Windows kernel driver or fight the packer statically, almost everything is done with **Unicorn emulation** of individual functions and small **Wine harnesses**.

## Vulnerability / Core Concept

There is no single bug — it is a layered emulation/crypto-reconstruction exercise:

- **Packed UM DLL, trivially unpacked.** `eac_nocrt.dll`'s entry stub decrypts itself with a fixed XOR (`^0x23` over the entry payload) plus a rolling ARX region decryptor. `unpack_eac.py` reproduces the loop and dumps `eac_nocrt_fullunpacked.dll`. The real attestation logic is exported by **ordinal 1**.
- **Runtime-decoded C2 host.** The server hostname is not a plain string in `chibile.exe`; it is produced by a small in-binary decoder. `decode_host.py` emulates that function (RVA `0x39d0`, seeded with the baked stack constant `0x3151c0de`) to recover it.
- **Custom packet wrapper.** Packets are `CBL2 | nonce | RSA-OAEP(k1|k2|k3|nonce) | iv | AES-CBC(xor_stream(json))`, HMAC'd with `k2`. The RSA public key is embedded at RVA `0x11190`. Reimplementing this in `proto_client.py` lets us talk to the server without the GUI.
- **KM attestation = keyed hash, emulated not loaded.** `eac_shield.sys` computes the KM attestation by hashing `CHIBILE-GATE-V1 || UM || "KM-ATTEST" || nonce` plus baked driver data. `emulate_km.py` runs that dispatch function under Unicorn (stubbing the few kernel imports) instead of loading a driver.
- **Secret derivation is a documented HMAC/rotate scheme.** From `PROTOCOL.md`, the two secrets come from `BK` (a 32-byte half-key baked in each binary), `LH = lh_*`, `C = c_*`:

  ```
  DK    = HMAC-SHA256(BK, LH)
  KS(b) = HMAC-SHA256(DK, tag || u32le(b))    ; tag = "UM-KS" | "KM-KS"
  user   : S[i] = rotl8(C[i] ^ KS(b)[j], 3) ^ BK[j]
  kernel : S[i] = rotr8(C[i] ^ DK[(i*7) % 32], 3) ^ KS(b)[j]
  ```

  The only unknown is which 32 bytes in each file are `BK`. Because the output must be 12 chars over `ABCDEFGHJKLMNPQRSTUVWXYZ23456789`, a sliding-window scan over the baked-data blocks finds exactly one clean-decoding candidate per file.

## Exploitation / Solving Process

**Secret-room phrase (`emulate_chibile.py`).** The check lives near `0x140008960`. It builds a 73-byte keystream and compares `expected[i] = ((i*0x17 - 0x5d) & 0xff) ^ stream[i] ^ key`. Emulating the relevant `chibile.exe` functions (stubbing `memcpy`/`memset`/`memcmp`) yields the keystream and reconstructs the phrase:

```
CONGRATS, YOU FOUND SOMETHING! TWEET AT @0XN*** AND MENTION THIS MESSAGE.
```

**UM attestation (`unpack_eac.py` -> `um_calc.exe`).** After unpacking, a tiny Wine harness (`um_calc.c`) loads the DLL, resolves ordinal 1, calls the init case, then command `10` with `(digest, nonce, out)` to emit the 32-byte UM attestation for a given nonce. `um_harness.c` / `harness.c` / `harness2.c` are the exploratory versions used to find the right command/argument layout.

**KM attestation (`emulate_km.py`).** Maps `eac_shield.sys`, stubs the imports (`IoGetCurrentProcess`, etc.), seeds the input buffer with `UM || nonce`, and runs the dispatch routine at RVA `0x2b00`. The first 32 output bytes are the KM attestation.

**Phase 1 (`solve_phase1.py` + `proto_client.py`).** Generate a random nonce, compute UM via `um_calc.exe`, KM via `emulate_km.py`, build the Phase-1 JSON, and send through the reimplemented crypto wrapper. Example response:

```json
{
  "sid": "f8c9a9e0f810d314597a835cb20a4777",
  "c_um": "7e2b107e240a0128e41871ee",
  "lh_um": "6e8c737ca5f1ec16b8f506db65160fa413a151f331be7436944b04d4cb8cdb29",
  "c_km": "c754ec4cafac05c226f9918a",
  "lh_km": "e62e048cc57f35a86be2bf4af384df8137ebbd2a9a21d679e9b3b3e81218a4f9"
}
```

**Decode UM/KM codes (`brute_segments.py`).** Implements the `PROTOCOL.md` `user`/`kern` transforms and scans the baked-data windows of `eac_nocrt.dll` and `eac_shield.sys` for the `BK` that decodes cleanly into the alphabet:

```python
def user(BK, LH, C):
    DK = hmac.new(BK, LH, hashlib.sha256).digest()
    return bytes(rotl8(c ^ hmac.new(DK, b'UM-KS'+(i//32).to_bytes(4,'little'), hashlib.sha256).digest()[i%32], 3) ^ BK[i%32]
                 for i, c in enumerate(C))
```

Recovered codes:

```
UM: PHAUSQ9HKRU9
KM: HQRFLP9L7XWA
```

**Phase 2 (`phase2.py`).** Reuse the `sid` from Phase 1, submit `typed_um` / `typed_km`, and the server returns a `CBF2`-framed PNG. The flag is rendered diagonally across the image (`flagtext_8.png`, included as evidence).

## Flag

```
SEKAI{Th4nk5_F0R_Pl4y1ng_My_Chibi_G4m3__5t4y_tun3d_f0r_my_n3xt_0n3}
```

Watch the leet substitutions: `F0R` / `f0r` / `0n3` use zeros, `Pl4y1ng` uses a `1`.

## Key Takeaways

- **Emulate functions, don't run the stack.** A user-mode DLL, a kernel `.sys`, and in-binary decoders were all reduced to single-function Unicorn runs (or one small Wine harness) instead of loading a real driver or fighting the packer.
- **A leaked protocol spec collapses the crypto.** `PROTOCOL.md` turned the final step into a 32-byte `BK` search with a printable-alphabet oracle — trivially brute-forced.
- **Attestations gate the network, not the flag.** The hard part was making Phase 1 accept our UM/KM values; once valid, the flag derivation was mechanical.
- Reconstructing the packet wrapper (`RSA-OAEP + AES-CBC + HMAC + keystream`) from the client lets you script the whole exchange headlessly.

## Files

- `PROTOCOL.md` — challenge-provided crib for the secret-derivation scheme.
- `decode_host.py` — Unicorn emulation of the in-binary hostname decoder.
- `unpack_eac.py` — reproduces the DLL self-decryptor, dumps `eac_nocrt_fullunpacked.dll`.
- `emulate_chibile.py` — recovers the secret-room phrase from `chibile.exe`.
- `um_calc.c` — Wine harness that calls DLL ordinal 1 to produce the UM attestation.
- `um_harness.c`, `harness.c`, `harness2.c` — exploratory DLL harnesses (command/arg discovery).
- `emulate_km.py` — emulates the KM attestation routine in `eac_shield.sys`.
- `proto_client.py` — reimplemented packet wrapper (host redacted).
- `solve_phase1.py` — drives UM+KM generation and sends Phase 1.
- `brute_segments.py` — `BK` search / secret decoder per `PROTOCOL.md`.
- `phase2.py` — submits the recovered codes, saves the flag PNG.
- `flagtext_8.png` — server-returned flag image (evidence).
