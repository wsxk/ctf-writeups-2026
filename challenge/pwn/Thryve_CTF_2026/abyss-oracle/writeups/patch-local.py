#!/usr/bin/env python3
import struct
src='extracted/abyss_oracle-original.ko'; dst='extracted/abyss_oracle.ko'
b=bytearray(open(src,'rb').read())
# target kernel vermagic
old=b'6.12.95+deb13-cloud-amd64 SMP preempt mod_unload modversions '
new=b'6.19.14+kali-amd64 SMP preempt mod_unload '
i=b.find(old); assert i>=0
b[i:i+len(old)]=new+b'\0'*(len(old)-len(new))
# Satisfy the loader's now-unreferenced undefined symbol with an existing export.
# This occurrence is the .strtab name (not the earlier __versions entry).
i=b.rfind(b'__mutex_init\0'); assert i>=0
b[i:i+13]=b'mutex_lock\0\0\0'
# .text lives at file offset 0x40. Replace the otherwise-unused helper,
# while preserving zeroed relocation fields at +0x15..18 and +0x26..29.
base=0x40
b[base+0x10:base+0x15]=bytes.fromhex('eb07909090')       # jump to +0x19
b[base+0x19:base+0x26]=bytes.fromhex('31c048890748894708eb06') + b'\x90'*2
b[base+0x2a:base+0x3d]=bytes.fromhex('488d47104889471048894718c3') + b'\x90'*6
# Redirect call relocation at .text+0x41e to local .text+0x10.
# .rela.text starts 0x2e50, entries are Elf64_Rela.
found=False
for off in range(0x2e50,0x2e50+0x6d8,24):
    ro,info,add=struct.unpack_from('<QQq',b,off)
    if ro==0x41e:
        # symbol 1 (.text), R_X86_64_PLT32 (4), target addend 0x10-4
        struct.pack_into('<QQq',b,off,ro,(1<<32)|4,0xc)
        found=True
assert found
# struct module::exit moved from 0x4b0 to 0x4c0 in Linux 6.19.
# Patch the second .rela.gnu.linkonce.this_module relocation's target offset.
struct.pack_into('<Q', b, 0x49e0 + 24, 0x4c0)
# 6.19 uses a different stack-canary ABI (RIP-relative rather than gs:0x28).
# Neutralize the old module's canary loads/checks for local compatibility.
for op in (0x8b, 0x2b):
    for modrm,xor3 in ((0x04,bytes.fromhex('4831c0')),
                       (0x14,bytes.fromhex('4831d2')),
                       (0x2c,bytes.fromhex('4831ed'))):
        pat=bytes((0x65,0x48,op,modrm,0x25,0x28,0,0,0))
        while True:
            j=b.find(pat)
            if j<0: break
            b[j:j+9]=xor3+b'\x90'*6
open(dst,'wb').write(b)
