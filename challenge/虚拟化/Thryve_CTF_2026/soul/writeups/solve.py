#!/usr/bin/env python3
from pathlib import Path
import struct

BIN = Path('soul_dist/soul_dist/soul_dispatch').read_bytes()
ENC = BIN[0x3060:0x3060+0x819]

MASK=(1<<64)-1
def ks(i):
    x=((i*0x9e3779b97f4a7c15)&MASK)^0xdeadbeef13371337
    x=((x^(x>>16))*0x45d9f3b37d3aff67)&MASK
    x=((x^(x>>16))*0x45d9f3b37d3aff67)&MASK
    return (x^(x>>16))&0xff

P=bytes(b^ks(i) for i,b in enumerate(ENC))

ops={
 0xff:('HALT',0), 0x7e:('JMP',2), 0x42:('MOVI',2), 0xd8:('XORI',2),
 0x17:('MOV',2), 0x93:('ADD',2), 0xa5:('SUB',2), 0x2c:('XOR',2),
 0x0a:('CMPEQ',2), 0x8c:('JZ',3), 0x55:('JNZ',3),
 0x3e:('LOAD',3), 0x6b:('STORE',3), 0xf1:('LOADX',4), 0xe5:('STOREX',4),
}

def disasm():
    pc=0
    while pc < len(P):
        a=pc; op=P[pc]; pc+=1
        if op not in ops:
            print(f'{a:04x}: DB {op:02x}')
            continue
        name,n=ops[op]; args=P[pc:pc+n]; pc+=n
        if name=='JMP': s=f'{int.from_bytes(args,"big"):04x}'
        elif name in ('JZ','JNZ'): s=f'r{args[0]}, {int.from_bytes(args[1:],"big"):04x}'
        elif name in ('LOAD','STORE'): s=f'r{args[0]}, [{int.from_bytes(args[1:],"big"):03x}]'
        elif name in ('LOADX','STOREX'): s=f'r{args[0]}, r{args[1]}, [{int.from_bytes(args[2:],"big"):03x}]'
        elif n: s=', '.join(f'r{x}' if j==0 or name not in ('MOVI','XORI') else f'{x:#x}' for j,x in enumerate(args))
        else:s=''
        print(f'{a:04x}: {name:6s} {s}')

if __name__=='__main__':
    disasm()
