from elftools.elf.elffile import ELFFile
import ctypes
import zlib
from Crypto.Cipher import ARC4

# Decrypt function hidden in .init.checksum.validation
def decrypt(key, encrypted_data):
    ks = 0x67
    out = bytearray()
    key_len = len(key)
    in_len = len(encrypted_data)

    for i in range(in_len):
        k = key[i % key_len]
        ks = (ks + k + i) & 0xff
        out.append(encrypted_data[i] ^ ks)
    
    return bytes(out)

# Get sections
with open("../war-hymn", "rb") as f:
    elf = ELFFile(f)
    secure_buf = elf.get_section_by_name(".bss.secure.buffer")

    if not secure_buf:
        raise ValueError("Section not found")

    encrypted_data = secure_buf.data()

    constructors_global = elf.get_section_by_name(".init.constructors.global")

    if not constructors_global:
        raise ValueError("Constructors section not found")

    # Ends with a null byte, so skip that
    # We can see the Ghidra disassembly do the same: key = key + -1;
    key = constructors_global.data()[:len(constructors_global.data()) - 1]

decrypt_result = decrypt(key, encrypted_data)

# Skip first 8 bytes since first 4 bytes are payload_len and next 4 bytes are zlib_len
# Even without knowing that though, in Ghidra we see the function call to load the shared library using a + 8 offset 
# when passing in the decrypted payload: load_shared_library(puVar9 + i + 8,zlib_size,local_132,local_107);

print("Writing decrypted zlib data to decrypted_zlib.bin...")

actual_zlib_data = decrypt_result[8:]
with open("decrypted_zlib.bin", "wb") as f:
    f.write(actual_zlib_data)


decompressed = zlib.decompress(actual_zlib_data, 15)

print("Writing decompressed data to shared_library.so...")

with open("shared_library.so", "wb") as f:
    f.write(decompressed)

# lib = ctypes.CDLL("./shared_library.so")
# lib.run.restype = ctypes.c_char_p
# result = lib.run()
# print(result.decode())

# From the extracted shared library
key = b"AggiesAggiesAggies"

data1 = bytes([
    0xc1, 0x4f, 0x8d, 0xde, 0xbd, 0x20, 0x4f, 0x7d,
    0x21, 0x7c, 0x03, 0x8b, 0xf0, 0xa7, 0x4a, 0x29,
    0xa5, 0xf6
])

data2 = bytes([
    0xd3, 0x4f, 0x89, 0xc6, 0xb1, 0x67, 0x54, 0x7c,
    0x26, 0x68, 0x03, 0x88, 0xeb, 0xbc, 0x56
])

data3 = bytes([
    0xd9, 0x58, 0x89, 0x96, 0xe6, 0x65, 0x1b, 0x61, 0x20, 0x6a, 0x51, 0x8f, 0xb9, 0xb0, 0x5b, 0x7d, 0xf3
])

data = bytearray([
    0xff, 0x43, 0x8b, 0xd3, 0xfc, 0x7b, 0x48, 0x7d,
    0x78, 0x7a, 0x4f, 0x8e, 0xc6, 0xa1, 0x0a, 0x7f,
    0xff, 0xdd, 0x98, 0x98, 0x70, 0xe1, 0x64, 0xd5,
    0xa8, 0x1b, 0x7f, 0x45, 0x2a, 0xa6, 0x3e, 0xe2,
    0x4a, 0x96, 0x36, 0xd5, 0x22, 0xc2, 0xc2, 0xb7,
    0xb0, 0xa4, 0x80, 0xc4, 0x09, 0x8c, 0x50, 0xdc,
    0xb5, 0x64, 0x71, 0x53
])

plaintext1 = ARC4.new(key).decrypt(data1)
plaintext2 = ARC4.new(key).decrypt(data2)
plaintext3 = ARC4.new(key).decrypt(data3)
plaintext4 = ARC4.new(key).decrypt(data)
print("Plaintext 1:", plaintext1)
print("Plaintext 2:", plaintext2)
print("Plaintext 3:", plaintext3)
print("Plaintext 4:", plaintext4)