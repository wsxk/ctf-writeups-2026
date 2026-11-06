> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #37 的连续章节摘录；代码未执行。

## #37 UnknownFirmware

### 1. 题目信息
- **题目名称**：UnknownFirmware
- **题目类型**：REVERSE/MISC
- **最终 Flag**：`NepCTF{U_Have_Dec0mpiled_Telink_FirmWareWooooW}`

### 2. 题目分析
UnknownFirmware：Telink / KNLT 一类固件，显示缓冲可以当位图抠。

### 3. 解题思路
多试几种宽高和 1bpp/2bpp 排布，扫二维码。

### 4. 解题过程
`work/37/exp/solve_telink_qr.py` 出 QR 文本 `NepCTF{U_Have_Dec0mpiled_Telink_FirmWareWooooW}`，提交。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/37/exp/solve_telink_qr.py`
```python
#!/usr/bin/env python3
"""#37 UnknownFirmware — Telink KNLT e-paper buffer -> QR
Session 95dd4278: magic KNLT/TLNK, try bitplanes + widths, QR decode.
Flag: NepCTF{U_Have_Dec0mpiled_Telink_FirmWareWooooW}
"""
import sys
from pathlib import Path
try:
    from pyzbar.pyzbar import decode as zbar_decode
    from PIL import Image
except ImportError:
    zbar_decode = None
    from PIL import Image

def find_knlt(data: bytes):
    return data.find(b'KNLT'), data.find(b'TLNK')

def bits_to_img(bits, w, h):
    import numpy as np
    arr = (1 - bits[:w*h].reshape(h,w)) * 255
    return Image.fromarray(arr.astype('uint8'), 'L')

def main(path):
    data = Path(path).read_bytes()
    print('KNLT', data.find(b'KNLT'), 'TLNK', data.find(b'TLNK'))
    # Heuristic: scan regions as 1-bit images with various widths
    import numpy as np
    # try after offset skip192 as in session hit skip192_41x90
    for skip in [0, 192, 256, 512, 1024]:
        blob = data[skip:]
        bits = np.unpackbits(np.frombuffer(blob[:500000], dtype=np.uint8))
        for w in range(40, 300):
            h = len(bits) // w
            if h < 40 or h > 400: continue
            # only try a few heights near square / known
            for hh in [w, 90, 122, 128, 250, min(h, 200)]:
                if hh*w > len(bits): continue
                img = bits_to_img(bits, w, hh)
                if zbar_decode:
                    res = zbar_decode(img)
                    if res:
                        print('HIT', f'skip{skip}_{w}x{hh}', res[0].data)
                        return res[0].data.decode()
    print('no QR found with heuristic; refine offsets from session')
    return None

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv)>1 else 'firmware.bin')
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

