#!/usr/bin/env python3
import struct
from pathlib import Path

ELF = Path("parallax").read_bytes()
CIPHER = ELF[0x20c0:0x20c0 + 0x2c7c]
OPMAP = ELF[0x4ea0:0x4ee0]
SBOX = ELF[0x4d40:0x4e40]

def decrypt():
    state = 0xdd44d5bae067208d
    plain = bytearray()
    for i, c in enumerate(CIPHER):
        if i % 8 == 0:
            state ^= state << 13
            state &= (1 << 64) - 1
            state ^= state >> 7
            state ^= state << 17
            state &= (1 << 64) - 1
        plain.append(c ^ ((state >> (8 * (i % 8))) & 0xff))
    return bytes(plain)

CODE = decrypt()
NAMES = ['HALT','MOVI','LOAD','XOR','ADD','MULI','ROL','SUB','SBOX','MIXI',
         'ASSERT','XORI','ADDI','SWAP','NOP','BAD']

def mix(x):
    x &= 0xffffffff
    x ^= x >> 16
    x = x * 0x7feb352d & 0xffffffff
    x ^= x >> 15
    x = x * 0x846ca68b & 0xffffffff
    x ^= x >> 16
    return x

def unxorshr(y, n):
    """Undo x ^ (x >> n), on a 32-bit word."""
    x = y
    shift = n
    while shift < 32:
        x ^= y >> shift
        shift += n
    return x & 0xffffffff

def unmix(x):
    x = unxorshr(x, 16)
    x = x * pow(0x846ca68b, -1, 1 << 32) & 0xffffffff
    x = unxorshr(x, 15)
    x = x * pow(0x7feb352d, -1, 1 << 32) & 0xffffffff
    x = unxorshr(x, 16)
    return x

def solve_triplet(m1, xor2, rot, m2, miximm, addimm, target,
                  allowed=(range(0x20, 0x7f),)*3):
    """Solve the recurring three-byte assertion template."""
    pre = unmix((target - addimm) & 0xffffffff) ^ miximm
    cproducts = {(c * m2) & 0xffffffff: c for c in allowed[2]}
    ans = []
    for a in allowed[0]:
        am = a * m1 & 0xffffffff
        for b in allowed[1]:
            left = rol((am + subst(b ^ xor2)) & 0xffffffff, rot)
            c = cproducts.get(left ^ pre)
            if c is not None:
                ans.append((a,b,c))
    return ans

def subst(x):
    return sum(SBOX[(x >> shift) & 0xff] << shift for shift in range(0, 32, 8))

def rol(x, n):
    n &= 31
    return ((x << n) | (x >> ((32 - n) & 31))) & 0xffffffff

def vm(inp, trace=False, trace_assert=True, return_history=False, stop_failed=False):
    assert len(inp) == 45
    regs = [0] * 8
    pc = phase = errors = 0
    assertions = []
    history = []
    for step in range(200000):
        if pc >= len(CODE):
            break
        old = pc
        oldphase = phase
        before = regs.copy()
        olderrors = errors
        raw = CODE[pc]
        if raw > 15:
            op = 15
        else:
            op = OPMAP[phase * 16 + raw]
        detail = ''
        if op == 0:
            pc = len(CODE)
        elif op in (1,5,9,10,11,12):
            if pc + 6 > len(CODE): errors |= 0x80000000; break
            a = CODE[pc+1]
            v = struct.unpack_from('<I', CODE, pc+2)[0]
            pc += 6
            detail = f'r{a}, {v:#010x}'
            if a >= 8:
                errors |= 1
            elif op == 1: regs[a] = v
            elif op == 5: regs[a] = regs[a] * v & 0xffffffff
            elif op == 9: regs[a] = mix(regs[a] ^ v)
            elif op == 10:
                good = regs[a] == v
                assertions.append((old, a, regs[a], v, good))
                errors |= not good
            elif op == 11: regs[a] ^= v
            elif op == 12: regs[a] = (regs[a] + v) & 0xffffffff
        elif op in (2,3,4,6,7,13):
            if pc + 3 > len(CODE): errors |= 0x80000000; break
            a, c = CODE[pc+1:pc+3]
            pc += 3
            detail = f'r{a}, {c if op in (2,6) else "r"+str(c)}'
            if op == 2:
                if a >= 8 or c >= len(inp): errors |= 1
                else: regs[a] = inp[c]
            elif op == 6:
                if a >= 8: errors |= 1
                else: regs[a] = rol(regs[a], c)
            else:
                if a >= 8 or c >= 8: errors |= 1
                elif op == 3: regs[a] ^= regs[c]
                elif op == 4: regs[a] = (regs[a] + regs[c]) & 0xffffffff
                elif op == 7: regs[a] = (regs[a] - regs[c]) & 0xffffffff
                else: regs[a], regs[c] = regs[c], regs[a]
        elif op == 8:
            if pc + 2 > len(CODE): errors |= 0x80000000; break
            a = CODE[pc+1]
            pc += 2
            detail = f'r{a}'
            if a >= 8: errors |= 1
            else: regs[a] = subst(regs[a])
        elif op == 14:
            pc += 1
        else:
            errors |= 0x20000000
            if trace: print(f'{step:5} @{old:04x} p{phase} raw{raw:x} BAD')
            break
        if trace or (trace_assert and op == 10):
            print(f'{step:5} @{old:04x} p{phase} raw{raw:x} {NAMES[op]:7} {detail:18} '
                  f'pc={pc:04x} r0={regs[0]:08x} r3={regs[3]:08x} err={errors:x}')
        history.append(dict(pc=old, phase=oldphase, raw=raw, op=op,
                            detail=detail, before=before, after=regs.copy(),
                            errors_before=olderrors, errors_after=errors))
        phase = (phase + ((regs[0] ^ regs[3] ^ pc) & 3) + (op & 1)) & 3
        if stop_failed and op == 10 and errors != olderrors:
            break
    result = (errors, assertions, pc, phase, regs)
    return result + (history,) if return_history else result

TRIPLET_OPS = [2, 2, 5, 11, 8, 4, 6, 2, 5, 3, 9, 12, 10]

def auto_solve(verbose=True):
    known = {i: c for i, c in enumerate(b'Thryve{')}
    known[44] = ord('}')
    printable = tuple(range(0x20, 0x7f))
    for iteration in range(100):
        candidate = bytes(known.get(i, ord('A')) for i in range(45))
        result = vm(candidate, trace_assert=False, return_history=True,
                    stop_failed=True)
        errors, assertions, pc, phase, regs, history = result
        failed = [x for x in assertions if not x[-1]]
        if not failed:
            if verbose:
                print('candidate', candidate)
                print('VM:', errors, 'pc', hex(pc), 'assertions', len(assertions))
            return candidate, errors
        # The challenge emits each check using this fixed 13-op template.
        end = len(history)
        start = end - len(TRIPLET_OPS)
        block = history[start:end]
        gotops = [x['op'] for x in block]
        if gotops != TRIPLET_OPS:
            raise RuntimeError(f'unexpected check template at {history[-1]["pc"]:#x}: {gotops}')
        p = [x['pc'] for x in block]
        ia = CODE[p[0]+2]
        ib = CODE[p[1]+2]
        ic = CODE[p[7]+2]
        m1 = struct.unpack_from('<I', CODE, p[2]+2)[0]
        xor2 = struct.unpack_from('<I', CODE, p[3]+2)[0]
        rot = CODE[p[6]+2]
        m2 = struct.unpack_from('<I', CODE, p[8]+2)[0]
        miximm = struct.unpack_from('<I', CODE, p[10]+2)[0]
        addimm = struct.unpack_from('<I', CODE, p[11]+2)[0]
        target = struct.unpack_from('<I', CODE, p[12]+2)[0]
        inds = (ia, ib, ic)
        allowed = tuple((known[i],) if i in known else printable for i in inds)
        answers = solve_triplet(m1, xor2, rot, m2, miximm, addimm, target,
                                allowed=allowed)
        if len(answers) != 1:
            raise RuntimeError(f'check {iteration} indices {inds}: {len(answers)} answers {answers[:10]}')
        values = answers[0]
        for i, value in zip(inds, values):
            if i in known and known[i] != value:
                raise RuntimeError(f'conflict at input[{i}]')
            known[i] = value
        if verbose:
            view = bytes(known.get(i, ord('?')) for i in range(45))
            print(f'{iteration:2}: assert@{p[-1]:04x} indices={inds} '
                  f'values={bytes(values)!r}  {view!r}')
    raise RuntimeError('too many iterations')

if __name__ == '__main__':
    import sys
    s = (sys.argv[1] if len(sys.argv)>1 else 'Thryve{' + 'A'*37 + '}').encode()
    print('input', s, 'len', len(s))
    print(vm(s, trace='-t' in sys.argv))

def solve_first():
    import z3
    xs = [z3.BitVec(f'x{i}', 8) for i in range(45)]
    x19,x10,x36=xs[19],xs[10],xs[36]
    arr=z3.K(z3.BitVecSort(8),z3.BitVecVal(0,8))
    for i,v in enumerate(SBOX): arr=z3.Store(arr,z3.BitVecVal(i,8),z3.BitVecVal(v,8))
    def zx(x): return z3.ZeroExt(24,x)
    def sb32(v):
      return z3.Concat(z3.Select(arr,z3.Extract(31,24,v)),z3.Select(arr,z3.Extract(23,16,v)),z3.Select(arr,z3.Extract(15,8,v)),z3.Select(arr,z3.Extract(7,0,v)))
    def mx(v):
      v=v ^ z3.LShR(v,16);v=v*z3.BitVecVal(0x7feb352d,32);v=v^z3.LShR(v,15);v=v*z3.BitVecVal(0x846ca68b,32);v=v^z3.LShR(v,16);return v
    v1=zx(x19)*z3.BitVecVal(0x76097283,32)
    v2=sb32(zx(x10)^z3.BitVecVal(0x1bda6b19,32))
    v1=z3.RotateLeft(v1+v2,9)
    v2=zx(x36)*z3.BitVecVal(0x08b8394b,32)
    v1=mx((v1^v2)^z3.BitVecVal(0xa46234c8,32))+z3.BitVecVal(0xeca831f7,32)
    s=z3.Solver()
    for x in [x19,x10,x36]:s.add(x>=0x20,x<=0x7e)
    s.add(v1==0xc09dfbdf)
    while s.check()==z3.sat:
      m=s.model(); sol=tuple(m.eval(x).as_long() for x in [x19,x10,x36]);print(sol,bytes(sol));s.add(z3.Or(*[x!=v for x,v in zip([x19,x10,x36],sol)]))

if __name__=='__main__' and '--first' in __import__('sys').argv: solve_first()
