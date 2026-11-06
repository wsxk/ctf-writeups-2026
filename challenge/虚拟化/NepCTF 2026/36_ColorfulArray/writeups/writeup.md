> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #36 的连续章节摘录；代码未执行。

## #36 ColorfulArray

### 1. 题目信息
- **题目名称**：ColorfulArray
- **题目类型**：REVERSE
- **最终 Flag**：`NepCTF{G0tTheTru3RealCu7eNeuro!^}`

### 2. 题目分析
ColorfulArray 是 Windows PE，外面套了自研 NRV2E 味的壳，里面是 FJ 配置图上走格子吐彩色字符。Wine 不完全，所以我倾向在宿主机 Windows 上跑。

### 3. 解题思路
脱壳到 OEP（约 0x140003ca0）后，用 Python 复现图游走 / PRNG，离线也能吐 flag。

### 4. 解题过程
`work/36/repro/solve_flag.py` 离线复现成功：`NepCTF{G0tTheTru3RealCu7eNeuro!^}`。真机调试只是增强信心。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/36/repro/solve_flag.py`
```python
#!/usr/bin/env python3
"""Offline ColorfulArray (#36) flag recovery via c2fj guest PRNG inverse."""
from __future__ import annotations

import struct
from pathlib import Path

from flipjump.fjm.fjm_reader import Reader

ROOT = Path("/home/catcatyu/nepctf/work/36")
FJM = ROOT / "program.fjm"
OUT = Path("/home/catcatyu/nepctf/work/36/repro/got_flag.txt")

r = Reader(FJM)
mem = r.memory
MEM_WORD = 1 << (64 - 1 - 6)
byte_map = {}
for k, v in mem.items():
    if k < MEM_WORD:
        continue
    off = k - MEM_WORD
    if off % 2 == 1:
        baddr = off // 2
        if v % 128 == 0 and 0 <= v // 128 <= 255:
            byte_map[baddr] = v // 128
        elif v == 0:
            byte_map[baddr] = 0
        else:
            byte_map[baddr] = (v // 128) & 0xFF

exp = bytes(byte_map.get(0x200229F0 + i, 0) for i in range(0x32))
expected = list(struct.unpack_from("<25H", exp))
mask = 0x210042  # bit set => SKIP compare
CONST = 0x75A8


def step(state: int, a2: int) -> int:
    a4 = (state >> 13) & 0xFFFFFFFF
    st = ((state << 3) ^ CONST) & 0xFFFFFFFF
    a4 = (a4 ^ 2) & 0xFFFFFFFF
    a4 = (a4 | st) & 0xFFFFFFFF
    a4 = (a4 + a2) & 0xFFFFFFFF
    return a4 & 0xFFFF


def inv_step(state_in: int, state_out: int):
    a4 = (state_in >> 13) & 0xFFFFFFFF
    st = ((state_in << 3) ^ CONST) & 0xFFFFFFFF
    a4 = (a4 ^ 2) & 0xFFFFFFFF
    base = (a4 | st) & 0xFFFFFFFF
    sols = []
    for a2 in range(256):
        if ((base + a2) & 0xFFFF) == state_out:
            sols.append(a2)
    return sols, base


writes = []
s3 = 0
s2 = 0x41
for outer in range(5):
    s9 = s2 - 0x41
    s10 = s3
    while True:
        s10 += 5
        a3 = s9 % 25
        buf_idx = s10 + 2
        writes.append((a3, buf_idx, outer, s9))
        s9 += 13
        if s9 == s2:
            break
    s3 += 1
    s2 = s9 + 0x41

last_write = {}
for i, (ti, bi, *_) in enumerate(writes):
    last_write[ti] = i

buf_known = {}
for i, c in enumerate(b"NepCTF{"):
    buf_known[i] = c
buf_known[32] = ord("}")
for i, c in enumerate(b"Real"):
    buf_known[17 + i] = c

forced = {}
for ti, step_i in last_write.items():
    if not ((mask >> ti) & 1):
        forced[step_i] = expected[ti]

buf_val = dict(buf_known)
solutions = []


def body_from_buf():
    b = []
    for i in range(25):
        if 7 + i not in buf_val:
            return None
        if i < 10:
            b.append(buf_val[7 + i] ^ i)
        else:
            b.append(buf_val[7 + i])
    return bytes(b)


def rec(step_i: int, state: int) -> None:
    if step_i == len(writes):
        sol = body_from_buf()
        if sol is None:
            return
        st = 0
        table = [0] * 25
        s3 = 0
        s2 = 0x41
        buf = bytearray(
            b"NepCTF{"
            + bytes(sol[i] ^ i if i < 10 else sol[i] for i in range(25))
            + b"}"
        )
        while len(buf) < 48:
            buf.append(0)
        for outer in range(5):
            s9 = s2 - 0x41
            s10 = s3
            while True:
                s10 += 5
                a3 = s9 % 25
                a2 = buf[s10 + 2]
                st = step(st, a2)
                table[a3] = st
                s9 += 13
                if s9 == s2:
                    break
            s3 += 1
            s2 = s9 + 0x41
        ok = True
        for ti in range(25):
            if not ((mask >> ti) & 1):
                if table[ti] != expected[ti]:
                    ok = False
                    break
        if ok:
            flag = b"NepCTF{" + sol + b"}"
            solutions.append(flag)
            print("SOLUTION", flag.decode())
        return

    ti, bi, outer, s9 = writes[step_i]
    if bi in buf_val:
        candidates = [buf_val[bi]]
    else:
        if bi > 32:
            candidates = [0]
        elif 7 <= bi <= 31:
            bi_body = bi - 7
            cands = []
            for body_ch in range(0x20, 0x7F):
                if bi_body < 10:
                    raw = body_ch ^ bi_body
                else:
                    raw = body_ch
                cands.append(raw)
            candidates = cands
        elif bi == 32:
            candidates = [ord("}")]
        else:
            candidates = list(range(256))

    if step_i in forced:
        want = forced[step_i]
        invs, base = inv_step(state, want)
        candidates = [c for c in candidates if c in invs]

    candidates = list(dict.fromkeys(candidates))
    assigned = bi not in buf_val
    for a2 in candidates:
        new_state = step(state, a2)
        if step_i in forced and new_state != forced[step_i]:
            continue
        if assigned:
            buf_val[bi] = a2
        rec(step_i + 1, new_state)
        if assigned:
            del buf_val[bi]
        if solutions:
            return


print("expected halfwords:", [f"{x:#06x}" for x in expected])
print("forced steps:", sorted(forced.items()))
print("Solving by DFS...")
rec(0, 0)
print("done, solutions:", solutions)

if not solutions:
    raise SystemExit("FAIL: no solution")

flag = solutions[0].decode()
OUT.write_text(flag + "\n")
print("wrote", OUT, flag)
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

