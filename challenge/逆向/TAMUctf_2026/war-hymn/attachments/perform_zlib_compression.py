import zlib

# Read the original .so file
with open("shared.so", "rb") as f:
    so_data = f.read()

# Compress with raw DEFLATE (matching what zlib-flate should do)
compressed = zlib.compress(so_data)[2:-4]  # Strip zlib header and checksum for raw deflate

# Or just use zlib format (easier)
compressed_zlib = zlib.compress(so_data)

# Save raw deflate version
with open("shared.so.deflate", "wb") as f:
    f.write(compressed)

# Save zlib version  
with open("shared.so.zlib", "wb") as f:
    f.write(compressed_zlib)

print(f"Original size: {len(so_data)}")
print(f"Compressed (raw deflate): {len(compressed)}")
print(f"Compressed (zlib): {len(compressed_zlib)}")

# Verify raw deflate decompresses
try:
    test = zlib.decompress(compressed, -15)
    print(f"✓ Raw deflate verified: {len(test)} bytes")
except Exception as e:
    print(f"✗ Raw deflate failed: {e}")

# Verify zlib decompresses
try:
    test = zlib.decompress(compressed_zlib)
    print(f"✓ Zlib verified: {len(test)} bytes")
except Exception as e:
    print(f"✗ Zlib failed: {e}")