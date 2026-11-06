import hashlib
import os
import random
import subprocess
import struct

DECOY_MULTIPLIER = 3
ABI_VERSION = 1
INITIAL_STAGE_ID = 0
EXEC_STAGE_1 = 1
EXEC_STAGE_2 = 2
TERMINAL_STAGE_ID = EXEC_STAGE_2
INITIAL_TOKEN = 0x1337C0DE

root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
obj_path = os.path.join(root, "build", "inner.o")
out_path = os.path.join(root, "src", "inner_chunks.h")
text_path = os.path.join(root, "build", "inner.text.bin")

subprocess.check_call(["objcopy", "--only-section=.text", "-O", "binary", obj_path, text_path])
text = open(text_path, "rb").read()

sym = subprocess.check_output(["readelf", "-sW", obj_path], text=True)
line = [x for x in sym.splitlines() if " FUNC " in x and x.rstrip().endswith(" inner_entry")][0]
parts = line.split()
sym_off = int(parts[1], 16)
sym_size = int(parts[2])

data = text[sym_off:sym_off + sym_size]
digest = hashlib.sha256(data).digest()

rng = random.Random(int.from_bytes(digest[:8], "big"))

chunks = []
start = 0
while start < len(data):
    chunk_len = rng.randint(1, min(10, len(data) - start))
    end = start + chunk_len
    chunks.append((start, data[start:end]))
    start = end

shuffled_chunks = chunks[:]
rng.shuffle(shuffled_chunks)
chunk_start_to_id = {chunk_start: i for i, (chunk_start, _) in enumerate(shuffled_chunks)}
BIND_ZERO = bytes(32)


def dispatch_hash(active, stage_id):
    return hashlib.sha256(active + struct.pack("<I", stage_id) + BIND_ZERO).digest()


def chunk_slice(abs_start, length):
    for chunk_start, chunk in shuffled_chunks:
        chunk_end = chunk_start + len(chunk)
        if abs_start >= chunk_start and (abs_start + length) <= chunk_end:
            return chunk_start_to_id[chunk_start], abs_start - chunk_start
    raise RuntimeError("unable to map source slice to a single chunk")


def add_rule(rules, active, stage_id, action_type, arg0, arg1, arg2, chunk_id):
    rules.append((dispatch_hash(active, stage_id), action_type, arg0, arg1, arg2, chunk_id))


seed_idx = (digest[0] + digest[7] * 3 + digest[31]) % len(data)
left = seed_idx
right = seed_idx
active = data[left:right + 1]
stage_id = INITIAL_STAGE_ID

real_rules = []
action_counts = {
    0: 0,
    1: 0,
    2: 0,
    3: 0,
    4: 0,
    5: 0,
}

while left > 0 or right < (len(data) - 1):
    can_prepend = left
    can_append = (len(data) - 1) - right

    use_prepend = bool(rng.getrandbits(1))
    if use_prepend and can_prepend == 0:
        use_prepend = False
    if (not use_prepend) and can_append == 0:
        use_prepend = True

    if use_prepend:
        total = rng.randint(1, min(10, can_prepend))
        while total > 0:
            target_end = left
            take_end = target_end
            found = None
            for chunk_start, chunk in shuffled_chunks:
                chunk_end = chunk_start + len(chunk)
                if (target_end - 1) >= chunk_start and (target_end - 1) < chunk_end:
                    found = (chunk_start, len(chunk), chunk_end)
                    break
            if found is None:
                raise RuntimeError("prepend chunk lookup failed")
            chunk_start, chunk_len, chunk_end = found
            take = min(total, take_end - chunk_start)
            abs_start = take_end - take
            chunk_id, chunk_off = chunk_slice(abs_start, take)
            add_rule(real_rules, active, stage_id, 0, chunk_off, take, 0, chunk_id)
            active = data[abs_start:take_end] + active
            left -= take
            total -= take
            action_counts[0] += 1
    else:
        total = rng.randint(1, min(10, can_append))
        cursor = right + 1
        while total > 0:
            found = None
            for chunk_start, chunk in shuffled_chunks:
                chunk_end = chunk_start + len(chunk)
                if cursor >= chunk_start and cursor < chunk_end:
                    found = (chunk_start, len(chunk), chunk_end)
                    break
            if found is None:
                raise RuntimeError("append chunk lookup failed")
            chunk_start, chunk_len, chunk_end = found
            take = min(total, chunk_end - cursor)
            chunk_id, chunk_off = chunk_slice(cursor, take)
            add_rule(real_rules, active, stage_id, 1, chunk_off, take, 0, chunk_id)
            active = active + data[cursor:cursor + take]
            cursor += take
            right += take
            total -= take
            action_counts[1] += 1

if active != data:
    raise RuntimeError("full reconstruction failed")

tail_start, tail_chunk = chunks[-1]
add_rule(real_rules, active, stage_id, 4, 0, ABI_VERSION, EXEC_STAGE_1, 0xFFFFFFFF)
stage_id = EXEC_STAGE_1
action_counts[4] += 1

add_rule(real_rules, active, stage_id, 4, 0, ABI_VERSION, EXEC_STAGE_2, 0xFFFFFFFF)
stage_id = EXEC_STAGE_2
action_counts[4] += 1

replace_chunk_start, replace_chunk = chunks[len(chunks) // 2]
donor_start, donor_chunk = chunks[0]
replace_len = min(len(replace_chunk), len(donor_chunk))
donor_id, donor_off = chunk_slice(donor_start, replace_len)
add_rule(real_rules, active, stage_id, 2, replace_chunk_start, replace_len, donor_off, donor_id)
active = active[:replace_chunk_start] + donor_chunk[:replace_len] + active[replace_chunk_start + replace_len:]
action_counts[2] += 1

add_rule(real_rules, active, stage_id, 3, tail_start, len(tail_chunk), 0, 0xFFFFFFFF)
active = active[:tail_start]
action_counts[3] += 1

terminal_expect_hash = hashlib.sha256(active).digest()
terminal = {
    "expect_stage_id": TERMINAL_STAGE_ID,
    "expect_token": INITIAL_TOKEN,
    "expect_io0": 0,
    "expect_io1": 0,
    "expect_active_len": len(active),
    "expect_active_sha256": terminal_expect_hash,
}

add_rule(real_rules, active, stage_id, 5, 0, 0, 0, 0xFFFFFFFF)
action_counts[5] += 1

seen_hashes = {h for h, _, _, _, _, _ in real_rules}
decoy_rules = []
target_decoys = len(real_rules) * DECOY_MULTIPLIER
while len(decoy_rules) < target_decoys:
    h = bytes(rng.getrandbits(8) for _ in range(32))
    if h in seen_hashes:
        continue
    seen_hashes.add(h)
    action_type = rng.randint(0, 5)
    if action_type in (0, 1):
        chunk_start, chunk = shuffled_chunks[rng.randrange(len(shuffled_chunks))]
        off = rng.randrange(len(chunk))
        length = rng.randint(1, len(chunk) - off)
        chunk_id = chunk_start_to_id[chunk_start]
        decoy_rules.append((h, action_type, off, length, 0, chunk_id))
    elif action_type == 2:
        chunk_start, chunk = shuffled_chunks[rng.randrange(len(shuffled_chunks))]
        off = rng.randrange(len(chunk))
        length = rng.randint(1, len(chunk) - off)
        chunk_id = chunk_start_to_id[chunk_start]
        dst = rng.randrange(len(data))
        decoy_rules.append((h, action_type, dst, length, off, chunk_id))
    elif action_type == 3:
        dst = rng.randrange(len(data))
        length = rng.randint(1, 10)
        decoy_rules.append((h, action_type, dst, length, 0, 0xFFFFFFFF))
    elif action_type == 4:
        decoy_rules.append((h, action_type, rng.randrange(8), ABI_VERSION, rng.randint(0, 7), 0xFFFFFFFF))
    else:
        decoy_rules.append((h, action_type, 0, 0, 0, 0xFFFFFFFF))

rules = real_rules + decoy_rules
rng.shuffle(rules)

if len({h for h, _, _, _, _, _ in rules}) != len(rules):
    raise RuntimeError("hash uniqueness invariant violated")

loader_max_steps = len(real_rules) + 32

with open(out_path, "w", encoding="ascii") as f:
    f.write("#ifndef INNER_CHUNKS_H\n")
    f.write("#define INNER_CHUNKS_H\n\n")
    f.write("#include <stdint.h>\n\n")
    f.write("#include \"loader_abi.h\"\n\n")
    f.write("typedef struct {\n")
    f.write("\tuint32_t start;\n")
    f.write("\tuint32_t len;\n")
    f.write("\tconst uint8_t* data;\n")
    f.write("} inner_chunk_t;\n\n")
    f.write(f"#define INNER_OBJ_LEN {len(data)}u\n")
    f.write(f"#define INNER_OBJ_CHUNK_COUNT {len(shuffled_chunks)}u\n")
    f.write(f"#define LOADER_RULE_COUNT {len(rules)}u\n")
    f.write(f"#define LOADER_REAL_RULE_COUNT {len(real_rules)}u\n")
    f.write(f"#define LOADER_DECOY_RULE_COUNT {len(decoy_rules)}u\n")
    f.write(f"#define LOADER_MAX_STEPS {loader_max_steps}u\n")
    f.write("#define LOADER_TERMINAL_COUNT 1u\n")
    f.write(f"#define LOADER_INITIAL_STAGE_ID {INITIAL_STAGE_ID}u\n")
    f.write(f"#define LOADER_INITIAL_TOKEN 0x{INITIAL_TOKEN:08x}u\n")
    f.write(f"#define LOADER_SEED_INDEX {seed_idx}u\n\n")

    for i, (_, chunk) in enumerate(shuffled_chunks):
        f.write(f"static const uint8_t inner_chunk_{i}[{len(chunk)}] = {{")
        for j, b in enumerate(chunk):
            if j % 12 == 0:
                f.write("\n\t")
            f.write(f"0x{b:02x}u")
            if j != len(chunk) - 1:
                f.write(", ")
        f.write("\n};\n\n")

    f.write("static const inner_chunk_t inner_chunks[INNER_OBJ_CHUNK_COUNT] = {\n")
    for i, (chunk_start, chunk) in enumerate(shuffled_chunks):
        f.write(f"\t{{ {chunk_start}u, {len(chunk)}u, inner_chunk_{i} }}")
        if i != len(shuffled_chunks) - 1:
            f.write(",")
        f.write("\n")
    f.write("};\n\n")

    f.write("static const loader_rule_t loader_rules[LOADER_RULE_COUNT] = {\n")
    for i, (h, action_type, arg0, arg1, arg2, chunk_id) in enumerate(rules):
        f.write("\t{")
        f.write("\n\t\t{")
        for j, b in enumerate(h):
            if j % 8 == 0:
                f.write("\n\t\t\t")
            f.write(f"0x{b:02x}u")
            if j != 31:
                f.write(", ")
        f.write("\n\t\t},")
        f.write(f"\n\t\t{action_type}u,\n\t\t0u,\n\t\t0u,\n\t\t{arg0}u,\n\t\t{arg1}u,\n\t\t{arg2}u,\n\t\t{chunk_id}u\n\t}}")
        if i != len(rules) - 1:
            f.write(", ")
        f.write("\n")
    f.write("};\n\n")

    f.write("static const loader_terminal_t loader_terminals[LOADER_TERMINAL_COUNT] = {\n")
    f.write("\t{\n")
    f.write(f"\t\t{terminal['expect_stage_id']}u,\n")
    f.write(f"\t\t0x{terminal['expect_token']:08x}u,\n")
    f.write(f"\t\t{terminal['expect_io0']}u,\n")
    f.write(f"\t\t{terminal['expect_io1']}u,\n")
    f.write(f"\t\t{terminal['expect_active_len']}u,\n")
    f.write("\t\t{")
    for i, b in enumerate(terminal["expect_active_sha256"]):
        if i % 8 == 0:
            f.write("\n\t\t\t")
        f.write(f"0x{b:02x}u")
        if i != 31:
            f.write(", ")
    f.write("\n\t\t}\n")
    f.write("\t}\n")
    f.write("\n};\n\n")

    f.write("#endif\n")

print(f"wrote {out_path}")
print(f"function=inner_entry offset={sym_off} size={sym_size}")
print(f"len={len(data)} chunks={len(shuffled_chunks)} real_rules={len(real_rules)} decoy_rules={len(decoy_rules)} total_rules={len(rules)}")
print(f"action_counts prepend={action_counts[0]} append={action_counts[1]} replace={action_counts[2]} remove={action_counts[3]} execute={action_counts[4]} terminal={action_counts[5]}")
