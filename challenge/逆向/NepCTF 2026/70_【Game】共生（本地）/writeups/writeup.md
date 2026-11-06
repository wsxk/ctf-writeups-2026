> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #70 的连续章节摘录；代码未执行。

## #70 【Game】共生（本地）

### 1. 题目信息
- **题目名称**：【Game】共生（本地）
- **题目类型**：MISC/REVERSE
- **最终 Flag**：`NepCTF{24743deb446548c5e811f290237a60ba692a788e8264323169b5cb793858de21}`

### 2. 题目分析
共生本地：Unity IL2CPP，BuildCompletionCode 相关；Scene3 有 TP 之类捷径，但 flag 要自然事件 Mix。

### 3. 解题思路
**natural 12 事件**序列，不要 allcp 作弊路径（那条过不了正确哈希）。

### 4. 解题过程
`python3 work/70/exp/local_flag.py --events natural` → SHA256 形式 flag：`NepCTF{24743deb446548c5e811f290237a60ba692a788e8264323169b5cb793858de21}`。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/70/exp/local_flag.py`
```python
#!/usr/bin/env python3
"""NepCTF 2026 #70 共生（本地） — offline flag builder (Frida-verified)."""
from __future__ import annotations
import argparse
import hashlib
import sys

MASK64 = (1 << 64) - 1
INITIAL_A = 0x243F6A8885A308D3
INITIAL_B = 0x13198A2E03707344
MIX_A = 0xD6E8FEB86659FD93
MIX_B = 0xA0761D6478BD642F
MIX_C = 0xE7037ED1A0B428DB
GOLDEN = 0x9E3779B97F4A7C15


def rotl(v: int, n: int) -> int:
    n &= 63
    return ((v << n) | (v >> (64 - n))) & MASK64


def mix(a: int, b: int, cnt: int, code: int) -> tuple[int, int, int]:
    code &= 0xFFFFFFFF
    cnt = (cnt + 1) & 0xFFFFFFFF
    t = (((a >> 2) + GOLDEN) + (((a << 6) & MASK64) + code)) & MASK64
    a = (a ^ t) & MASK64
    a = (rotl(a, (code % 23) + 7) * MIX_A) & MASK64
    b = (b + (((code * MIX_B) & MASK64) ^ a)) & MASK64
    b = (rotl(b, (cnt % 29) + 11) * MIX_C) & MASK64
    return a, b, cnt


def build(token: str, events: list[int]) -> tuple[str, str]:
    a, b, c = INITIAL_A, INITIAL_B, 0
    for e in events:
        a, b, c = mix(a, b, c, e)
    payload = f"j07-local-v2|{token}|{a:016x}|{b:016x}|{c}"
    flag = f"NepCTF{{{hashlib.sha256(payload.encode()).hexdigest()}}}"
    return flag, payload


# Scene1/2/3 win = 0x200+idx; StorePoint = ((sceneIdx+0x10)<<4)+cpIdx
# StorePoints per scene (data.unity3d level2/3/4 = Scene1/2/3), sorted by position.x:
#   S1: 1 @x≈-7.8 → 0x100
#   S2: 3 @x≈-9.3(elev),5.3,28.8 → 0x110..0x112
#   S3: 6 @x≈-16,66,124,176,240.6,306.5 → 0x120..0x125
# Scene3 teleports (data.unity3d):
#   TpStart1@28.4 → TpEnd1@61.9  (no CP skipped)
#   TpStart2@135.6 → TpEnd2@185.4  skips StorePoint (3) @176 → 0x123
# Platform AC path = natural play with TP2 (skip 0x123), not allcp.
DEFAULT_WINS = [0x200, 0x201, 0x202]
DEFAULT_ALLCP = [
    0x100, 0x200,
    0x110, 0x111, 0x112, 0x201,
    0x120, 0x121, 0x122, 0x123, 0x124, 0x125, 0x202,
]
# Platform-accepted (2026-07-19): natural L→R + TP2 skip 0x123
DEFAULT_NATURAL = [
    0x100, 0x200,
    0x110, 0x111, 0x112, 0x201,
    0x120, 0x121, 0x122, 0x124, 0x125, 0x202,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=open("/home/catcatyu/nepctf/work/70/team_token.txt").read().strip())
    ap.add_argument("--events", default="natural", help="natural|allcp|wins|empty|firstcp|comma hex list")
    args = ap.parse_args()
    if args.events == "wins":
        ev = DEFAULT_WINS
    elif args.events == "empty":
        ev = []
    elif args.events == "firstcp":
        ev = [0x100, 0x200, 0x110, 0x201, 0x120, 0x202]
    elif args.events == "allcp":
        ev = DEFAULT_ALLCP
    elif args.events == "natural":
        ev = DEFAULT_NATURAL
    else:
        ev = [int(x, 0) for x in args.events.split(",") if x]
    flag, payload = build(args.token, ev)
    print(payload)
    print(flag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

