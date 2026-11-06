#!/usr/bin/env python3
from pathlib import Path
from struct import unpack_from

BIN = Path('chimera_mirror').read_bytes()
MASK = 0xffffffff

def u32(x): return x & MASK
def xs(x):
    x=u32(x)
    x=u32((x << 13) ^ x)
    x=u32(x ^ (x >> 17))
    return u32(x ^ (x << 5))
def rol(x,n):
    n &= 31; x=u32(x)
    return u32((x<<n) | (x>>((-n)&31)))
def ror(x,n): return rol(x,-n)

def outer_code():
    enc=BIN[0x20c0:0x20c0+0x720]
    out=bytearray(len(enc)); state=0x7b3a7bd4; key=0x61
    for i,c in enumerate(enc):
        state=xs(state + 3*i + 0xa5a5a5a5)
        out[i]=c ^ key ^ ((state >> ((i&3)*8))&0xff)
        key=(key+0x1d)&0xff
    return bytes(out)

OUTER_NAMES={0xbf:'MOV',0x95:'ROLX',0xb7:'MIX',0xdc:'GUARD',0xef:'LEN',0xcd:'CHECK',0x91:'AND',0xa3:'RET'}
INNER_NAMES={0x0a:'MOV',0x0f:'ADD',0x21:'OK',0x26:'XOR3',0x30:'IN',0x59:'ROLADD',0x71:'ROL',0x76:'MIX',0x7d:'EQ',0x93:'SUB',0xa7:'ROR',0xab:'XOR',0xd2:'MUL'}

def ins_fields(x):
    return x[0],x[1]&7,x[2]&7,x[3]&31,int.from_bytes(x[4:8],'little')

def dump_outer():
    code=outer_code()
    for pc in range(0,len(code),8):
        op,a,b,c,imm=ins_fields(code[pc:pc+8])
        print(f'{pc//8:03}: {OUTER_NAMES.get(op,hex(op)):5} r{a}, r{b}, {c:02}, {imm:#010x}')

def inner_meta(i):
    ln=unpack_from('<H',BIN,0x29c0+2*i)[0]
    off=unpack_from('<H',BIN,0x2ac0+2*i)[0]
    seed=unpack_from('<I',BIN,0x27e0+4*i)[0]
    return off,ln,seed

def inner_code(i):
    off,ln,seed=inner_meta(i)
    enc=BIN[0x2bc0+off:0x2bc0+off+ln]
    out=bytearray(ln); state=u32(((i+1)*0x45d9f3b) ^ ((i+1)*0x9e3779b9) ^ seed ^ rol(0x7b805a1f,(i*7)%31))
    key=u32(i*-0x7d)
    for j,c in enumerate(enc):
        state=xs(state + i*0x11 + 0x7f4a7c15 + j)
        out[j]=c ^ (key&0xff) ^ ((state>>((j&3)*8))&0xff)
        key=u32(key+0x11)
    return bytes(out)

def dump_inner(i):
    code=inner_code(i)
    print(f'-- check {i}: off,len,seed={inner_meta(i)}, ins={len(code)//8}')
    for pc in range(0,len(code),8):
        op,a,b,c,imm=ins_fields(code[pc:pc+8])
        print(f'  {pc//8:02}: {INNER_NAMES.get(op,hex(op)):6} r{a}, r{b}, {c:02}, {imm:#010x}')

BASE_REGS=list(unpack_from('<8I',BIN,0x53f0))

def run_inner(i, inp, outer_src=1, debug=0, trace=False):
    """Concrete model of the nested VM. Returns its boolean result."""
    code=inner_code(i)
    salt=debug ^ outer_src ^ i
    init_add=u32(salt+i)
    r=[xs(x+init_add) for x in BASE_REGS]
    for pc in range(0,len(code),8):
        op,a,b,c,imm=ins_fields(code[pc:pc+8])
        if trace: print(pc//8,INNER_NAMES.get(op,hex(op)),a,b,c,hex(imm),[hex(x) for x in r])
        if op==0x0a: r[a]=imm
        elif op==0x0f: r[a]=u32(r[a]+imm)
        elif op==0x21: return 1
        elif op==0x26: r[a]=u32(imm ^ r[a] ^ r[b] ^ r[c&7])
        elif op==0x30:
            if imm>=len(inp): return 0
            r[a]=inp[imm]
        elif op==0x59: r[a]=rol(r[a]+r[b]+imm,c)
        elif op==0x71: r[a]=rol(r[a],b)
        elif op==0x76: r[a]=xs(r[b]+r[a]+salt+imm)
        elif op==0x7d:
            if r[a] != imm: return 0
        elif op==0x93: r[a]=u32(r[a]-imm)
        elif op==0xa7: r[a]=ror(r[a],b)
        elif op==0xab: r[a]=u32(r[a]^imm)
        elif op==0xd2: r[a]=u32(r[a]*(imm|1))
        else: return 0
    return 0

def recover_direct():
    flag=bytearray(b'?'*48)
    for i in range(48):
        hits=[]
        for ch in range(256):
            flag[i]=ch
            if run_inner(i,flag): hits.append(ch)
        assert len(hits)==1,(i,hits)
        flag[i]=hits[0]
    return bytes(flag)

def verify_all(flag):
    return [(i,run_inner(i,flag)) for i in range(88)]

if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='dump':
        dump_outer()
        for i in range(116): dump_inner(i)
    else:
        f=recover_direct()
        print(f)
        print(verify_all(f))
