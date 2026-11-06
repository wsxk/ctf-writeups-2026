# Ouroboros

**Category:** Reverse · **Points:** 130 (dynamic scoring, mid-event snapshot) · **Solves:** 150 · **Flag:** `KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}`

## Challenge

We're handed a single binary, `chronos`, with the flavor text "We made a small program here. The developer left a lot of Easter eggs." That last sentence turns out to be a very literal warning — this thing is packed with decoys.

## Initial Analysis

`chronos` is a stripped universal (fat) Mach-O containing both an x86-64 and an arm64 slice. Running `strings` on it is tempting, and it even pays off... with the wrong answer. The binary contains a plaintext-looking flag, `KubSTU{m4ch0_s3ct10ns_t3ll_st0r13s}`, sitting right there as a Base64-decodable Easter egg, plus a couple more plaintext decoys scattered around. None of them are the real flag — they're bait for anyone who stops at the first `strings` hit.

The real logic lives in two custom sections, `__DATA.__d3` and `__DATA.__d5`, which are both encrypted blobs rather than readable data.

## Core Idea

The name "Ouroboros" is the big hint: the binary is keyed by itself — specifically by its own `__text` (code) section. This is a self-referential/self-verifying scheme, multiple layers deep:

1. **`__d3` is LCG-encrypted bytecode for a tiny stack VM.** The keystream comes from a linear congruential generator seeded with `0x1337beef` (`state = state * 0x41c64e6d + 0x3039 mod 2^32`, keystream byte = `state >> 16`). Decrypting it reveals bytecode for a verifier VM.
2. **The VM bytecode encodes an activation-key check.** Each input byte is transformed through a chain of rotate/add/XOR operations (keyed by a per-round rotation amount and a 32-byte constant table baked into the last 48 bytes of the program), and compared against 16 expected output bytes. Inverting that chain byte-by-byte recovers the activation key: `KUBSTU-CHR0N0S26`.
3. **The program hashes its own `__text` section** (SHA-256) and builds a 57-byte key preimage: `activation_key || SHA256(__text) || 0x00 || "chr0n0s!"`. SHA-256 of *that* is the real ChaCha20 key — i.e. the binary's own code is a load-bearing ingredient in its own decryption key. That's the "keyed by its own text section" the flag refers to.
4. **`__d5` is the ChaCha20-encrypted flag payload**, framed as `"CHR0N0S\x01"` header + 12-byte nonce + 39-byte length + ciphertext at offset 32. ChaCha20 with counter 0 and the derived key decrypts straight to the flag.

Because each architecture slice hashes a *different* `__text` section, the two slices use different nonces, ciphertexts, and derived keys entirely — but both independently decrypt to the identical flag, confirming the result.

## Solving It

`solve.py` walks the whole chain end-to-end, directly against the `chronos` binary:

1. Parse the fat Mach-O header and pull out `__text`, `__d3`, and `__d5` for each architecture slice (`macho_sections`).
2. Run the LCG keystream over `__d3` to recover the verifier VM bytecode (`decrypt_vm`).
3. Locate the 16 `ROL` opcodes in the bytecode to recover the per-round rotation amounts, then brute-force each activation-key byte (0-255) against the chained rotate/add/XOR transform until it matches the expected output table (`recover_activation_key`).
4. Build the 57-byte key preimage from the activation key and the SHA-256 of `__text`, hash it, and use the result as a ChaCha20 key (implemented from scratch with the standard quarter-round function) to decrypt `__d5` (`decrypt_payload`).
5. Confirm both architecture slices agree on the same flag before printing it.

```
python3 solve.py
```

## Flag

`KubSTU{k3y3d_by_1ts_0wn___t3xt_s3ct10n}`

## Key Takeaways

- Never trust the first `strings` hit in a reversing challenge — this binary deliberately plants multiple plausible-looking decoy flags, including a Base64-encoded one.
- A program can use its own code bytes as key material. Hashing `__text` and folding that hash into a derived key means you can't decrypt the payload without the exact, byte-for-byte binary — a neat "self-keying" trick worth recognizing.
- Fat/universal Mach-O binaries can carry divergent per-architecture secrets (different nonces/ciphertexts) that still resolve to the same plaintext — useful as a built-in sanity check when solving.
- Small embedded bytecode VMs are common obfuscation for key checks; finding the opcode pattern (here, `ROL` markers) is often enough to invert the transform without fully emulating the VM.
