# RISC-V.

**Category:** Reverse · **Points:** 127 (dynamic scoring, mid-event snapshot) · **Solves:** 155 · **Flag:** `KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}`

## Challenge

Just one attachment: `fw.bin`, 16.22 KiB. The description is a one-line nudge: "Reduced Instruction Set Computing. Remember the lectures on computer hardware." — i.e. this is bare-metal RISC-V firmware, no OS, no ELF, go read it like hardware.

## Initial Analysis

`fw.bin` doesn't start with an ELF header — it opens with a small raw RV32IM boot stub. That stub:

1. Hashes its own bytes at offsets `0x00..0xdb` (FNV-style: XOR each little-endian word into a running state seeded at `0x811c9dc5`, multiply by `0x01000193`, rotate left 13), ending at state `0xd1b83785`.
2. Feeds that state into an xorshift32 PRNG.
3. Uses the xorshift stream to XOR-decrypt 0x4000 bytes starting at file offset `0xe0`, and "loads" the result at address `0x80100000`.

Decrypting that gives a second raw RV32 image containing readable UART strings and the actual challenge logic — so the real target is self-decrypting firmware, two layers deep.

## Core Idea

The flag text (`tr4ps_4r3_th3_r34l_c0ntr0l_fl0w`) says it plainly: control flow here isn't normal function calls, it's driven by **illegal-instruction traps**. The second-stage firmware installs a trap handler, and `main` doesn't call functions directly — it executes four bogus/custom 32-bit words that are *not* valid RV32 instructions:

```
0x0000007f
0x0010007f
0x0020007f
0x0030007f
```

Each one deliberately triggers an illegal-instruction exception. The trap handler pulls bits 20-and-above out of the faulting word as a dispatch index, stashes a continuation address, overwrites the saved `ra`, and returns straight into the selected routine — a hand-rolled "trap-as-call-instruction" calling convention. A fifth custom word, `0x0000107f`, works as the matching "return" op. The four dispatch targets are:

```
0 -> 0x80100454  print bootstrap message
1 -> 0x80100138  build an RC4 S-box + 64-byte key stream
2 -> 0x80100248  transform the submitted 16-byte key (Feistel network)
3 -> 0x801005c0  compare the result and, on success, decrypt the flag
```

So the actual logic (key check + flag decryption) only runs if you understand that traps *are* the function-call ABI here.

## Solving It

Everything is reproduced statically in `solve.py`, no emulator needed:

1. `decrypt_second_stage` recomputes the boot stub's FNV-ish hash, seeds xorshift32, and XOR-decrypts the 0x4000-byte second-stage image directly from `fw.bin`.
2. Routine 1's dispatch key is read straight out of the decrypted image at offset `0x874`: the literal string `tr4p_d1sp4tch_v1`. That's used for a standard RC4 KSA + keystream (`rc4_setup` / `rc4_keystream`) to generate the 64-byte stream the Feistel rounds consume.
3. Routine 2 splits the 16-byte access key into two 8-byte halves and runs 8 Feistel rounds, where each round function is `S[(round_key[i] + right[i]) & 0xff] XOR ROL8(right[(i+1) & 7], i+1)`. The expected post-transform block is stored in the firmware; `decrypt_feistel` inverts the 8 rounds to recover the original access key, and `encrypt_feistel` re-runs it forward as a sanity check — both must agree with the firmware's expected block.
4. That recovers the access key: `RV32-TR4P-G4T3S!`
5. While processing the key, four 32-bit hash-like states evolve round by round. Their final values (`ba84109d bfd2b184 755d3cb9 bd89b8c2`) are concatenated little-endian into a 16-byte key, which is fed into RC4 one more time to decrypt 39 ciphertext bytes sitting at second-stage offset `0x884` — producing the actual flag.

```
python3 solve.py
```

Expected output: the access key, followed by the flag, both verified against the firmware's expected values along the way.

## Flag

`KubSTU{tr4ps_4r3_th3_r34l_c0ntr0l_fl0w}`

## Key Takeaways

- Bare-metal/firmware binaries often don't look like normal executables at all — no ELF header, just raw code mapped at a fixed load address. `file`/`strings`/entropy checks (and noticing the image decrypts into more code) are the way in.
- Self-decrypting firmware is common in embedded CTF challenges: the "payload" is encrypted with a key derived from hashing the loader's own bytes, so you have to replicate the loader's math exactly before you can even see the real program.
- Illegal-instruction traps can be (ab)used as a custom calling convention — the trap handler becomes a dispatcher keyed on bits embedded in the "undefined" instruction word. Recognizing that pattern is the key unlock for this challenge's "real control flow."
- RC4 and Feistel networks built from scratch (not a library call) show up a lot in homebrew firmware crypto — reversing the round function by hand and inverting it is usually faster than trying to brute force it.
