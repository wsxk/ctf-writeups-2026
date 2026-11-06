# Batcave Bitflips

**Category:** Reversing | **Difficulty:** Medium | **Flag:** `UMASS{__p4tche5_0n_p4tche$__#}`

## TL;DR

A license-checker binary that's been "hit by cosmic rays" (intentional bitflips). The decryption routine has an `OR` where there should be an `XOR`, meaning the flag is simply `FLAG_data XOR EXPECTED_hash` — no hash reversal or license key brute-force needed.

## What We're Given

A single ELF binary: `batcave_license_checker`. The flavor text is doing some real work here:

> "Batman's AI agent deleted source code. Old debug version hit by cosmic rays (bitflips)."

That last sentence is the whole challenge. "Bitflips" isn't just a cool name — it's telling us the binary has been deliberately corrupted at the bit level. Our job is to figure out what got flipped and what that means for getting the flag.

## Initial Recon

Standard first moves: `file` and `checksec` to understand what we're dealing with.

```
$ file batcave_license_checker
batcave_license_checker: ELF 64-bit LSB executable, x86-64, dynamically linked, not stripped
```

Not stripped — nice. That means function names are intact, which makes reversing much friendlier. We load it up in Binary Ninja and start mapping out the program flow.

The binary is a license key verifier. Here's the general structure from `main`:

1. Reads 32 bytes from stdin (the license key)
2. Calls `hash(input, output)` — a custom hash function
3. Calls `verify(hash_output)` — does a `memcmp` against a hardcoded expected value
4. If it matches, calls `decrypt_flag(hash_output)` and prints the flag

There's also a static string at `0x404020`: `!_batman-robin-alfred_((67||67))` — that's the license key baked into the binary. The string data in `.data` looks like:

| Address | Contents | Purpose |
|---------|----------|---------|
| `0x404020` | `!_batman-robin-alfred_((67||67))` | LICENSE_KEY |
| `0x404040` | 32 bytes | EXPECTED hash output |
| `0x404060` | 32 bytes | encrypted FLAG |
| `0x404080` | 256 bytes | SBOX (substitution table) |

So the structure is clear: hash the license key, compare against `EXPECTED`, if they match use the hash to decrypt `FLAG` and print it. Now we just need to figure out how the bitflips break this.

## The Vulnerability / Trick

This is where it gets fun. The binary has multiple bitflips — intentional corruptions that break the program. Let's walk through them.

**Bitflip #1: The SBOX**

The substitution box at `0x404080` is a 256-byte lookup table that should be a valid permutation — every value from 0x00 to 0xFF exactly once. We checked it and found that value `0x43` appears *twice* (at indices 24 and 92) while `0x44` is completely missing. One bit difference between `0x43` and `0x44` — that's a single bit flip in the binary data.

**Bitflip #2: The rotate function**

The hash uses a rotate-left-by-3 on 8-bit values. The correct formula is:
```
(x << 3) | (x >> 5)
```
But the binary has:
```
(x << 3) | (x >> 6)
```
One bit flipped in the shift amount (5 vs 6), corrupting every rotation in the hash.

**Bitflip #3: The decrypt_flag function — the crucial one**

Here's the decompiled `decrypt_flag`:

```c
for (int i = 0; i < 32; i++) {
    FLAG[i] |= hash[i % 32];   // <-- OR instead of XOR
}
```

It's using bitwise OR (`|=`) where it should be using XOR (`^=`). These opcodes differ by exactly one bit in x86 encoding. This is the bitflip that matters most.

**The shortcut we spotted immediately:**

If `decrypt_flag` is *supposed* to do `FLAG[i] ^= hash[i]`, and the program only decrypts when `hash == EXPECTED`, then the correct decryption is just:

```
plaintext = FLAG ^ EXPECTED
```

We don't need to reverse the hash. We don't need to find the license key. We don't need to fix the binary. We just grab the two 32-byte arrays from the binary and XOR them together.

This works because XOR encryption is self-inverse: if `encrypted = plaintext XOR key`, then `plaintext = encrypted XOR key`. Here, `EXPECTED` is the key (the hash that would be produced by the correct license key), and `FLAG` is the ciphertext.

## Building the Exploit

Extract the two arrays from the binary using Binary Ninja (or `xxd` if you prefer the raw approach), then XOR them:

```python
# FLAG data at 0x404060 (32 bytes from the binary)
FLAG = bytes.fromhex(
    "6e1934497" "77df05a07" "b433a68ce" "6e617"
    "fbe96fae2" "ee526c370" "e3c47d277" "f2b00"
)

# EXPECTED hash at 0x404040 (32 bytes from the binary)
EXPECTED = bytes.fromhex(
    "3b54751a2" "406af0577" "8047c5e48" "3d348"
    "cb8730de1" "a9145ab15" "c79b22040" "22bee"
)

# XOR them together — that's all
flag = bytes(a ^ b for a, b in zip(FLAG, EXPECTED))
print(flag.decode('ascii'))
```

The key insight to understand here: Python's `zip` pairs up bytes from both sequences, then we XOR each pair with `a ^ b`. The `bytes(...)` constructor rebuilds it into a byte string, and `.decode('ascii')` turns it into readable text.

No brute force. No hash reversal. No patching the binary. Just XOR.

## Running It

```
$ python3 solve.py
UMASS{__p4tche5_0n_p4tche$__#}
```

One line, instant flag. The cosmic rays made Batman's license checker very un-secure.

## Key Takeaways

**The core technique:** When you see a "bitflip" challenge, the binary is intentionally broken. Map out every function and look for instructions that are *almost* right but slightly off — wrong shift amounts, OR vs XOR, off-by-one constants. The bug is usually one bit away from correct behavior.

**The clever shortcut:** Instead of fixing all the bitflips and reversing the hash, we reasoned backward from the goal. We asked: "what would the decryption do if it were *correct*, and what values would flow through it?" That led directly to `FLAG ^ EXPECTED = plaintext`.

**Pattern to remember:** Anytime a CTF binary XORs encrypted data against a hash value, and you can extract both the encrypted data and the expected hash from the binary, you can skip the whole hash computation. The expected hash *is* the key.

**Tools used:**
- Binary Ninja for static analysis and decompilation
- Python for the one-liner XOR

**The intended path** (which we skipped entirely) was probably: identify all three bitflips, patch the binary to fix them, figure out that `!_batman-robin-alfred_((67||67))` is the license key, run the fixed binary, get the flag. Our path took about 5 minutes. Respect to anyone who did it the hard way though — it's a clean challenge design.
