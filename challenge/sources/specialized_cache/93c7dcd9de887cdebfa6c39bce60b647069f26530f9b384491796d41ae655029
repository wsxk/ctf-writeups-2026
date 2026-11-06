#!/usr/bin/env python3
from pathlib import Path
import struct,hashlib
p=Path('extracted/lib/arm64-v8a/libd3llvm_payload.so')
b=bytearray(p.read_bytes())
sign=b[0x52b0:0x53b0]
assert sign[:8]==b'D3SGN2\0\0'
ver,flags=struct.unpack_from('<II',sign,8)
text_vaddr,text_size,text_off=struct.unpack_from('<QQQ',sign,0x10)
nonce=sign[0x28:0x38]
key=sign[0x38:0x58]
expected=sign[0x58:0x78]
print(ver,flags,hex(text_vaddr),hex(text_size),hex(text_off))
print('nonce',nonce.hex(),'key',key.hex(),'expected',expected.hex())
ct=b[text_off:text_off+text_size]
pt=bytearray(ct)
for counter,pos in enumerate(range(0,len(pt),32)):
    stream=hashlib.sha256(key+nonce+struct.pack('<Q',counter)).digest()
    for i in range(min(32,len(pt)-pos)): pt[pos+i]^=stream[i]
print('first',pt[:64].hex())
print('sha256',hashlib.sha256(pt).hexdigest(), 'matches',hashlib.sha256(pt).digest()==expected)
b[text_off:text_off+text_size]=pt
out=p.with_name('libd3llvm_payload.dec.so')
out.write_bytes(b)
print('wrote',out)
