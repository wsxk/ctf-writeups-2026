import struct,string
b=open('touch_model.mnn','rb').read(); n=len(b)
u16=lambda p:struct.unpack_from('<H',b,p)[0]; u32=lambda p:struct.unpack_from('<I',b,p)[0]; i32=lambda p:struct.unpack_from('<i',b,p)[0]
def stringat(q):
 if q<0 or q+4>n:return None
 l=u32(q)
 if not (0<l<200 and q+4+l<=n):return None
 s=b[q+4:q+4+l]
 if all(32<=c<127 for c in s): return s.decode()
def table_fields(t):
 if t<4 or t>=n:return []
 try:v=t-i32(t); vl=u16(v); os=u16(v+2)
 except:return []
 if not(4<=vl<=100 and 4<=os<=256 and 0<=v<n):return []
 out=[]
 for f in range((vl-4)//2):
  o=u16(v+4+2*f)
  if o and o+4<=os:
   loc=t+o; val=u32(loc); q=loc+val
   out.append((f,o,val,q,stringat(q)))
 return out
root=u32(0); opvec=916; cnt=u32(opvec)
print('count',cnt)
for i in range(cnt):
 loc=opvec+4+4*i; t=loc+u32(loc)
 print(i,hex(t),table_fields(t))
