#!/usr/bin/env python3
import angr, claripy

SO='extracted/lib/arm64-v8a/libd3llvm_payload.dec.so'
p=angr.Project(SO,auto_load_libs=False)
b=p.loader.main_object.mapped_base
inp=0x700000
words=[claripy.BVS(f'w{i}',16) for i in range(16)]
st=p.factory.call_state(b+0x35330,inp,b+0x42fb8,
    add_options={angr.options.ZERO_FILL_UNCONSTRAINED_MEMORY,
                 angr.options.ZERO_FILL_UNCONSTRAINED_REGISTERS})
for i,w in enumerate(words):
    st.memory.store(inp+2*i,w,endness=p.arch.memory_endness)
sm=p.factory.simgr(st)
sm.run()
print('deadended',len(sm.deadended),'errored',len(sm.errored),'active',len(sm.active))
for s in sm.deadended:
    t=s.copy()
    t.add_constraints(t.regs.x0==1)
    if t.solver.satisfiable():
        vals=[t.solver.eval(w) for w in words]
        # Input hex parsing packs each group of four nibbles big-endian into uint16.
        print(''.join(f'{x:04x}' for x in vals))
        print([hex(x) for x in vals])
        break
else:
    for e in sm.errored[:3]: print(e)
