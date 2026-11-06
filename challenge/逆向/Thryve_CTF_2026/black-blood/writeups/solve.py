import struct
MASK=(1<<64)-1
b=open('pekaboo/pekaboo','rb').read()
def u64(x): return x&MASK
def mix(x):
 x=u64((x^(x>>30))*0xbf58476d1ce4e5b9)
 x=u64((x^(x>>27))*0x94d049bb133111eb)
 return x^(x>>31)
def rol(x,n): n&=63; return u64((x<<n)|(x>>(64-n))) if n else x
state=struct.unpack_from('<Q',b,0x14018)[0]
g=struct.unpack_from('<Q',b,0x14010)[0]
state=u64(rol(state^0xf071dd5262dca406,17)+0x2bdf4d1ae947bb7c)
g ^= mix(state)
state=rol(u64(state+0xa450ffb79267f445),29)^0xcda2cc6ad9b3512a
g=u64(g+rol(state,7))
state=u64(mix(state^0x339d7d9bd931bad2)+0x8ab94c26a88c6e2b)
g ^= rol(state,41) # decomp state >>23 | <<41
print('globals',hex(g),hex(state))
qkeys=struct.unpack_from('<13Q',b,0x6340)
qconst=struct.unpack_from('<13Q',b,0x63c0)
chain=0x5075fcdbf977489a
q=0
u12=mix(state ^ chain ^ qconst[q] ^ u64((q+1)*(-0x5f89e29b87429bd1)))
u15=mix(qkeys[q]^u12^0xe7037ed1a0b428db)
ans=[]
for j in range(13):
 k=mix(u64((j+1)*(-0x5f89e29b87429bd1)) ^ u15 ^ 0xe7037ed1a0b428db)
 ans.append(b[0x6760+q*13+j]^(k&0xff))
print(hex(u12),hex(u15),bytes(ans))
def ctx(q,chain,anti=0):
 u12=mix(anti ^ state ^ chain ^ qconst[q] ^ u64((q+1)*0xa0761d6478bd642f))
 u15=mix(qkeys[q]^u12^0xe7037ed1a0b428db)
 return u12,u15

def dec_ins(q,chain,pc):
 u12,u15=ctx(q,chain)
 i=pc+1
 k=mix(u64(i*0x8ebc6af09c88c6e3)^u12^0x589965cc75374cc3)
 off=struct.unpack_from('<I',b,0x6300+4*q)[0]
 ct=struct.unpack_from('<Q',b,0x6810+8*(off+pc))[0]
 ins=ct^k
 check=mix((ins&0xffffffffffff)^u64(i*0xd6e8feb86659fd93)^u12)&0xffff
 assert ins>>48==check,(pc,hex(ins),hex(check))
 return ins

if __name__=='__main__':
 from collections import Counter
 print('ins')
 for pc in range(30):
  x=dec_ins(0,0x5075fcdbf977489a,pc)
  print(pc,hex(x),x.to_bytes(8,'little').hex(),hex(x&255))
 print(Counter(dec_ins(0,0x5075fcdbf977489a,pc)&255 for pc in range(482)))

def recover_answer(q,chain):
    u12,u15=ctx(q,chain)
    n=struct.unpack_from('<H',b,0x62d0+2*q)[0]
    equations=[]
    mlo=mhi=None
    rhs=None
    for pc in range(n):
        ins=dec_ins(q,chain,pc)
        op=ins&255; a=(ins>>8)&255
        if op==7:
            j=a+1
            mlo=mix(u64(j*0x9e3779b97f4a7c15)^qkeys[q]^0x243f6a8885a308d3)
            mhi=mix(u64(j*0xd1b54a32d192ed03)^qkeys[q]^0x13198a2e03707344)&0xffffffffff
        elif op==0x6e:
            j=a>>3
            ks=mix(u64((j+1)*0xa0761d6478bd642f)^u15^0xe7037ed1a0b428db)&255
            rhs=((ks^b[0x6760+q*13+j])>>(a&7))&1
        elif op==0x33:
            assert mlo is not None and rhs is not None
            equations.append((mlo|(mhi<<64),rhs))
            mlo=mhi=rhs=None
    assert len(equations)==104,len(equations)
    # Gauss-Jordan elimination over GF(2), augmented bit at position 104.
    rows=[m | (r<<104) for m,r in equations]
    rank=0
    piv=[]
    for col in range(104):
        k=next((k for k in range(rank,104) if (rows[k]>>col)&1),None)
        if k is None: continue
        rows[rank],rows[k]=rows[k],rows[rank]
        for k in range(104):
            if k!=rank and ((rows[k]>>col)&1): rows[k]^=rows[rank]
        piv.append(col);rank+=1
    assert all((r&((1<<104)-1)) or not ((r>>104)&1) for r in rows)
    assert rank==104,rank
    x=0
    for i,col in enumerate(piv): x|=((rows[i]>>104)&1)<<col
    return x.to_bytes(13,'little')

def mix_tail(x):
    """The last two SplitMix64 avalanche stages (some VM ops omit x^x>>30)."""
    x=u64(x*0xbf58476d1ce4e5b9)
    x=u64((x^(x>>27))*0x94d049bb133111eb)
    return x^(x>>31)

def run_vm(q,chain,answer,anti=0,trace=False):
    assert len(answer)==13
    u12,u15=ctx(q,chain,anti)
    regs=[mix(u12),mix(u15),mix(chain),mix(qkeys[q])]
    # Machine indexes are masked with 7, but only four entries should be used.
    regs += [0,0,0,0]
    ilo=int.from_bytes(answer[:8],'little')
    ihi=int.from_bytes(answer[8:],'little')
    n=struct.unpack_from('<H',b,0x62d0+2*q)[0]
    pc=0; steps=1; fail=0; acc=0; md=me=0
    while pc<n and steps<0x2711:
        ins=dec_ins(q,chain,pc)
        op=ins&255; b1=(ins>>8)&255; b2=(ins>>16)&255
        mid16=(ins>>16)&0xffff; hi16=(ins>>32)&0xffff
        nxt=pc+1
        if trace: print(steps,pc,hex(op),hex(ins))
        if op==0x33:
            fail |= acc
            j=b1&7
            regs[j]=rol(hi16 ^ fail ^ regs[j],(b2+1)&63)
        elif op==0x19:
            acc=((ilo&md).bit_count()^(ihi&me).bit_count())&1
            j=b1&7
            regs[j]=u64(regs[j]+mix_tail(u64(hi16+mid16+acc)))
        elif op==7:
            j0=b1+1
            md=mix(u64(j0*0x9e3779b97f4a7c15)^qkeys[q]^0x243f6a8885a308d3)
            me=mix(u64(j0*0xd1b54a32d192ed03)^qkeys[q]^0x13198a2e03707344)&0xffffffffff
            j=b1&7
            regs[j] ^= mix(hi16^md^me)
        elif op==1:
            j=b1&7
            regs[j] ^= regs[b2&7] ^ (ins&0xffff00000000)
        elif op==0x29:
            j=b1&7
            regs[j]=mix(hi16^(ins&0xffff0000)^pc^regs[j])
        elif op==0x40:
            j=b1&7
            regs[j]=rol(regs[j],(b2+1)&63)^hi16
        elif op==0x6e:
            bi=b1>>3
            ks=mix(u64((bi+1)*0xa0761d6478bd642f)^u15^0xe7037ed1a0b428db)&255
            acc^=((ks^b[0x6760+q*13+bi])>>(b1&7))&1
            j=(b1+3)&7
            regs[j]^=mix_tail(u64(hi16+acc))
        elif op==0xc4:
            fail|=1<<60
        elif op==0x55:
            break
        elif op==0xdf:
            s=mid16 if mid16<0x8000 else mid16-0x10000
            nxt=pc+s
        else:
            fail|=1<<62
            break
        pc=nxt
        if pc>=n: break
        steps+=1
    out2=regs[0]^steps^regs[3]
    inner=mix((ihi<<17)^ilo^0x6a09e667f3bcc909)
    out1=mix(qkeys[q]^u12^qconst[q]^inner)
    return fail,out1,out2,steps
def recover_all():
    chain=0x5075fcdbf977489a
    answers=[]
    for q in range(13):
        ans=recover_answer(q,chain)
        out=run_vm(q,chain,ans)
        assert out[0]==0,(q,out)
        answers.append(ans)
        gamma=u64((q+1)*0x9e3779b97f4a7c15)
        chain=mix(chain^out[1]^qconst[q]^gamma)
    return answers,chain
