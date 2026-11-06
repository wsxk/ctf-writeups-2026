> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #72 的连续章节摘录；代码未执行。

## #72 【Game】共生（联机）

### 1. 题目信息
- **题目名称**：【Game】共生（联机）
- **题目类型**：MISC/REVERSE
- **最终 Flag**：`NepCTF{bcaff050dfd983a85c73ad969eded5fb6eea353117d582820c22ed182697bead}`

### 2. 题目分析
共生联机：公开 HTTP + UDP 双端。坑是 guest 如果复用 host 的 team_token，Auth 直接 DupTeam，后面全是 NotInGame——我第一版 online_flag 就栽在这。

### 3. 解题思路
guest **单独 register** 一个 bot-guest token → 双端 AUTH + PEER_JOINED → 开局 → 等到进度够再 RunComplete → claim。太早 RunComplete 会 TooEarly。

### 4. 解题过程
`python3 work/72/repro/proven_run.py`（或修好 token 的 `online_flag.py`）。HTTP `114.66.24.240:30888` UDP `:30885`。Flag：`NepCTF{bcaff050dfd983a85c73ad969eded5fb6eea353117d582820c22ed182697bead}`。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/72/repro/proven_run.py`
```python
#!/usr/bin/env python3
"""Proven dual-client #72 flag claim (from agent a398682debc2dac28 SUCCESS run)."""
import json, os, socket, struct, time, urllib.error, urllib.request

HOST, PORT = "114.66.24.240", 30885
HTTP = "http://114.66.24.240:30888"
TOKEN = "1rGLoJ_jPij-eVUqQuf4I"
MAGIC = b"JH"
REPRO = "/home/catcatyu/nepctf/work/72/repro"
os.makedirs(REPRO, exist_ok=True)

def post(path, body):
    req = urllib.request.Request(HTTP + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "null")

def hdr(mt, pid, seq):
    return MAGIC + bytes([mt, pid]) + struct.pack("<I", seq)

class C:
    def __init__(self, n):
        self.n = n
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(("0.0.0.0", 0))
        self.s.settimeout(0.12)
        self.seq = 1
        self.pid = 255
        self.room = 0
        self.rsid = 0
    def close(self):
        self.s.close()
    def send(self, mt, pid, payload=b"", note=""):
        pkt = hdr(mt, pid, self.seq) + payload
        self.seq += 1
        self.s.sendto(pkt, (HOST, PORT))
        if note:
            print(f"[{self.n}] TX {note}", flush=True)
    def pump(self, t=0.5):
        end = time.time() + t
        runs = []
        while time.time() < end:
            try:
                d = self.s.recvfrom(4096)[0]
            except socket.timeout:
                continue
            mt = d[2]
            p = d[8:]
            if mt == 24 and len(p) >= 12:
                req, room, res, rpid, rsid = struct.unpack_from("<IHBBI", p, 0)
                if res == 0:
                    self.room, self.pid, self.rsid = room, rpid, rsid
            if mt == 26 and len(p) >= 1:
                print(f"[{self.n}] RUN res={p[0]}", flush=True)
                runs.append(p[0])
            if mt == 25 and len(p) >= 1:
                print(f"[{self.n}] AUTH res={p[0]}", flush=True)
            if mt == 17:
                print(f"[{self.n}] PEER_JOINED", flush=True)
        return runs

def ctrl(cli, pid, cmd, start, cseq, ch):
    cli.send(5, pid, struct.pack("<II", start, cseq) + bytes([cmd, ch, 0, 0]), f"cmd{cmd} ch{ch} st{start}")

def main():
    _, hreg = post("/api/v1/register", {"team_token": TOKEN})
    _, greg = post("/api/v1/register", {"team_token": "bot-guest-" + str(int(time.time()))})
    hs, hc = bytes.fromhex(hreg["session_id"]), bytes.fromhex(hreg["credential"])
    gs, gc = bytes.fromhex(greg["session_id"]), bytes.fromhex(greg["credential"])
    print("sessions", hreg["session_id"][:8], greg["session_id"][:8], flush=True)
    H, G = C("H"), C("G")
    try:
        H.send(1, 255); G.send(1, 255); H.pump(0.6); G.pump(0.6)
        for i in range(20):
            H.send(6, 255, struct.pack("<IHH", i + 1, 0, 0), "create")
            H.pump(1.0)
            if H.room >= 1000:
                break
            time.sleep(2)
        print("room", H.room, H.pid, flush=True)
        assert H.room >= 1000
        G.send(7, 255, struct.pack("<IHH", 1, H.room, 0), "join")
        for _ in range(25):
            H.pump(0.1); G.pump(0.1)
        print("guest", G.room, G.pid, flush=True)
        H.send(8, H.pid, hs + hc, "authH"); H.pump(0.8)
        G.send(8, G.pid, gs + gc, "authG"); G.pump(0.8)
        for _ in range(8):
            H.send(3, H.pid); G.send(3, G.pid); H.pump(0.2); G.pump(0.2)
        ctrl(H, H.pid, 1, 1, 1, 0); H.pump(0.2); G.pump(0.4)
        ctrl(H, H.pid, 2, 1, 2, 0)
        for _ in range(12):
            H.pump(0.1); G.pump(0.1)
        ctrl(G, G.pid, 3, 1, 1, 0)
        for _ in range(12):
            H.pump(0.1); G.pump(0.1)
        print("status", post("/api/v1/status", {"session_id": hreg["session_id"], "credential": hreg["credential"]}), flush=True)
        t0 = time.time(); tick = 0; hist = {}
        while time.time() - t0 < 120:
            tick += 10
            payload = bytearray(84)
            struct.pack_into("<III", payload, 0, 1, tick, tick)
            struct.pack_into("<ff", payload, 12, float(tick % 50), 0.0)
            H.send(4, H.pid, bytes(payload))
            H.send(3, H.pid); G.send(3, G.pid)
            H.pump(0.03); G.pump(0.03)
            elapsed = time.time() - t0
            if tick % 200 == 0:
                for start, comp in [(1, tick), (1, max(2, int(elapsed * 10))), (1, max(2, int(elapsed))), (1, 3600), (1, tick * 2), (1, 1400)]:
                    H.send(9, H.pid, struct.pack("<II", start, comp), f"run s={start} c={comp} e={elapsed:.1f}")
                    for r in H.pump(0.7):
                        hist[r] = hist.get(r, 0) + 1
                        if r == 0:
                            print("SUCCESS", start, comp, tick, elapsed, flush=True)
                            print(post("/api/v1/status", {"session_id": hreg["session_id"], "credential": hreg["credential"]}), flush=True)
                            c, d = post("/api/v1/claim", {"session_id": hreg["session_id"], "credential": hreg["credential"]})
                            print("claim", c, d, flush=True)
                            if isinstance(d, dict) and d.get("flag"):
                                flag = d["flag"]
                                open(os.path.join(REPRO, "got_flag.txt"), "w").write(flag + "\n")
                                open("/home/catcatyu/nepctf/work/72/flag.txt", "w").write(flag + "\n")
                                print("FLAG", flag, flush=True)
                            return 0
        print("hist", hist, flush=True)
        print("status", post("/api/v1/status", {"session_id": hreg["session_id"], "credential": hreg["credential"]}), flush=True)
        print("claim", post("/api/v1/claim", {"session_id": hreg["session_id"], "credential": hreg["credential"]}), flush=True)
        return 2
    finally:
        H.close(); G.close()

if __name__ == "__main__":
    raise SystemExit(main() or 0)
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

