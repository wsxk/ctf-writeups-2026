import os
import random

random.seed(0x5A17)

counts = [145, 125, 130, 120, 140, 120, 80, 52]
variants_bias = {
    1: [2, 7, 10, 1, 4, 9, 12, 15],
    2: [0, 3, 5, 6, 8, 11, 13, 14],
    3: list(range(16)),
    4: list(range(16)),
    5: [1, 9, 2, 7, 10, 4, 12, 15],
    6: list(range(16)),
    7: list(range(16)),
    8: list(range(16)),
}

insts = []
for t, n in enumerate(counts, start=1):
    pool = variants_bias[t]
    for _ in range(n):
        v = pool[random.randrange(len(pool))]
        opcode = (t << 4) | (v & 0xF)
        op1 = random.randrange(256)
        op2 = random.randrange(256)
        insts.append((opcode, op1, op2))

random.shuffle(insts)
blob = []
for a, b, c in insts:
    blob.extend([a, b, c])

assert len(insts) == 912
assert len(blob) == 2736

out = os.path.join(os.path.dirname(__file__), "..", "generated_chamber.h")
with open(out, "w", encoding="ascii") as f:
    f.write("#ifndef GENERATED_CHAMBER_H\n")
    f.write("#define GENERATED_CHAMBER_H\n\n")
    f.write("#include <stdint.h>\n\n")
    f.write("#define CHAMBER_INSTRUCTIONS 912u\n")
    f.write("#define CHAMBER_BLOB_BYTES 2736u\n\n")
    f.write("static const uint8_t k_chamber_blob[CHAMBER_BLOB_BYTES] = {\n")
    for i in range(0, len(blob), 24):
        row = ", ".join(f"0x{b:02x}" for b in blob[i:i + 24])
        f.write(f"    {row},\n")
    f.write("};\n\n")
    f.write("#endif\n")
