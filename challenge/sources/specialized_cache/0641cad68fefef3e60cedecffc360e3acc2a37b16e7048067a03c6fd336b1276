from emulate_payload import *
from unicorn.arm64_const import *
from pathlib import Path
import struct

e=Emu('0'*64)
u=e.uc
raw=Path('touch_model.mnn.enc').read_bytes()
p=e.malloc(len(raw)); u.mem_write(p,raw)
vin=e.malloc(24); vout=e.malloc(24)
u.mem_write(vin,struct.pack('<QQQ',p,p+len(raw),p+len(raw)))
u.mem_write(vout,b'\0'*24)
u.reg_write(UC_ARM64_REG_SP,STACK+0x1ff000)
u.reg_write(UC_ARM64_REG_X0,vin)
u.reg_write(UC_ARM64_REG_X8,vout)
u.reg_write(UC_ARM64_REG_LR,STUB_BASE+0xfffc)
e.run(0x3055c)
a,b,c=struct.unpack('<QQQ',bytes(u.mem_read(vout,24)))
print('vout',hex(a),hex(b),hex(c),'size',b-a)
out=bytes(u.mem_read(a,b-a)); Path('touch_model.stage1').write_bytes(out)
print(out[:200])
