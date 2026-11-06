#!/usr/bin/env python3
import struct,z3
p='redline'; data=open(p,'rb').read()
# One Boolean per logical dual-rail wire (first rail).
xs=[z3.Bool(f'x{i}') for i in range(288)]
w={i:xs[i] for i in range(288)}
rands=[]
counts={}
for i in range(0xb9c0//16):
    f,a,b,c=struct.unpack_from('<QHHH',data,0xa14a0+16*i)
    counts[f]=counts.get(f,0)+1
    if f==0x401bb0: # NOT a -> b
        w[b]=z3.Not(w[a])
    elif f==0x401bd0: # XOR a,b -> c
        w[c]=z3.Xor(w[a],w[b])
    elif f==0x401c00: # NAND a,b -> c
        w[c]=z3.Not(z3.And(w[a],w[b]))
    elif f==0x401c30: # fanout a -> b,c
        w[b]=w[a]; w[c]=w[a]
    elif f==0x401c60: # flip a,b by the same runtime PRNG bit
        r=z3.Bool(f'r{len(rands)}'); rands.append(r)
        w[a]=z3.Xor(w[a],r); w[b]=z3.Xor(w[b],r)
    else: raise ValueError((i,hex(f)))
print('gates',counts,'rands',len(rands),'wires',len(w))
inds=struct.unpack_from('<320H',data,0x7ec00)
target=data[0x7ef20:0x7ef20+40]
s=z3.Solver()
for i,wi in enumerate(inds):
    bit=(target[i//8]>>(i%8))&1
    s.add(w[wi] == bool(bit))
# input is exactly 36 graphic bytes as enforced by binary
for j in range(36):
    val=z3.Sum([z3.If(xs[8*j+k],1<<k,0) for k in range(8)])
    s.add(val>=0x21,val<=0x7e)
# Known flag wrapper (challenge asks credential/flag and exact length strongly suggests this)
prefix=b'ThryveCTF{'
for j,ch in enumerate(prefix):
    for k in range(8): s.add(xs[8*j+k] == bool((ch>>k)&1))
ch=ord('}')
for k in range(8): s.add(xs[8*35+k] == bool((ch>>k)&1))
print('check...')
print(s.check())
m=s.model()
out=[]
for j in range(36):
    v=sum((1<<k) if z3.is_true(m.eval(xs[8*j+k],model_completion=True)) else 0 for k in range(8))
    out.append(v)
print(bytes(out))
print('randoms', ''.join('1' if z3.is_true(m.eval(r,model_completion=True)) else '0' for r in rands))
# uniqueness of input
s.add(z3.Or([x != m.eval(x,model_completion=True) for x in xs]))
print('another input?',s.check())
