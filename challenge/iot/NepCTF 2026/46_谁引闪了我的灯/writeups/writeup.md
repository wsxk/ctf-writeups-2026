> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #46 的连续章节摘录；代码未执行。

## #46 谁引闪了我的灯

### 1. 题目信息
- **题目名称**：谁引闪了我的灯
- **题目类型**：MISC
- **最终 Flag**：`NepCTF{5bf7d6ca3d718c33301a52e5f45909b8}`

### 2. 题目分析
谁引闪了我的灯：ESP32 / Godox 引闪协议，16 字节帧；配图 comment 里藏了 channel / id。

### 3. 解题思路
按 `55 | G | ID | type | payload | CS` 组帧，整帧 MD5（去空格）就是 flag 内容。

### 4. 解题过程
组出 `55 01 13 01 01 ... 6B` 那帧 → md5 → `NepCTF{5bf7d6ca3d718c33301a52e5f45909b8}`。脚本 `work/46/exp/solve_godox_md5.py`。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/46/exp/solve_godox_md5.py`
```python
#!/usr/bin/env python3
"""#46 谁引闪了我的灯
Frame: 55 | group | id | type | payload... | checksum
ch18 id19 -> group=1 id=19 type=1 payload=01
55 01 13 01 01 00 00 00 00 00 00 00 00 00 00 6B
flag = NepCTF{md5(hex without spaces lowercase)}
"""
import hashlib
frame = bytes([0x55, 0x01, 0x13, 0x01, 0x01] + [0]*10)
# fix checksum
frame = bytearray(frame)
# 16 bytes: last is CS
cs = sum(frame[:15]) & 0xFF
# rebuild properly
buf = [0x55, 0x01, 0x13, 0x01, 0x01] + [0]*10  # 15 bytes then CS
assert len(buf)==15
buf.append(sum(buf)&0xFF)
hexstr = ''.join(f'{b:02X}' for b in buf)
print('frame', hexstr)
print('flag', 'NepCTF{' + hashlib.md5(hexstr.encode()).hexdigest() + '}')
# also try lowercase hex
hexstr_l = ''.join(f'{b:02x}' for b in buf)
print('flag_lowerhex', 'NepCTF{' + hashlib.md5(hexstr_l.encode()).hexdigest() + '}')
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

