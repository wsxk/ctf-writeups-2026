import hashlib
import os
import subprocess

root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
build_dir = os.path.join(root, "build")
bin_path = os.environ.get("CHALLENGE_BIN", "").strip()

if not bin_path:
    preferred = [
        os.path.join(build_dir, "challenge7"),
        os.path.join(build_dir, "challenge7_main"),
    ]
    for candidate in preferred:
        if os.path.isfile(candidate):
            bin_path = candidate
            break

if not bin_path:
    raise FileNotFoundError(
        "unable to resolve challenge binary for self hash; set CHALLENGE_BIN"
    )

if not os.path.isabs(bin_path):
    bin_path = os.path.join(root, bin_path)

if not os.path.isfile(bin_path):
    raise FileNotFoundError(f"challenge binary not found: {bin_path}")

out_path = os.path.join(root, "src", "self_hash.h")
bin_base = os.path.basename(bin_path)
text_path = os.path.join(build_dir, f"{bin_base}.text.bin")

subprocess.check_call(["objcopy", "--only-section=.text", "-O", "binary", bin_path, text_path])

with open(text_path, "rb") as f:
    digest = hashlib.sha256(f.read()).digest()

with open(out_path, "w", encoding="ascii") as f:
    f.write("#ifndef SELF_HASH_H\n")
    f.write("#define SELF_HASH_H\n\n")
    f.write("#include <stdint.h>\n\n")
    f.write("#define SELF_HASH_READY 1u\n\n")
    f.write("static const uint8_t self_expected_sha256[32] = {")
    for i, b in enumerate(digest):
        if i % 8 == 0:
            f.write("\n\t")
        f.write(f"0x{b:02x}u")
        if i != 31:
            f.write(", ")
    f.write("\n};\n\n")
    f.write("#endif\n")

print(f"wrote {out_path}")
print(f"self_hash_bin={bin_path}")
print("self_text_sha256=" + digest.hex())
