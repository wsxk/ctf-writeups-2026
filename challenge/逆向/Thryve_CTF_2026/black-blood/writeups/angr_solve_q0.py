import angr,claripy,struct,time
from solve import state, mix
p=angr.Project('pekaboo/pekaboo',auto_load_libs=False)
base=p.loader.main_object.mapped_base
print('base',hex(base))
out=0x700000; inp=0x700100
st=p.factory.call_state(base+0x3bf0,out,0,inp,0x5075fcdbf977489a,0,ret_addr=0xdeadbeef)
# post-construct global
st.memory.store(base+0x14018, state.to_bytes(8,'little'))
cs=[claripy.BVS('c%d'%i,8) for i in range(13)]
for i,c in enumerate(cs):
 st.memory.store(inp+i,c)
 # avoid newline only; otherwise unrestricted
 st.solver.add(c!=10,c!=13)
sm=p.factory.simgr(st)
t=time.time();sm.explore(find=0xdeadbeef)
print('time',time.time()-t,'found',len(sm.found),'active',len(sm.active),'dead',len(sm.deadended),'err',len(sm.errored))
for e in sm.errored[:2]: print(e)
for x in sm.found:
 fail=x.memory.load(out,8,endness=p.arch.memory_endness)
 if x.solver.satisfiable(extra_constraints=[fail==0]):
  x.add_constraints(fail==0)
  a=bytes(x.solver.eval(c) for c in cs)
  print('answer',a,a.hex())
  print('outs', [hex(x.solver.eval(x.memory.load(out+8*i,8,endness=p.arch.memory_endness))) for i in range(3)])
