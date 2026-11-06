from pathlib import Path
from typing import Tuple

from Crypto.Cipher import AES

K_AES_KEY = b"youknowwhatImean"
K_AES_IV = b"itsallintheflow!"
K_CIPHER_TARGET = bytes(
    [
       0x56, 0x96, 0x70, 0xde, 0x6d, 0x7e, 0x27, 0x0e, 0x7e, 0x27, 0xa1, 0x89, 0xce, 0xc7, 0x08, 0x2b,
        0xa1, 0x88, 0x3f, 0x69, 0x79, 0x66, 0x31, 0xad, 0xbd, 0x7c, 0x6d, 0x0f, 0xea, 0x9f, 0x28, 0x1d,
        0x60, 0xf9, 0xd1, 0x27, 0x7f, 0x1b, 0x00, 0x7c, 0x36, 0xd6, 0x31, 0x72, 0x77, 0x53, 0xed, 0xcf
    ]
)

RC4_KEY = b"TobeorNottobe"


def u32(x: int) -> int:
    return x & 0xFFFFFFFF


def rotl8(v: int, s: int) -> int:
    return ((v << s) | (v >> (8 - s))) & 0xFF


def rotr8(v: int, s: int) -> int:
    return ((v >> s) | (v << (8 - s))) & 0xFF


def xorshift32(v: int) -> int:
    v = u32(v)
    v ^= (v << 13) & 0xFFFFFFFF
    v ^= v >> 17
    v ^= (v << 5) & 0xFFFFFFFF
    return u32(v)


def fnv1a32(data: bytes) -> int:
    h = 2166136261
    for b in data:
        h ^= b
        h = u32(h * 16777619)
    return h


def crc32_custom(data: bytes) -> int:
    table = []
    for i in range(256):
        c = i
        for _ in range(8):
            c = (0xEDB88320 ^ (c >> 1)) if (c & 1) else (c >> 1)
        table.append(c & 0xFFFFFFFF)

    crc = 0xFFFFFFFF
    for b in data:
        crc = table[(crc ^ b) & 0xFF] ^ (crc >> 8)
    return u32(~crc)


def derive_runtime_key_iv(bundle: bytes) -> Tuple[bytes, bytes]:
    n = len(bundle)
    salt_k = fnv1a32(bundle) & 0xFF
    salt_i = (crc32_custom(bundle) >> 8) & 0xFF

    rk = bytearray(16)
    riv = bytearray(16)
    for i in range(16):
        kb = bundle[(i * 17 + 11) % n]
        ib = bundle[(i * 29 + 7) % n]
        rk[i] = K_AES_KEY[i] ^ kb ^ ((salt_k + i) & 0xFF)
        riv[i] = K_AES_IV[i] ^ ib ^ ((salt_i + i * 3) & 0xFF)
    return bytes(rk), bytes(riv)


def pkcs7_unpad(data: bytes, block_size: int = 16) -> bytes:
    pad = data[-1]
    return data[:-pad]


def rc4warp_process(key: bytes, data: bytes) -> bytes:
    s = list(range(256))
    j = 0
    salt = 0xC3

    for i in range(256):
        k0 = key[(i * 5 + 1) % len(key)]
        k1 = key[(i * 3 + 7) % len(key)]
        salt = rotl8(salt, 1)
        j = (j + s[i] + k0 + ((k1 ^ salt) & 0xFF) + i) & 0xFF
        s[i], s[j] = s[j], s[i]

    i = 0
    j = 0
    twist = 0x9D
    out = bytearray(len(data))

    for n, b in enumerate(data):
        i = (i + 1) & 0xFF
        j = (j + s[i] + ((i * 11) & 0xFF)) & 0xFF
        s[i], s[j] = s[j], s[i]

        idx = (s[i] + s[j] + ((s[(i + j) & 0xFF] ^ twist) & 0xFF)) & 0xFF
        k = s[idx]
        twist = rotl8(twist, 3)
        spice = s[(k ^ twist) & 0xFF]
        out[n] = (b ^ k ^ spice ^ ((i * 13) & 0xFF)) & 0xFF

    return bytes(out)


def recover_flag(bundle_path: Path) -> str:
    bundle = bundle_path.read_bytes()
    rk, riv = derive_runtime_key_iv(bundle)

    stage1_padded = AES.new(rk, AES.MODE_CBC, riv).decrypt(K_CIPHER_TARGET)
    stage1 = pkcs7_unpad(stage1_padded)
    flag_bytes = rc4warp_process(RC4_KEY, stage1)
    return flag_bytes.decode("utf-8")


def main() -> None:
    bundle_path = Path("cache.snap.bundle")
    flag = recover_flag(bundle_path)
    print(flag)


if __name__ == "__main__":
    main()