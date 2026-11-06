# LACTF-1986 Writeup

**Category:** Reverse Engineering
**Points:** 241
**Solves:** 54

> Dug around the archives and found a floppy disk containing a long-forgotten LA CTF challenge. Perhaps you may be the first to solve it in decades.

## First Look

We're given a file called `CHALL.IMG` - a floppy disk image. How retro! The challenge name "LACTF-1986" hints at something old-school, and sure enough, this is a DOS-era challenge.

```bash
$ file CHALL.IMG
CHALL.IMG: DOS/MBR boot sector, OEM-ID "IPRT 6.2", FAT (12 bit)
```

Let's extract what's on this floppy:

```bash
$ 7z x CHALL.IMG -oextracted
$ ls extracted/
CHALL.EXE
```

A DOS executable from 1986! (Well, pretending to be from 1986.) Let's see what strings it contains:

```bash
$ strings CHALL.EXE
...
UCLA NetSec presents: LACTF '86 Flag Checker
Check your Flag:
Sorry, the flag must begin with "lactf{..."
Sorry, that's not the flag.
Indeed, that's the flag!
0123456789abcdefghijklmnopqrstuvwxyz
...
```

So it's a flag checker - we need to figure out what input makes it print "Indeed, that's the flag!"

## Understanding the Algorithm

Since this is a 16-bit DOS executable, modern tools like IDA or Ghidra can be finicky with it. I ended up analyzing it manually by looking at the hex dump and decoding the x86 instructions.

After much squinting at bytes, I figured out the program does three things:

### 1. Check the Prefix
First, it verifies the input starts with `lactf{`. Pretty standard.

### 2. Hash the Input
It computes a custom hash of the entire flag using this formula:
```
hash = 0
for each character c:
    hash = (hash * 67 + c) mod 2^20
```

This gives a 20-bit hash value (about 1 million possible values).

### 3. Stream Cipher Check
Here's where it gets interesting. The program uses that hash to seed a **Linear Feedback Shift Register (LFSR)** - a simple pseudo-random number generator.

The LFSR works like this:
```
feedback_bit = (hash[bit 3] XOR hash[bit 0])
new_hash = (hash >> 1) | (feedback_bit << 19)
```

For each character in the flag, it:
1. Steps the LFSR to get a new state
2. XORs the flag character with the low byte of the LFSR state
3. Compares the result against a table of expected values stored in the binary

If all comparisons pass, you win!

## The Trick

Here's the clever part: the hash depends on the flag, and the LFSR seed is the hash. So you can't just "decrypt" the expected values - you need to find a flag where:

1. When you hash it, you get some value H
2. When you use H to generate a keystream and XOR with the flag, you get the expected values

It's self-referential! The flag validates itself.

## Solving It

The key insight is that 20 bits = ~1 million possibilities. That's totally brute-forceable!

The attack:
1. Extract the expected values from the binary (73 bytes at offset 0x2506)
2. Try every possible 20-bit hash value (0 to 2^20 - 1)
3. For each candidate hash:
   - Generate the keystream using the LFSR
   - XOR with expected values to get a candidate flag
   - Check if it's printable ASCII
   - Verify the hash of the candidate equals our starting hash

```python
def hash_string(s):
    lo, hi = 0, 0
    for c in s:
        val = ((lo | (hi << 16)) * 67 + ord(c))
        lo = val & 0xFFFF
        hi = (val >> 16) & 0x0F
    return lo, hi

def lfsr_step(lo, hi):
    val = lo | (hi << 16)
    feedback = ((val >> 3) ^ val) & 1
    new_val = (val >> 1) | (feedback << 19)
    return new_val & 0xFFFF, (new_val >> 16) & 0x0F

# Brute force all 2^20 possibilities
for init in range(1 << 20):
    lo = init & 0xFFFF
    hi = (init >> 16) & 0x0F

    # Generate keystream (step BEFORE using)
    keystream = []
    for _ in range(73):
        lo, hi = lfsr_step(lo, hi)
        keystream.append(lo & 0xFF)

    # Decrypt
    candidate = bytes([k ^ e for k, e in zip(keystream, expected)])

    # Check if printable
    if not all(32 <= c < 127 for c in candidate):
        continue

    # Verify hash matches
    h_lo, h_hi = hash_string(candidate.decode())
    if h_lo == (init & 0xFFFF) and h_hi == ((init >> 16) & 0x0F):
        print(f"Found: {candidate.decode()}")
        break
```

After about a million iterations (takes a few seconds), we find a match!

## Flag

```
lactf{3asy_3nough_7o_8rute_f0rce_bu7_n0t_ea5y_en0ugh_jus7_t0_brut3_forc3}
```

The flag itself is a cheeky message: "easy enough to brute force but not easy enough just to brute force"

And that perfectly describes this challenge - the 20-bit keyspace is small enough to brute force, but you still need to understand the self-referential hash constraint to solve it. You can't just blindly try inputs; you need to work backwards from the expected values.

## Lessons Learned

1. **Old doesn't mean easy** - 16-bit DOS code can be tricky to reverse, but the algorithms are often simpler
2. **Look for the keyspace** - 20 bits (~1M) is very brute-forceable; 32+ bits usually isn't
3. **Self-referential checks are cool** - The hash-of-plaintext-seeds-the-cipher trick is elegant
4. **LFSRs are everywhere** - They're a classic PRNG, worth recognizing the shift-and-XOR pattern

Fun retro challenge!
