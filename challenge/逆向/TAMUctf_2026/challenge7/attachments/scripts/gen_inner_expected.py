import os

FLAG = "gigem{this_will_be_the_flag_for_challenge_7}"
STAGE_TOKEN = 0x1337C0DE


def rotl32(x, r):
    return ((x << (r & 31)) | (x >> ((32 - r) & 31))) & 0xFFFFFFFF


def rotr32(x, r):
    return ((x >> (r & 31)) | (x << ((32 - r) & 31))) & 0xFFFFFFFF


def is_body_char(c):
    return (ord("a") <= c <= ord("z")) or (ord("0") <= c <= ord("9")) or c == ord("_")


def make_constants(flag, stage_token):
    data = flag.encode()
    body_off = 6
    body_len = 37
    state = (stage_token ^ 0xC0DEF00D) & 0xFFFFFFFF
    acc = 0x31415926
    out = []

    for i in range(body_len):
        x = data[body_off + i]
        state = (state + 0x9E3779B9 + (i * 0x45D9F3B)) & 0xFFFFFFFF
        state = rotl32(state, 5) ^ rotr32(state, 3)
        key = (state ^ (state >> 8) ^ (i * 17)) & 0xFF
        add = ((state >> 16) + i * 11) & 0xFF
        t = ((x ^ key) + add) & 0xFF
        out.append(t)
        acc = (rotl32(acc ^ t ^ i, 3) + 0x1020304 + ((t * 13) & 0xFFFFFFFF)) & 0xFFFFFFFF

    return out, acc


words, acc = make_constants(FLAG, STAGE_TOKEN)
packed = []
for base in range(0, len(words), 8):
    v = 0
    chunk = words[base:base + 8]
    for j, b in enumerate(chunk):
        v |= (b & 0xFF) << (8 * j)
    packed.append(v)

print(f"FLAG={FLAG}")
print(f"STAGE_TOKEN=0x{STAGE_TOKEN:08X}")
print("#ifndef INNER_EXPECTED_H")
print("#define INNER_EXPECTED_H")
print("")
print("#include <stdint.h>")
print("")
print("#define INNER_BODY_LEN 37u")
print(f"#define INNER_EXPECT_WORD_COUNT {len(packed)}u")
print("")
for i, v in enumerate(packed):
    print(f"#define INNER_EXPECT_WORD_{i} 0x{v:016X}ull")
print("")
print(f"#define INNER_EXPECT_ACC 0x{acc:08X}u")
print("")
print("#endif")

out = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "src", "inner_expected.h"))
with open(out, "w", encoding="ascii") as f:
    f.write("#ifndef INNER_EXPECTED_H\n")
    f.write("#define INNER_EXPECTED_H\n\n")
    f.write("#include <stdint.h>\n\n")
    f.write("#define INNER_BODY_LEN 37u\n\n")
    f.write(f"#define INNER_EXPECT_WORD_COUNT {len(packed)}u\n\n")
    for i, v in enumerate(packed):
        f.write(f"#define INNER_EXPECT_WORD_{i} 0x{v:016X}ull\n")
    f.write("\n")
    f.write(f"#define INNER_EXPECT_ACC 0x{acc:08X}u\n")
    f.write("\n#endif\n")

print(f"wrote {out}")
