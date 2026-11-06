# Ehlel

**Category:** Rev | **Points:** 1000 | **Author:** flame | **Flag:** `HZ{0a662d79_h4j1m3_sh1n3_3hl3l_7b0f5d34}`

## Challenge Description

We are handed a packed, big-endian **MIPS** program that behaves like a peer in a
small peer-to-peer network. The binary embeds an identifier for a file but not
the file itself. Its job is to locate another peer, perform a key exchange, and
download that file over **uTP** (the UDP-based transport used by BitTorrent).

The handout is an encrypted ZIP (`challenge.zip`); the password is the classic
malware-sample password `infected`.

## Initial Analysis

Unpacking and identifying the ELF:

```bash
7z x -pinfected challenge.zip
file extracted/*.elf     # ELF 32-bit MSB executable, MIPS, MIPS-I, statically linked
```

"MSB" means **big-endian**, which matters because the protocol uses four-byte
integers — reading them in the wrong byte order produces nonsense.

The ELF was also **packed**: no useful section table, few strings, and an entry
point that led into a small decompression stub. Rather than reproduce the packer,
we let its own loader do the work under `qemu-mips` + `gdb-multiarch` and dumped
the unpacked image once the real entry point (`0x4002a0`, image around
`0x400000`) was reached:

```gdb
dump binary memory unpacked.mem 0x400000 0x47b000
```

The unpacked code closely resembled the **Hajime** IoT malware's peer-to-peer
module, with the dangerous stages stripped out. Useful embedded data:

```
dht.transmissionbt.com
[modules] / [peers]
aa2e0776b8d223d232e80cefd9a7f52e4eb5f7d0     <- per-team module ID
4ffe036a14a3dca45666dd4489a47825e418f1c309c79817a72cc2b0dc894220  <- owner Ed25519 key
```

## The Vulnerability / Core Concept

The point of the challenge is protocol reconstruction, not a memory bug. The
peer discovery uses Mainline DHT (BEP 5 `get_peers`) with the module ID as the
info hash, but the challenge's own instance is reachable directly on UDP port
1337 speaking uTP, so we can skip DHT once the wire format is understood.

Layered format:

```
module request  ->  encrypted record  ->  uTP packet  ->  UDP
```

- **Record format:** `4-byte big-endian body length | 1-byte type | body`.
  Types: `0` hello, `1` module data, `2` request module, `6` transfer length.
- **Handshake:** each side sends a type-0 hello containing an Ed25519 public
  key. Keys are converted Ed25519 -> Curve25519 and combined with X25519 /
  `crypto_box_beforenm` (NaCl) into a shared 32-byte secret.
- **Encryption:** two plain **RC4** streams keyed with the shared secret (one TX,
  one RX). No nonce, no MAC. RC4 encrypts the *entire* record stream, length and
  type fields included.
- **The uTP off-by-one (the real time sink):** the first client DATA packet must
  ACK the server's initial STATE sequence **minus one** — a STATE packet consumes
  no stream sequence number:

  ```python
  initial_ack = (server_state_sequence - 1) & 0xffff
  ```

## Exploitation

The clean Python client (`solve.py`) performs the uTP handshake, the
Ed25519->Curve25519 conversion, RC4 setup, sends a type-2 request for the module
ID (NUL-terminated, since MIPS treats it as a C string), and parses the reply:

```python
request = record(2, b"aa2e0776b8d223d232e80cefd9a7f52e4eb5f7d0\0")
encrypted_request = tx.crypt(request)
```

The decrypted 54-byte response was two records: a type-6 (`0x28` = 40, the
transfer length) followed by a 40-byte type-1 chunk that decoded straight to the
flag.

```bash
python3 -u solve.py <HOST> 1337   # host/port from the challenge platform
```

## Flag

```
HZ{0a662d79_h4j1m3_sh1n3_3hl3l_7b0f5d34}
```

## Key Takeaways

- Separate the layers instead of solving everything at once: let the packer
  unpack itself, recover the protocol statically, test the plaintext hello
  before adding crypto, then decrypt the record stream.
- Use a real crypto library (PyNaCl) for the Ed25519->Curve25519 conversion
  rather than reimplementing it.
- The hardest bug was not the MIPS code or the cryptography — it was a single
  off-by-one in the uTP acknowledgement. Compare questionable transport behavior
  against a known-good implementation (`libutp`).
