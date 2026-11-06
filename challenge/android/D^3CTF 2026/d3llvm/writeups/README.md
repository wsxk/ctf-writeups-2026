# d3llvm Writeup

**Challenge:** d3llvm  
**Category:** Reverse Engineering  
**Points:** 1000  
**Flag:** `d3ctf{OLLVM_is_still_somewhat_useful_for_AI}`

## The short version

The APK asks us to handwrite a 64-character hexadecimal token, verifies it in
native code, and then starts a small game. Reaching 100 points calls another
native function which decrypts the flag.

There are three main problems:

1. The interesting native library is encrypted.
2. The token checker is heavily control-flow-obfuscated.
3. The flag key also uses a secret generated while the handwriting model runs.

The final token is:

```text
196f0d201332b47deb98221f33c7f4a13d03de6c2a77279c4dbc1f87e4d297a8
```

## 1. Looking through the APK

An APK is basically a ZIP archive, so I started by unpacking it and opening it
with JADX:

```bash
unzip app-debug.apk -d extracted
jadx -d jadx_out app-debug.apk
```

The relevant Java classes were:

- `MainActivity`
- `MnnTouchClassifier`
- `GameActivity`
- `OpcodeDashGame`
- `FlagNative`

`MainActivity` tells us that the input must be exactly 64 characters. Each
character is produced by an MNN handwriting classifier and normalized to one
of:

```text
0123456789abcdef
```

When all 64 characters have been entered, Java calls:

```java
FlagNative.nativeVerifyInput(userInput.toString())
```

If that returns true, the game starts. `OpcodeDashGame` has a target score of
100, after which `nativeRevealFlag()` is called.

So the game itself is mostly a distraction. The real work is in the native
libraries.

## 2. Finding the encrypted payload

The APK contains both a loader and a payload:

```text
lib/arm64-v8a/libd3llvm.so
lib/arm64-v8a/libd3llvm_payload.so
```

The payload's code section is encrypted. A structure named `.signinfo` at file
offset `0x52b0` contains:

- Magic: `D3SGN2`
- Encrypted text offset and size
- A 16-byte nonce
- A 32-byte key
- The expected SHA-256 hash of the plaintext

The stream cipher is simple: for every 32-byte block, calculate:

```text
SHA256(key || nonce || little_endian_64(counter))
```

and XOR that digest with the ciphertext.

Here is the complete decryption script:

```python
from pathlib import Path
import hashlib
import struct

p = Path("extracted/lib/arm64-v8a/libd3llvm_payload.so")
b = bytearray(p.read_bytes())

sign = b[0x52b0:0x53b0]
assert sign[:8] == b"D3SGN2\0\0"

text_vaddr, text_size, text_off = struct.unpack_from("<QQQ", sign, 0x10)
nonce = sign[0x28:0x38]
key = sign[0x38:0x58]
expected_hash = sign[0x58:0x78]

text = bytearray(b[text_off:text_off + text_size])

for counter, pos in enumerate(range(0, len(text), 32)):
    stream = hashlib.sha256(
        key + nonce + struct.pack("<Q", counter)
    ).digest()

    for i in range(min(32, len(text) - pos)):
        text[pos + i] ^= stream[i]

assert hashlib.sha256(text).digest() == expected_hash

b[text_off:text_off + text_size] = text
Path("libd3llvm_payload.dec.so").write_bytes(b)
```

The recovered plaintext hash is:

```text
ac4a4b6d774425ec553b3207607f4ab6f6052a72a893536e857eba8a91022f10
```

At this point, tools such as Ghidra, Binary Ninja, or radare2 can properly
disassemble the payload.

## 3. Solving the token checker

The exported JNI wrapper for `nativeVerifyInput` eventually reaches a custom
checker at payload offset `0x35330`.

Before that, the input is checked to ensure that it is:

- Exactly 64 characters
- Lowercase hexadecimal

It is then decoded into sixteen 16-bit words. The checker is intentionally
ugly: its control flow has been flattened and routed through lookup tables.
Reading all of it by hand is possible, but not especially fun.

Instead, I used angr. Each of the sixteen words was symbolic, and angr executed
the checker until it reached a return state where `x0 == 1`.

```python
import angr
import claripy

SO = "libd3llvm_payload.dec.so"

p = angr.Project(SO, auto_load_libs=False)
base = p.loader.main_object.mapped_base

input_address = 0x700000
words = [claripy.BVS(f"word_{i}", 16) for i in range(16)]

state = p.factory.call_state(
    base + 0x35330,
    input_address,
    base + 0x42fb8,
    add_options={
        angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY,
        angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS,
    },
)

for i, word in enumerate(words):
    state.memory.store(
        input_address + i * 2,
        word,
        endness=p.arch.memory_endness,
    )

simgr = p.factory.simgr(state)
simgr.run()

for result in simgr.deadended:
    result.add_constraints(result.regs.x0 == 1)
    if result.solver.satisfiable():
        values = [result.solver.eval(word) for word in words]
        print("".join(f"{value:04x}" for value in values))
        break
```

This produces:

```text
196f0d201332b47deb98221f33c7f4a13d03de6c2a77279c4dbc1f87e4d297a8
```

The sixteen words are:

```text
196f 0d20 1332 b47d eb98 221f 33c7 f4a1
3d03 de6c 2a77 279c 4dbc 1f87 e4d2 97a8
```

Running the real native checker with this token returns true.

## 4. Why the token alone is not enough

Initially I tried passing the token directly to the flag routine. That failed
with:

```text
ciphertext has invalid PKCS7 padding
```

The verifier saves two pieces of information:

1. The valid token
2. A 64-bit value from the handwriting classifier's native state

The second value is used as part of the flag key. This prevents us from merely
patching the token check and immediately asking for the flag.

The classifier state contains:

```text
+0x1c   64 bytes marking active input positions
+0x60   64 unsigned 64-bit contribution values
+0x260  final 64-bit accumulated secret
```

The final secret is calculated as:

```c
secret = 0;
for (int i = 0; i < 64; i++) {
    if (position_is_active[i]) {
        secret += contribution[i];
    }
}
```

All 64 positions are active for a complete token.

## 5. Understanding the handwriting contribution

The classifier uses MNN's:

```cpp
runSessionWithCallBackInfo(...)
```

The callback executed after every optimized model operation takes that
operation's name, calculates its 64-bit FNV-1a hash, and adds it to an
accumulator.

FNV-1a is:

```python
MASK = (1 << 64) - 1

def fnv1a64(data):
    h = 0xcbf29ce484222325
    for byte in data:
        h ^= byte
        h = (h * 0x100000001b3) & MASK
    return h
```

Importantly, the callback hashes the operation names, not the user's actual
drawing coordinates. The optimized operation list is the same for every
character, so every input position receives the same contribution.

### Decrypting the MNN model

The model is stored as:

```text
assets/model/touch_model.mnn.enc
```

Despite the key string saying `This is 3DES`, the file is encrypted with
AES-128-ECB. The key is the string padded with four null bytes:

```python
key = b"This is 3DES" + b"\0" * 4
```

The plaintext starts with 12 junk bytes followed by a Base64-encoded MNN
model:

```python
from Crypto.Cipher import AES
import base64

ciphertext = open("touch_model.mnn.enc", "rb").read()
plaintext = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)
plaintext = plaintext[:-plaintext[-1]]  # Remove PKCS#7 padding

model = base64.b64decode(plaintext[12:])
open("touch_model.mnn", "wb").write(model)
```

I loaded the recovered model with MNN 3.6 and printed the names passed to the
post-operation callback. The optimized execution uses these thirteen names:

```text
getitem_raster_0
getitem
getitem_3_raster_0
getitem_3
max_pool1d_raster_0
max_pool1d
getitem_6_raster_0
getitem_6
mean_raster_0
mean_raster_1
logits__matmul_converted_raster_0
logits__matmul_converted
logits_raster_0
```

Adding their FNV-1a hashes modulo `2^64` gives the contribution for one
character:

```text
0x4280720401113ed2
```

There are 64 active characters, so:

```python
contribution = 0x4280720401113ed2
secret = (contribution * 64) & 0xffffffffffffffff
print(hex(secret))
```

Result:

```text
0xa01c8100444fb480
```

## 6. Deriving the flag key

The final AES key depends on both the token and the classifier secret.

First, the token is hashed with FNV-1a:

```text
FNV1a64(token) = 0xc05f81ba6ac93cf5
```

The program then derives two 64-bit values with SplitMix64:

```python
MASK = (1 << 64) - 1

def splitmix64(x):
    x = (x + 0x9e3779b97f4a7c15) & MASK
    x = ((x ^ (x >> 30)) * 0xbf58476d1ce4e5b9) & MASK
    x = ((x ^ (x >> 27)) * 0x94d049bb133111eb) & MASK
    return x ^ (x >> 31)

def ror64(x, n):
    return ((x >> n) | (x << (64 - n))) & MASK

a = splitmix64(
    token_hash
    ^ secret
    ^ 0xd3c7f19a5eed2026
)

b = splitmix64(
    secret
    ^ ror64(token_hash, 47)
    ^ 0xa11ce5c0dec0de42
)
```

The AES key is `a` followed by `b`, both encoded little-endian:

```text
a = 0xd2afe8c4612f0322
b = 0xaa8d52b4e3653bd4

AES key = 22032f61c4e8afd2d43b65e3b4528daa
```

## 7. Decrypting the flag

The payload contains 48 bytes of ciphertext at file offset `0x4a94`:

```text
f154eaeafaebf01674f062267087e584
f3842f342f59283dbf515aacf4cd01d1
51c2a502b36d45be5cb5f9b11942d2c1
```

The final decryption is AES-128-ECB with PKCS#7 padding:

```python
from Crypto.Cipher import AES
import struct

key = struct.pack("<QQ", a, b)

ciphertext = bytes.fromhex(
    "f154eaeafaebf01674f062267087e584"
    "f3842f342f59283dbf515aacf4cd01d1"
    "51c2a502b36d45be5cb5f9b11942d2c1"
)

plaintext = AES.new(key, AES.MODE_ECB).decrypt(ciphertext)
plaintext = plaintext[:-plaintext[-1]]
print(plaintext.decode())
```

Output:

```text
d3ctf{OLLVM_is_still_somewhat_useful_for_AI}
```

## Final answer

```text
Token:
196f0d201332b47deb98221f33c7f4a13d03de6c2a77279c4dbc1f87e4d297a8

Flag:
d3ctf{OLLVM_is_still_somewhat_useful_for_AI}
```

The main trick was realizing that the hidden classifier value did not depend
on drawing the token perfectly. It was just a checksum of MNN's optimized
operation names. Once that was identified, the rest reduced to a few standard
hashes and an AES decryption.
