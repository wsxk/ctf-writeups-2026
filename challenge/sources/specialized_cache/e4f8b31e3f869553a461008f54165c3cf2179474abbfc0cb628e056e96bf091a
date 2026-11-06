#!/usr/bin/env python3
from z3 import *

w=[BitVec(f'w{i}',16) for i in range(16)]

def rol(x,n): return RotateLeft(x,n & 15)
def mix(a,b,c,d,r):
    t0=a ^ rol(d,3)
    t1=b + r*0x101
    t2=c ^ 0xa5a5
    v=rol(t0 + 0x9e37,5)
    v=v ^ rol(t1*0x45d9,9)
    v=rol(v + (t2 ^ 0x7f4a),3)
    v=v ^ (t0*0x1337)
    return v ^ rol(d*0x27d4 + r*0x33,(r%11)+1)

def mix_idx(desc):
    i0,i1,i2,i3,r=desc
    t0=w[i0]
    t1=w[i1] ^ rol(w[i3],(r%13)+1)
    t2=w[i2]
    v=rol(t0 + 0x9e37,5)
    v=v ^ rol(t1*0x45d9,9)
    v=rol(v + (t2 ^ 0x7f4a),3)
    v=v ^ (t0*0x1337)
    return v + rol(w[i3] ^ (r*0x1111),(r%7)+1)

s=Solver()
row=[0xcead,0x6d43,0xdf57,0xd811]
col=[0x6558,0xa8dc,0x35f7,0x10e5]
for k in range(4):
    s.add(mix(*w[4*k:4*k+4],k+1)==row[k])
    s.add(mix(w[k],w[k+4],w[k+8],w[k+12],k+5)==col[k])
s.add(mix(w[0],w[5],w[10],w[15],11)==0x4434)
s.add(mix(w[3],w[6],w[9],w[12],13)==0x0735)

descs=[
 [0,6,11,13,17], [4,10,15,1,19], [8,14,3,5,23], [12,2,7,9,29],
 [5,0,14,10,31], [15,4,9,2,37], [6,12,1,11,41], [3,8,13,7,43]]
iexp=[0xf826,0xd3ae,0x8ccc,0x0225,0x7c26,0x0982,0xee37,0xa397]
for d,e in zip(descs,iexp): s.add(mix_idx(d)==e)

c1=[0x4d31,0x91a7,0x2c5e,0xb083]
c2=[0xae1c,0xd1bd,0x5f43,0x4993]
cr=[3,7,11,5]
for i in range(4):
    idx=[0,1,4,5][i]
    # Checker calls the constant generator with loop counter i, then checks
    # the word selected by the small index table.
    s.add(w[idx]==rol(BitVecVal(c1[i]^c2[i],16),cr[i]))

print(s.check())
if s.check()==sat:
 m=s.model()
 vals=[m.eval(x).as_long() for x in w]
 print(''.join(f'{x:04x}' for x in vals))
 print([hex(x) for x in vals])
