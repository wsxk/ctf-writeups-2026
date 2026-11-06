import os
import re
import struct
import subprocess
import sys

PACK_NAME = sys.argv[1]


def parse_load_segments(binary_path: str) -> list[tuple[int, int, int]]:
    out = subprocess.check_output(["readelf", "-W", "-l", binary_path], text=True)
    segments: list[tuple[int, int, int]] = []
    for line in out.splitlines():
        parts = line.split()
        if not parts or parts[0] != "LOAD" or len(parts) < 6:
            continue
        offset = int(parts[1], 16)
        vaddr = int(parts[2], 16)
        filesz = int(parts[4], 16)
        segments.append((vaddr, vaddr + filesz, offset))
    if not segments:
        raise RuntimeError("No LOAD segments found")
    return segments


def vaddr_to_file_offset(vaddr: int, load_segments: list[tuple[int, int, int]]) -> int:
    for seg_start, seg_end, file_offset in load_segments:
        if seg_start <= vaddr < seg_end:
            return file_offset + (vaddr - seg_start)
    raise RuntimeError(f"Address 0x{vaddr:x} not in any file-backed LOAD segment")


def parse_segment_addresses_from_symbols(binary_path: str, needed_segments: int) -> list[int]:
    out = subprocess.check_output(["nm", "-n", binary_path], text=True)
    by_index: dict[int, int] = {}
    for line in out.splitlines():
        match = re.match(r"^([0-9a-fA-F]+)\s+\S\s+segment(\d+)$", line.strip())
        if match is None:
            continue
        idx = int(match.group(2))
        by_index[idx] = int(match.group(1), 16)

    missing = [i for i in range(needed_segments) if i not in by_index]
    if missing:
        raise RuntimeError(f"Missing segment symbols in nm output: {missing}")

    return [by_index[i] for i in range(needed_segments)]


generated_code_module_name = f"generated_code_{PACK_NAME}"
generated_code_module = __import__(generated_code_module_name)

sboxbes = []
cur_sboxb = generated_code_module.SBOXB
for i in range(generated_code_module.NSEGMENTS):
    sboxb = cur_sboxb.copy()
    generated_code_module.PREPARATION_FUNCS[i](sboxb)
    sboxbes.append(sboxb)
    cur_sboxb = sboxb

needed_segments = generated_code_module.NSEGMENTS + 2
addresses = parse_segment_addresses_from_symbols(
    f"unpacked_{PACK_NAME}", needed_segments
)
for i, addr in enumerate(addresses):
    print(f"segment{i}: {hex(addr)}")

binary = open(f"unpacked_{PACK_NAME}", "rb").read()
inputdata = open(f"secret_input_{PACK_NAME}", "rb").read()
load_segments = parse_load_segments(f"unpacked_{PACK_NAME}")

segmentdata = []
for i in range(generated_code_module.NSEGMENTS + 1):
    start = addresses[i]
    end = addresses[i + 1]
    start_off = vaddr_to_file_offset(start, load_segments)
    end_off = vaddr_to_file_offset(end, load_segments)
    segmentdata.append((start, bytearray(binary[start_off:end_off])))

for i in range(generated_code_module.NSEGMENTS - 1, -1, -1):
    sboxb = sboxbes[i]
    sboxbinv = [0] * 256
    for j in range(256):
        sboxbinv[sboxb[j]] = j
    encrypt_func = generated_code_module.ENCRYPT_FUNCS[i]
    input_value = struct.unpack("H", inputdata[i * 2 : (i + 1) * 2])[0]
    encrypt_func(segmentdata, input_value, sboxbinv)

newbinary = bytearray(binary)
for i in range(generated_code_module.NSEGMENTS + 1):
    start = addresses[i]
    end = addresses[i + 1]
    start_off = vaddr_to_file_offset(start, load_segments)
    end_off = vaddr_to_file_offset(end, load_segments)
    newbinary[start_off:end_off] = segmentdata[i][1]

with open(f"packed_{PACK_NAME}", "wb") as f:
    f.write(newbinary)

os.chmod(f"packed_{PACK_NAME}", 0o755)
