#!/usr/bin/env python3
from pathlib import Path
import struct, sys
from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_INVALID
from unicorn.arm64_const import *

SO = 'extracted/lib/arm64-v8a/libd3llvm_payload.dec.so'
BASE = 0x1000000
STUB_BASE = 0x8000000
STACK = 0x9000000
HEAP = 0xa000000
TLS = 0xb000000
ENV = 0xc000000

def au(x, n=0x1000): return (x+n-1)&-n
def u64(x): return struct.pack('<Q', x)

class Emu:
 def __init__(self, token):
  self.uc=Uc(UC_ARCH_ARM64, UC_MODE_ARM)
  self.uc.mem_map(BASE,0x60000)
  self.uc.mem_map(STUB_BASE,0x10000)
  self.uc.mem_map(STACK,0x200000)
  self.uc.mem_map(HEAP,0x400000)
  self.uc.mem_map(TLS,0x10000)
  self.uc.mem_map(ENV,0x10000)
  self.brk=HEAP
  self.stubs={}; self.stub_names={}; self.next_stub=STUB_BASE
  self.load_elf()
  self.setup(token)
  self.uc.hook_add(UC_HOOK_CODE,self.on_code)
  self.uc.hook_add(UC_HOOK_MEM_INVALID,self.on_invalid)

 def load_elf(self):
  raw=Path(SO).read_bytes()
  with open(SO,'rb') as f:
   ef=ELFFile(f)
   for seg in ef.iter_segments():
    if seg['p_type']=='PT_LOAD':
     self.uc.mem_write(BASE+seg['p_vaddr'],raw[seg['p_offset']:seg['p_offset']+seg['p_filesz']])
   dynsym=ef.get_section_by_name('.dynsym')
   for secn in ['.rela.dyn','.rela.plt']:
    sec=ef.get_section_by_name(secn)
    for rel in sec.iter_relocations():
     typ=rel['r_info_type']; off=BASE+rel['r_offset']; add=rel['r_addend']
     si=rel['r_info_sym']; sym=dynsym.get_symbol(si) if si else None
     name=sym.name if sym else ''
     if typ==1027: val=BASE+add
     elif typ in (1025,1026):
      val=BASE+sym['st_value'] if sym and sym['st_value'] else self.get_stub(name)
     elif typ==257:
      val=(BASE+sym['st_value'] if sym and sym['st_value'] else self.get_stub(name))+add
     else:
      print('unhandled reloc',typ,hex(rel['r_offset']),name); continue
     self.uc.mem_write(off,u64(val))

 def get_stub(self,name):
  if name not in self.stubs:
   a=self.next_stub; self.next_stub+=4
   self.stubs[name]=a; self.stub_names[a]=name
   self.uc.mem_write(a,b'\xc0\x03\x5f\xd6') # ret
  return self.stubs[name]

 def setup(self,token):
  self.token=token.encode()+b'\0'
  self.tokptr=ENV+0x3000; self.uc.mem_write(self.tokptr,self.token)
  self.envtab=ENV+0x1000
  self.uc.mem_write(ENV,u64(self.envtab))
  for off,name in [(0x548,'JNI_GetStringUTFChars'),(0x550,'JNI_ReleaseStringUTFChars'),(0x538,'JNI_NewStringUTF')]:
   self.uc.mem_write(self.envtab+off,u64(self.get_stub(name)))
  self.uc.mem_write(TLS+0x28,u64(0x12345678abcdef00))
  self.uc.reg_write(UC_ARM64_REG_TPIDR_EL0,TLS)
  self.uc.reg_write(UC_ARM64_REG_SP,STACK+0x1ff000)
  self.uc.reg_write(UC_ARM64_REG_X0,ENV)
  self.uc.reg_write(UC_ARM64_REG_X1,0x1111)
  self.uc.reg_write(UC_ARM64_REG_X2,0x2222)
  self.uc.reg_write(UC_ARM64_REG_X3,BASE+0x42b90)
  self.uc.reg_write(UC_ARM64_REG_LR,STUB_BASE+0xfffc)

 def read_c(self,p,limit=100000):
  out=bytearray()
  while len(out)<limit:
   b=bytes(self.uc.mem_read(p+len(out),1))
   if b==b'\0': break
   out+=b
  return bytes(out)
 def malloc(self,n):
  p=self.brk; self.brk=au(p+max(n,1),16); return p
 def ret(self,val=0):
  self.uc.reg_write(UC_ARM64_REG_X0,val & ((1<<64)-1))
  self.uc.reg_write(UC_ARM64_REG_PC,self.uc.reg_read(UC_ARM64_REG_LR))

 def on_code(self,uc,addr,size,user=None):
  rel=addr-BASE
  if rel==0x1c640 and hasattr(self,'fake_session'):
   self.ret(self.fake_session); return
  if rel==0x29fc8:
   fp=uc.reg_read(UC_ARM64_REG_X29)
   sptr=struct.unpack('<Q',bytes(uc.mem_read(fp-0x28,8)))[0]
   st=struct.unpack('<I',bytes(uc.mem_read(sptr,4)))[0]
   print('SUCCESSSTORE state',st,'x8_before',hex(uc.reg_read(UC_ARM64_REG_X8)))
  if 0x2a444 <= rel < 0x2b848:
   last=getattr(self,'last_reveal_pc',None)
   if last is None or rel != last+4: print('REVBB',hex(rel))
   self.last_reveal_pc=rel
  reveal_calls={0x2a56c,0x2a670,0x2a67c,0x2a6c0,0x2a728,0x2a8d4,
    0x2a8ec,0x2a9a8,0x2aa10,0x2aaac,0x2ac6c,0x2acb0,0x2ada4,
    0x2ae38,0x2af30,0x2b060,0x2b0f4,0x2b1ec,0x2b22c,0x2b564,
    0x2b5a8,0x2b5b0,0x2b61c,0x2b690,0x2b69c,0x2b73c,0x2b758}
  if rel in reveal_calls:
   xs=[uc.reg_read(UC_ARM64_REG_X0+i) for i in range(5)]
   print('REVCALL',hex(rel),'target',hex(uc.reg_read(UC_ARM64_REG_X8)),*map(hex,xs))
  hnames={0x349d8:'mix_col',0x34f64:'hash16',0x34f50:'const4',
          0x34604:'ptr16a',0x34bc0:'mix4',0x34d54:'const8',
          0x34f30:'ptr16b',0x347e8:'mix_row',0x34d68:'mix_idx',
          0x34624:'ptr32',0x34f08:'ptr20',0x34d14:'ptr16',
          0x34590:'const_mix',0x34d34:'ptr16c'}
  if rel in hnames:
   xs=[uc.reg_read(UC_ARM64_REG_X0+i) for i in range(5)]
   print('HELP',hnames[rel],*map(hex,xs))
  if rel in (0x299a0,0x29bac,0x29c2c,0x29e78,0x2a0b8,0x1c6b0,0x1ca5c,0x35064,0x34644,0x347c8):
   xs=[uc.reg_read(UC_ARM64_REG_X0+i) for i in range(4)]
   print('TRACE',hex(rel),*map(hex,xs))
  if rel==0x2a1a0:
   print('SECRETCALL target',hex(uc.reg_read(UC_ARM64_REG_X8)),
         'x0',hex(uc.reg_read(UC_ARM64_REG_X0)),'x1',hex(uc.reg_read(UC_ARM64_REG_X1)))
  if addr==STUB_BASE+0xfffc:
   print('RETURN',hex(uc.reg_read(UC_ARM64_REG_X0))); uc.emu_stop(); return
  name=self.stub_names.get(addr)
  if not name:return
  x=[uc.reg_read(UC_ARM64_REG_X0+i) for i in range(8)]
  # print('CALL',name,*map(hex,x[:4]))
  if name in ('malloc','_Znwm','_ZnwmSt11align_val_t'):
   self.ret(self.malloc(x[0])); return
  if name=='calloc':
   p=self.malloc(x[0]*x[1]); uc.mem_write(p,b'\0'*(x[0]*x[1])); self.ret(p); return
  if name=='realloc':
   p=self.malloc(x[1]); self.ret(p); return
  if name in ('free','_ZdlPv','_ZdlPvm','_ZdlPvSt11align_val_t','pthread_mutex_lock','pthread_mutex_unlock'):
   self.ret(0); return
  if name in ('memset','__memset_chk'):
   uc.mem_write(x[0],bytes([x[1]&255])*x[2]); self.ret(x[0]); return
  if name in ('memcpy','__memcpy_chk','memmove'):
   uc.mem_write(x[0],bytes(uc.mem_read(x[1],x[2]))); self.ret(x[0]); return
  if name=='memcmp':
   a=bytes(uc.mem_read(x[0],x[2])); b=bytes(uc.mem_read(x[1],x[2])); self.ret((a>b)-(a<b)); return
  if name=='strlen': self.ret(len(self.read_c(x[0]))); return
  if name=='JNI_GetStringUTFChars': self.ret(self.tokptr); return
  if name=='JNI_ReleaseStringUTFChars': self.ret(0); return
  if name=='JNI_NewStringUTF':
   print('NewStringUTF:',self.read_c(x[1])); self.ret(x[1]); return
  if name=='bridge_cb': self.ret(1); return
  if name.endswith('6__initEPKcm') or name.endswith('6assignEPKcm'):
   obj,src,n=x[0],x[1],x[2]
   data=bytes(uc.mem_read(src,n))
   if n <= 22:
    uc.mem_write(obj,bytes([(n<<1)&0xfe])+data+b'\0'*(23-n))
   else:
    p=self.malloc(n+1); uc.mem_write(p,data+b'\0')
    uc.mem_write(obj,u64(1)+u64(n)+u64(p))
   self.ret(obj); return
  if name in ('__stack_chk_fail','abort','__cxa_throw'):
   raise RuntimeError('fatal '+name)
  # Harmless destructors / exception API / unknown imports initially return zero.
  if name=='__cxa_guard_acquire':
   self.ret(0 if bytes(uc.mem_read(x[0],1)) != b'\0' else 1); return
  if name=='__cxa_guard_release':
   uc.mem_write(x[0],b'\1'); self.ret(0); return
  if name.startswith('_ZNSt6__ndk1') or name in ('__cxa_begin_catch','__cxa_end_catch'):
   print('CXX',name,*map(hex,x[:4]))
   self.ret(0); return
  print('UNHANDLED',name,*map(hex,x[:4])); self.ret(0)

 def on_invalid(self,uc,access,addr,size,value,user=None):
  print('INVALID',access,hex(addr),size,'pc',hex(uc.reg_read(UC_ARM64_REG_PC)))
  return False

 def run(self,fn=0x292c4):
  try:self.uc.emu_start(BASE+fn,STUB_BASE+0xfffc,count=10000000)
  except Exception as e:
   print('EXC',e,'pc',hex(self.uc.reg_read(UC_ARM64_REG_PC)))
   raise
  print('STOP pc',hex(self.uc.reg_read(UC_ARM64_REG_PC)),'x0',hex(self.uc.reg_read(UC_ARM64_REG_X0)))

if __name__=='__main__':
 Emu(sys.argv[1] if len(sys.argv)>1 else '0'*64).run()
