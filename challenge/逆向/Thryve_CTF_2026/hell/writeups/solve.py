#!/usr/bin/env python3
from z3 import *
target = bytes.fromhex('67 f8 71 ec 32 37 3a b7 70 19 47 f6')
x = [BitVec(f'x{i}',8) for i in range(12)]
s=Solver()
for c in x:
    s.add(UGE(c, 0x20), ULE(c,0x7e))
for i,t in enumerate(target):
    s.add(((x[i] ^ x[(i+1)%12]) + x[(i+2)%12]) * 3 == t)

for n in range(20):
    if s.check()!=sat: break
    m=s.model()
    ans=bytes(m.eval(c).as_long() for c in x)
    print(ans, ans.decode())
    s.add(Or(*[c != m.eval(c) for c in x]))
