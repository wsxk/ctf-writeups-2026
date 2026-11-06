from emulate_payload import *
from unicorn.arm64_const import *
t='196f0d201332b47deb98221f33c7f4a13d03de6c2a77279c4dbc1f87e4d297a8'
secret=0xa01c8100444fb480
e=Emu(t);uc=e.uc
uc.mem_write(BASE+0x43180,t.encode()+b'\0')
uc.mem_write(BASE+0x431c8,u64(secret))
uc.mem_write(BASE+0x431d0,b'\1');b=BASE+0x43118
uc.mem_write(b,u64(1)+u64(e.get_stub('bridge_cb'))+u64(BASE)+u64(0x3f8c0)+u64(BASE+0x52b0)+u64(0x80))
uc.mem_write(BASE+0x3689c,b'\x20\x00\x80\x52\xc0\x03\x5f\xd6')
uc.reg_write(UC_ARM64_REG_X0,ENV);uc.reg_write(UC_ARM64_REG_X1,0x1111);uc.reg_write(UC_ARM64_REG_X2,BASE+0x42ca0);e.run(0x2a444)
