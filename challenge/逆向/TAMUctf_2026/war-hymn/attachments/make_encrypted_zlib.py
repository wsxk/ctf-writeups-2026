
import struct 

def encrypt(blob: bytes, key: str) -> bytes:
    encrypted = bytearray()
    ks = 0x67

    key_bytes = key.encode() 

    for i, b in enumerate(blob):
        ks = (ks + key_bytes[i % len(key_bytes)] + i) & 0xff
        encrypted.append(b ^ ks)

    return bytes(encrypted)


key = "Hullabaloo, Caneck! Caneck! Hullabaloo, Caneck! Caneck! All hail to dear old Texas A&M Rally around Maroon and White Good luck to dear old Texas Aggies They are the boys who show the real old fight That good old Aggie spirit thrills us And makes us yell and yell and yell So let's fight for dear old Texas A&M We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M! Good-bye to texas university So long to the orange and the white Good luck to dear old Texas Aggies They are the boys that show the real old fight 'The eyes of Texas are upon you . . .' That is the song they sing so well So good-bye to texas university We're going to beat you all to Chig-gar-roo-gar-rem Chig-gar-roo-gar-rem Rough Tough! Real Stuff! Texas A&M!"
filename = "shared.so.zlib"
print(f"Python key byte at 271: 0x{ord(key[271]):02x} ('{key[271]}')")
print(f"Python key length: {len(key)}")
with open(filename, "rb") as f:
    data = f.read()

zlib_len = len(data)

# Create blob: [payload_len][zlib_len][zlib data]
blob = struct.pack("<I", zlib_len + 8) + struct.pack("<I", zlib_len) + data

print(f"Original blob size: {len(blob)}")
print(f"First 20 bytes (before encryption): {blob[:20].hex()}")

# Encrypt
encrypted = encrypt(blob, key)

with open("encrypted_zlib.bin", "wb") as f:
    f.write(encrypted)

# Now decrypt to verify
decrypted = encrypt(encrypted, key)

print(f"Decrypted size: {len(decrypted)}")
print(f"First 20 bytes (after decrypt): {bytes(decrypted[:20]).hex()}")
print(f"Match: {blob == bytes(decrypted)}")

# Extract and verify the zlib portion
payload_len_dec = struct.unpack("<I", decrypted[0:4])[0]
zlib_len_dec = struct.unpack("<I", decrypted[4:8])[0]
zlib_data_dec = bytes(decrypted[8:])

print(f"\npayload_len: {payload_len_dec}")
print(f"zlib_len: {zlib_len_dec}")
print(f"zlib data size: {len(zlib_data_dec)}")
print(f"First 16 bytes of zlib: {zlib_data_dec[:16].hex()}")

# Try to decompress
import zlib
try:
    decompressed = zlib.decompress(zlib_data_dec)
    print(f"SUCCESS! Decompressed {len(decompressed)} bytes")
except Exception as e:
    print(f"FAILED: {e}")