import struct

BLOCK_SIZE = 64
MASK32 = 0xFFFFFFFF
DELTA = 0x70336364

ALPHA = 8
BETA = 3


def ror32(x, r):
    r &= 31
    return ((x >> r) | (x << (32 - r))) & MASK32


def rol32(x, r):
    r &= 31
    return ((x << r) | (x >> (32 - r))) & MASK32


def words_be(b):
    if len(b) % 4:
        raise ValueError("length must be multiple of 4")
    return list(struct.unpack(">" + "I" * (len(b) // 4), b))


def bytes_be(ws):
    return struct.pack(">" + "I" * len(ws), *[w & MASK32 for w in ws])


def speck_pair(x, y, k):
    x = ror32(x, ALPHA)
    x = (x + y) & MASK32
    x ^= k
    y = rol32(y, BETA)
    y ^= x
    return x, y


def speck_pair_inv(x, y, k):
    y ^= x
    y = ror32(y, BETA)
    x ^= k
    x = (x - y) & MASK32
    x = rol32(x, ALPHA)
    return x, y


def expand_key(key32, rounds):
    if len(key32) != 32:
        raise ValueError("key must be 32 bytes")
    a, b, c, d, e, f, g, h = words_be(key32)
    s = 0x73756572
    rks = []
    for r in range(rounds):
        s = (s + DELTA + r) & MASK32
        a = (a + rol32(b ^ s, 3)) & MASK32
        b = (b + rol32(c ^ a, 5)) & MASK32
        c = (c + rol32(d ^ b, 7)) & MASK32
        d = (d + rol32(e ^ c, 11)) & MASK32
        e = (e + rol32(f ^ d, 13)) & MASK32
        f = (f + rol32(g ^ e, 17)) & MASK32
        g = (g + rol32(h ^ f, 19)) & MASK32
        h = (h + rol32(a ^ g, 23)) & MASK32

        rks.append([
            (a ^ c ^ s) & MASK32,
            (b ^ d ^ (s + 0x62616f7a)) & MASK32,
            (e ^ g ^ (s + 0x6f6e6777)) & MASK32,
            (f ^ h ^ (s + 0x696e6221)) & MASK32,
            (a + e) & MASK32,
            (b + f) & MASK32,
            (c + g) & MASK32,
            (d + h) & MASK32,
            (a ^ f) & MASK32,
            (b ^ g) & MASK32,
            (c ^ h) & MASK32,
            (d ^ e) & MASK32,
        ])
    return rks


def F_round(R, rk, s):
    R2 = R[:]
    for p in range(4):
        i = 2 * p
        R2[i], R2[i + 1] = speck_pair(R2[i], R2[i + 1], rk[p])

    Fout = [0] * 8
    for i in range(8):
        ri = R2[i]
        rj = R2[(i + 1) & 7]
        mix = (((ri << 4) ^ (ri >> 5)) + rj) & MASK32
        k = rk[4 + i]
        extra = rol32(R2[(i + 3) & 7], (i + 1) & 31)
        Fout[i] = ((mix ^ (s + k)) + (extra ^ (s >> ((i + 1) & 7)))) & MASK32
    return R2, Fout


def inv_pairmix(R2, rk):
    R = R2[:]
    for p in (3, 2, 1, 0):
        i = 2 * p
        R[i], R[i + 1] = speck_pair_inv(R[i], R[i + 1], rk[p])
    return R


def encrypt_block_64(block64, key32, rounds=4):
    if len(block64) != 64:
        raise ValueError("block must be 64 bytes")
    rks = expand_key(key32, rounds)

    W = words_be(block64)
    L, R = W[:8], W[8:]
    s = 0
    for rk in rks:
        s = (s + DELTA) & MASK32
        R2, Fout = F_round(R, rk, s)
        L, R = R2, [(L[i] ^ Fout[i]) & MASK32 for i in range(8)]
    return bytes_be(L + R)


def decrypt_block_64(block64, key32, rounds=4):
    if len(block64) != 64:
        raise ValueError("block must be 64 bytes")
    rks = expand_key(key32, rounds)

    W = words_be(block64)
    L, R = W[:8], W[8:]

    sums = []
    s = 0
    for _ in range(rounds):
        s = (s + DELTA) & MASK32
        sums.append(s)

    for idx in range(rounds - 1, -1, -1):
        rk = rks[idx]
        s = sums[idx]
        R2 = L

        Fout = [0] * 8
        for i in range(8):
            ri = R2[i]
            rj = R2[(i + 1) & 7]
            mix = (((ri << 4) ^ (ri >> 5)) + rj) & MASK32
            k = rk[4 + i]
            extra = rol32(R2[(i + 3) & 7], (i + 1) & 31)
            Fout[i] = ((mix ^ (s + k)) + (extra ^ (s >> ((i + 1) & 7)))) & MASK32

        L_prev = [(R[i] ^ Fout[i]) & MASK32 for i in range(8)]
        R_prev = inv_pairmix(R2, rk)
        L, R = L_prev, R_prev

    return bytes_be(L + R)


def pkcs7_pad(data, bs=BLOCK_SIZE):
    pad = bs - (len(data) % bs)
    return data + bytes([pad]) * pad


def pkcs7_unpad(data, bs=BLOCK_SIZE):
    if not data or (len(data) % bs):
        raise ValueError("bad padded length")
    pad = data[-1]
    if pad < 1 or pad > bs:
        raise ValueError("bad padding")
    tail = data[-pad:]
    bad = 0
    for b in tail:
        bad |= (b ^ pad)
    if bad:
        raise ValueError("bad padding")
    return data[:-pad]


def derive_next_key32_from_block(block64):
    """用上一轮密文(64B)派生下一轮 key(32B)：前32B XOR 后32B"""
    a = block64[:32]
    b = block64[32:]
    return bytes(x ^ y for x, y in zip(a, b))


def encrypt_key_chaining(plaintext, key32, rounds=4):
    """
    取消 CBC，仅 padding。
    每块用当前 key 加密；下一块 key = f(上一块密文)
    输出：ciphertext（无 IV）
    """
    if len(key32) != 32:
        raise ValueError("key must be 32 bytes")
    pt = pkcs7_pad(plaintext, BLOCK_SIZE)
    out = bytearray()
    k = key32
    mv = memoryview(pt)
    for i in range(0, len(pt), BLOCK_SIZE):
        block = mv[i:i + BLOCK_SIZE].tobytes()
        c = encrypt_block_64(block, k, rounds=rounds)
        out += c
        k = derive_next_key32_from_block(c)
    return bytes(out)


def decrypt_key_chaining(ciphertext, key32, rounds=4):
    """
    解密端同样 key chaining：
    每块用当前 key 解密；下一块 key = f(本块密文)
    """
    if len(key32) != 32:
        raise ValueError("key must be 32 bytes")
    if len(ciphertext) == 0 or (len(ciphertext) % BLOCK_SIZE):
        raise ValueError("ciphertext length must be multiple of 64")
    out = bytearray()
    k = key32
    mv = memoryview(ciphertext)
    for i in range(0, len(ciphertext), BLOCK_SIZE):
        c = mv[i:i + BLOCK_SIZE].tobytes()
        p = decrypt_block_64(c, k, rounds=rounds)
        out += p
        k = derive_next_key32_from_block(c)
    return pkcs7_unpad(bytes(out), BLOCK_SIZE)


if __name__ == "__main__":
    key = bytes(range(32))
    data = open("ddd.su_mv_enc", "rb").read()[4:]
    # ct = encrypt_key_chaining(data, key, rounds=4)
    rt = decrypt_key_chaining(data, key, rounds=4)
    with open("ddd.wav", "wb") as f:
        f.write(rt)