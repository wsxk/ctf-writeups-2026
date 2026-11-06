# Made In Mongolia

**Category:** Pwn | **Points:** 1000 | **Author:** flame | **Flag:** `HZ{EZLThCay_n1c3_3sc@p3_fr0m_s1tu@t10n_E8dQ7eZS}`

## Challenge Description

A website lets you run programs written in **SFEX**, a small custom programming
language implemented in Rust. Dangerous standard-library features (file access,
command execution, networking) are blocked by an AST-based WAF, so there is no
simple `System.run("/flag")` solution. The goal is to run the `/flag` executable
inside the runner sandbox.

The web endpoint accepts up to 12 KiB of SFEX source:

```http
POST /api/run
Content-Type: application/json

{"code":"Story:\n    Print 123\n"}
```

Build details are fixed by the Dockerfile and matter for offsets:

- Rust 1.96, Ubuntu 24.04 runner
- SFEX commit `d9f6677e156304ee52b71eb31367309522b7f67e`

## Initial Analysis

The WAF is a proper AST check, not a string blacklist. It rejects imports and
references to dangerous globals (`System`, `File`, `Data`, `CSV`, `Env`, `HTTP`,
`WebSocket`, `TCP`, `UDP`, `LLM`). No spelling trick bypasses it, and the final
exploit does not need to — every statement in the payload is valid, WAF-approved
SFEX.

The real weakness lives lower down, in SFEX's **Cranelift JIT compiler**, which
turns methods "hot" after 100 calls into native code (`JIT_THRESHOLD = 100`).

## The Vulnerability / Core Concept

Two independent JIT bugs are chained:

**Bug 1 — wrong argument count on a cached JIT function.**
A method is compiled with a native signature based on its declared parameters
(all `F64`). But when the cached function is later called, the Rust function type
is chosen from the number of arguments supplied *at that call site*, with no
check that it matches the compiled signature:

```rust
match args.len() {
    2 => { let func: extern "C" fn(f64, f64) -> f64 = mem::transmute(func_ptr); ... }
    // ...up to ten arguments...
}
```

Declaring a method with 81 parameters, compiling it (100 calls with 81 args),
then calling the cached function with only 10 args makes the compiled code read
stale registers/stack slots — an ABI-level out-of-bounds read that leaks
addresses. Since all params are `f64`, a leaked pointer arrives as a subnormal
float whose value is `raw_bits × 2^-1074`, so multiplying by `2^1074` recovers
the integer address.

**Bug 2 — JIT symbol collision leaves stale Cranelift IR.**
Symbols are formed as `format!("{}_{}", concept, method)`, so `A_B.C` and
`A.B_C` both mangle to `A_B_C`. The duplicate-definition failure returns before
`clear_context`, so the *next* compiled method inherits the stale body — which
contains `Set This.B to A1`, invoking the unsafe `jit_update_field` helper with
an attacker-controlled `obj_ptr` cast to `Arc<RwLock<HashMap<String, Value>>>`.

## Exploitation

Full generator in `solve.py`. It emits `exploit.sfex` (11,341 bytes, under the
12 KiB limit).

1. **Spray + leak.** Define an 81-arg method, call it 100× to JIT it, then call
   with 10 args. Out-of-bounds ABI params `A41`/`A14`/`A22` disclose the JIT
   function entry, a stack address, and the `jit_args` heap vector.

2. **Recover pointers.** `JP is LJ * 2^1074` converts the subnormal float leak
   back to an integer. The exact `2^1074` is spelled as a huge decimal;
   `2^-1074` (the smallest positive `f64`, raw bits = 1) is used for raw-bit
   arithmetic via `FastNumber(...)`.

3. **Shellcode in executable JIT memory.** Cranelift materializes chosen `f64`
   constants as `movabs` immediates inside an RX code page. Five 8-byte chunks
   encode `execve("/flag", NULL, NULL)`, each ending in `jmp +0xc` to skip
   Cranelift's wrapper (20-byte stride) and land on the next immediate:

   ```python
   payloads = [
       bytes.fromhex("31d25231f690"),      # xor edx,edx; push rdx; xor esi,esi
       bytes.fromhex("68666c616790"),      # push "flag"
       bytes.fromhex("c64424ff2f90"),      # mov byte [rsp-1], '/'
       bytes.fromhex("488d7c24ff90"),      # lea rdi,[rsp-1]
       bytes.fromhex("31c0b03b0f059090"),  # execve syscall
   ]
   ```

   Nested `If` branches force the five constants to be emitted consecutively.
   The first chunk lands at `JIT_base + 0x122`, computed as
   `SP is FastNumber(JP + 290)`.

4. **Stale write primitive.** Compile `A_B.C` (claims symbol `A_B_C`), attempt
   `A.B_C` (fails, leaves dirty context), then compile `Z.Q` (inherits the stale
   `Set This.B` body). Because `Z.Q`'s metadata says it has no `Set`, the
   interpreter does not prepend a real object pointer, so its first ordinary
   argument is used as `jit_update_field`'s `obj_ptr`.

5. **Forge the Rust object.** A 10-arg call allocates exactly 80 bytes. Calling
   `SS.L` (10 args) inline first frees an 80-byte `jit_args` block whose address
   was just leaked; the outer 10-arg `W.Q` call deterministically reuses it, so
   its ten `f64` slots double as a fake `Arc/RwLock/HashMap`:

   ```sfex
   W.Q with (SS.L with ten args) and SP and BZ and BZ and TC and BM and BG and BZ and BZ and BZ
   ```

   The fake hash table is aimed at the JIT stack so inserting field `B` writes
   `SP` (the shellcode address) over the saved return address. When `Z.Q`
   returns, execution enters the JIT page and runs `execve("/flag")`.

The expected `stderr` includes the *intentional* duplicate-definition error —
that is part of the working exploit, not a failure:

```text
JIT compilation failed for A.B_C: Duplicate definition of identifier: A_B_C
```

Generate and (optionally) submit:

```sh
python3 solve.py                                   # writes exploit.sfex
python3 solve.py --local --run-local               # local proof (needs sfex + ./fla)
python3 solve.py --url 'https://<HOST>/api/run' --cookie '...'
```

`fla.c` builds the tiny local `/flag` stand-in used by `--local`.

## Flag

`HZ{EZLThCay_n1c3_3sc@p3_fr0m_s1tu@t10n_E8dQ7eZS}`

## Key Takeaways

- Language runtimes are a security boundary. A friendly source language and a
  perfect syntactic WAF do not protect against disagreements between the
  interpreter, JIT compiler, and native calling convention.
- A cached JIT function called with the wrong arity is an ABI-level OOB read —
  great for defeating ASLR without any array bug.
- A failed compilation that forgets to clear the compiler context can graft a
  dangerous body onto the next, innocent-looking method.
- JIT code pages are attacker-writable executable memory: chosen `f64` constants
  become `movabs` immediates you can execute directly, avoiding NX and ROP.
- `Decimal.from_float` (not scientific notation) is required so no bit of the
  shellcode constants is rounded away.
