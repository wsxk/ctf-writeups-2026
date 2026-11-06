# Polly's Key

**Category:** Reverse Engineering<br>
**Points:** 500

## Description

A single file that is simultaneously valid Ruby AND valid Perl -- a polyglot. The challenge requires finding a 50-character key that passes validation checks in both languages simultaneously, which then decrypts the flag via MD5 and XOR.

## Solution

### Step 1: Recognize the Polyglot

The file can be executed with either `ruby pollys_key` or `perl pollys_key`. Both interpret the same source file but execute different code paths, thanks to how each language handles multi-line comments:

- Ruby uses `=begin` ... `=end` as comment blocks
- Perl uses `=begin` ... `=cut` as POD blocks, ignoring `=end`

This lets the author selectively show code to one language while hiding it from the other.

### Step 2: Trace Both Code Paths

**Ruby (the pirate)** requires:
- All characters with ASCII values 33-126
- Each value transformed by `(value - 16) % 257` must be a **primitive root modulo 257**
- Exactly 50 unique characters
- Ordering constraints: `c` before `F`, `O` before `p`, `E` before `f`

**Perl (the parrot)** requires:
- A completely different transformation due to `.` being concatenation in Perl (not a method call): the "same" line `$_ - $c.hex` computes a different mathematical function
- No caret character (ASCII 94)
- An insertion sort inversion count must match a hardcoded `sArray`, constraining the exact ordering

### Step 3: Exploit the Tight Constraint

There are exactly **50** printable ASCII characters (excluding `^`) whose Ruby-transformed values are primitive roots mod 257. Not 51, not 49 -- exactly 50. So every valid character must be used exactly once; only the ordering matters.

The `sArray` inversion table determines the rank of every position in sorted order. Seven character pairs share the same Perl-transform value (creating ties), and the ordering constraints from both languages resolve every tie uniquely.

### Step 4: Decrypt the Flag

Once the key is determined, both languages compute:
```
MD5(key) -> take each hex nibble -> XOR with encrypted treasure array -> ASCII
```

```python
import hashlib

key = "}O;m`pHw[Gq(g1\\5@W6~Uu8{v7jnE?=9yRZ|$f#],ceCbkF+Qz"
enc = [76,77,65,83,67,121,85,100,48,94,91,48,53,102,82,55,
       97,73,111,123,61,52,76,116,95,116,58,123,119,54,120,127]
md5 = hashlib.md5(key.encode()).hexdigest()
flag = ''.join(chr(int(md5[x], 16) ^ enc[x]) for x in range(32))
print(flag)  # BCCTF{Th3_P05h_9oLly61Ot_p4rr0t}
```

### Verification

```
$ echo '}O;m`pHw[Gq(g1\5@W6~Uu8{v7jnE?=9yRZ|$f#],ceCbkF+Qz' | ruby pollys_key
Aft a bit o' thought, I appreciate wha' ye've done wit' yer key.
If me parrot agrees, dis best be me treasure: BCCTF{Th3_P05h_9oLly61Ot_p4rr0t}

$ echo '}O;m`pHw[Gq(g1\5@W6~Uu8{v7jnE?=9yRZ|$f#],ceCbkF+Qz' | perl pollys_key
SQUAWK YOU REALLY DID IT SQUAWK! IF MY SERVANT AGREES SQUAWK
THIS SHOULD BE THE FLAG SQUAWK: BCCTF{Th3_P05h_9oLly61Ot_p4rr0t}
```

## Flag

`BCCTF{Th3_P05h_9oLly61Ot_p4rr0t}`

## Files

- `solve.py` - Solution script
