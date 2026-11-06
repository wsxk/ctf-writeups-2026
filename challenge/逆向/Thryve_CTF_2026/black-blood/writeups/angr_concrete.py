import angr,struct,time
import solve
p=angr.Project('pekaboo/pekaboo',auto_load_libs=False)
base=p.loader.main_object.mapped_base

def check(q,chain,answer):
 out=0x700000; inp=0x700100
 st=p.factory.call_state(base+0x3bf0,out,q,inp,chain,0,ret_addr=0xdeadbeef,
     add_options={angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS,angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY})
 st.memory.store(base+0x14018,solve.state.to_bytes(8,'little'))
 st.memory.store(inp,answer)
 sm=p.factory.simgr(st)
 sm.explore(find=0xdeadbeef)
 assert len(sm.found)==1,(len(sm.active),len(sm.deadended),sm.errored)
 x=sm.found[0]
 return tuple(x.solver.eval(x.memory.load(out+8*i,8,endness=p.arch.memory_endness)) for i in range(3))
if __name__=='__main__':
 chain=0x5075fcdbf977489a
 a=solve.recover_answer(0,chain); t=time.time();print(a,tuple(hex(x) for x in check(0,chain,a)),time.time()-t)
