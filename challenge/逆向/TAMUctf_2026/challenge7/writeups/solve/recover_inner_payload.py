import hashlib
import struct
import sys

from elftools.elf.elffile import ELFFile


bin_path = sys.argv[1] if len(sys.argv) > 1 else "build/challenge7"
out_path = sys.argv[2] if len(sys.argv) > 2 else "solve/inner_stage_payload.bin"

f = open(bin_path, "rb")
elf = ELFFile(f)
ro = elf.get_section_by_name(".rodata")
text = elf.get_section_by_name(".text")
data_rel_ro = elf.get_section_by_name(".data.rel.ro")
rela_dyn = elf.get_section_by_name(".rela.dyn")

ro_b = ro.data()
text_b = text.data()
drr_b = data_rel_ro.data()

sections = []
for s in elf.iter_sections():
    if s["sh_flags"] & 0x2:
        sections.append((s["sh_addr"], s["sh_addr"] + s["sh_size"], s.data()))


def read_vaddr(addr, size):
    for lo, hi, blob in sections:
        if lo <= addr and addr + size <= hi:
            off = addr - lo
            return blob[off:off + size]
    return None


def find_chunk_table():
    lo = data_rel_ro["sh_addr"]
    hi = lo + data_rel_ro["sh_size"]
    rels = []
    for r in rela_dyn.iter_relocations():
        off = r["r_offset"]
        if lo <= off < hi:
            rels.append((off, r["r_addend"]))
    rels.sort()

    best = []
    cur = []
    for rel in rels:
        if not cur or rel[0] == cur[-1][0] + 16:
            cur.append(rel)
        else:
            if len(cur) > len(best):
                best = cur
            cur = [rel]
    if len(cur) > len(best):
        best = cur

    chunks = []
    for ptr_off, ptr_addr in best:
        entry_off = ptr_off - lo - 8
        start = struct.unpack_from("<I", drr_b, entry_off)[0]
        size = struct.unpack_from("<I", drr_b, entry_off + 4)[0]
        data = read_vaddr(ptr_addr, size)
        if data is None:
            break
        chunks.append((start, size, data))

    return chunks


chunks = find_chunk_table()
chunk_count = len(chunks)
inner_len = max(start + size for start, size, _ in chunks)


RULE_SIZE = 52


def find_rule_table():
    best_off = 0
    best_n = 0

    for off in range(0, len(ro_b) - RULE_SIZE):
        n = 0
        while off + (n + 1) * RULE_SIZE <= len(ro_b):
            rec = ro_b[off + n * RULE_SIZE:off + (n + 1) * RULE_SIZE]
            action = rec[32]
            cid = struct.unpack_from("<I", rec, 48)[0]
            if action > 5:
                break
            if rec[33] != 0 or rec[34] != 0 or rec[35] != 0:
                break
            if cid != 0xFFFFFFFF and cid >= chunk_count:
                break
            n += 1
        if n > best_n:
            best_n = n
            best_off = off

    rules = []
    for i in range(best_n):
        rec = ro_b[best_off + i * RULE_SIZE:best_off + (i + 1) * RULE_SIZE]
        rules.append((
            rec[:32],
            rec[32],
            struct.unpack_from("<I", rec, 36)[0],
            struct.unpack_from("<I", rec, 40)[0],
            struct.unpack_from("<I", rec, 44)[0],
            struct.unpack_from("<I", rec, 48)[0],
        ))

    return rules


rules = find_rule_table()
rule_by_hash = {h: (a, a0, a1, a2, cid) for h, a, a0, a1, a2, cid in rules}
rule_hashes = set(rule_by_hash)


def chunk_slice_materialized(bind, chunk_id, off, size):
    if chunk_id >= chunk_count or size == 0:
        return None
    _, clen, cdata = chunks[chunk_id]
    if off > clen or size > clen - off:
        return None
    src = cdata[off:off + size]
    return bytes(src[i] ^ bind[(off + i) & 31] for i in range(size))


def decode_full_payload(bind):
    out = bytearray(inner_len)
    for start, size, cdata in chunks:
        for i in range(size):
            out[start + i] = cdata[i] ^ bind[i & 31]
    return bytes(out)


def simulate(bind, payload, seed_idx):
    active = bytearray([payload[seed_idx]])
    stage = 0
    first_exec = None

    for step in range(5000):
        digest = hashlib.sha256(active + stage.to_bytes(4, "little") + bind).digest()
        rule = rule_by_hash.get(digest)
        if rule is None:
            return None

        action, arg0, arg1, arg2, chunk_id = rule

        if action == 0:
            data = chunk_slice_materialized(bind, chunk_id, arg0, arg1)
            if data is None:
                return None
            active = bytearray(data + active)
        elif action == 1:
            data = chunk_slice_materialized(bind, chunk_id, arg0, arg1)
            if data is None:
                return None
            active.extend(data)
        elif action == 2:
            if arg1 == 0 or arg0 > len(active) or arg1 > len(active) - arg0:
                return None
            data = chunk_slice_materialized(bind, chunk_id, arg2, arg1)
            if data is None:
                return None
            active[arg0:arg0 + arg1] = data
        elif action == 3:
            if arg1 == 0 or arg0 > len(active) or arg1 > len(active) - arg0:
                return None
            del active[arg0:arg0 + arg1]
        elif action == 4:
            if arg0 >= len(active) or arg1 != 1:
                return None
            if first_exec is None:
                first_exec = bytes(active)
            stage = arg2
        elif action == 5:
            return first_exec if first_exec is not None else bytes(active)
        else:
            return None

    return None


text_sha = hashlib.sha256(text_b).digest()

for off in range(0, len(ro_b) - 31):
    expected = ro_b[off:off + 32]
    bind = bytes(text_sha[i] ^ expected[i] for i in range(32))

    has_step0 = False
    for b in range(256):
        d = hashlib.sha256(bytes([b]) + (0).to_bytes(4, "little") + bind).digest()
        if d in rule_hashes:
            has_step0 = True
            break
    if not has_step0:
        continue

    payload = decode_full_payload(bind)
    for seed_idx in range(inner_len):
        recovered = simulate(bind, payload, seed_idx)
        if recovered is not None:
            with open(out_path, "wb") as wf:
                wf.write(recovered)
            with open(out_path + ".full.bin", "wb") as wf:
                wf.write(payload)
            print(f"binary: {bin_path}")
            print(f"chunk_count: {chunk_count}")
            print(f"rule_count: {len(rules)}")
            print(f"inner_len: {inner_len}")
            print(f"seed_idx: {seed_idx}")
            print(f"bind_candidate_rodata_off: 0x{off:x}")
            print(f"stage_payload_len: {len(recovered)}")
            print(f"wrote: {out_path}")
            print(f"wrote: {out_path}.full.bin")
            f.close()
            sys.exit(0)

print("failed to recover payload")
f.close()
sys.exit(1)
