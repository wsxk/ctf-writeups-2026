# squ1rrel-o-tron-2

**Category:** Rev | **Difficulty:** 495 pts (2 solves) | **Flag:** `squ1rrel{c0mp1l1ng_t0_c0mb1n4t0rs_1s_s0_r3tr0}`

## TL;DR

A PDF hides a retro 32-bit register VM in its JavaScript layer. The VM implements a mystery `mix()` function — and the server challenges you to compute it 20,000 times in 5 seconds. Running the VM is way too slow (~5 ms/call × 20,000 = 100 seconds), so we reverse-engineered the VM bytecode to extract the actual algorithm: 12 rounds of `ROTL5(SBOX4(char × accumulator XOR round_key))`, reimplemented it in 43 lines of C, and solved all 20,000 challenges in under 20 milliseconds.

## What We're Given

Two files: `server.py` and `chall.pdf`. The server description is immediately provocative:

```python
def mix(s: str) -> str:
    raise NotImplementedError
```

Yep, the server's `mix()` function is literally a `NotImplementedError`. The implementation is in the PDF. The server sends 20,000 random 8-character challenges over TCP. For each challenge `c_i`, we need to compute `a_i = mix(a_{i-1} + c_i)`, where consecutive answers chain together (the previous output becomes the first 4 characters of the next input). All 20,000 must be answered correctly within a 5-second window.

The challenge description drops a hint: *"I found my father's squ1rrel-o-tron! But it's running something from a bygone era, and he told me not to be lazy."*

"Not be lazy" is a strong hint. We'll come back to why.

## Initial Recon

Opening `chall.pdf` in any viewer gives you a retro terminal display that says `squ1rrel-o-tron 2` and a `>` prompt. The flavor text says it works best on Chromium — that's because it runs JavaScript in the PDF's `OpenAction` event, which Chromium's PDF viewer actually executes.

The fun part: PDFs can contain JavaScript. A full custom computer emulator, implemented in PDF JavaScript. That's the "bygone era" — we're literally booting a virtual 1986-era 8-bit terminal.

We extracted the JavaScript from the PDF stream and found a complete VM:

- **31 registers** (`j[0..30]`)
- **65,536 memory cells** (`P[0..65535]`), each 32 bits wide
- **16 opcodes**: load-immediate (high/low), branch, load, store, add, sub, xor, and, or, shift, multiply, halt
- **Memory-mapped I/O** at address `h=40832`: reads from `h` pull the next input character; writes to `h+odd_offset` push characters to the screen output

When you type a 12-character string and hit enter, the VM "computes" something and prints a 4-hex-digit answer.

We verified the oracle: `mix("0000aaaaaaaa")` → `"90aa"`. Working.

## The Vulnerability / Trick

The trick here is a performance cliff — and the only way out is to actually understand what the algorithm *is*.

### Step 1: The Oracle Is Unusably Slow

We ported the VM to JavaScript, then to C with `-O3`. Best speed: **~5.7 ms per `mix()` call** in optimized C. Multiply that out:

```
5.7 ms × 20,000 calls = 114 seconds
```

The deadline is 5 seconds. We need a ~23× speedup minimum. And there's no parallelism — each challenge depends on the previous answer.

We tried threaded-code JIT (computed goto in C), a JavaScript JIT that pre-compiled VM bytecode to native functions. The computed-goto version compiled to a 1.1 MB C file; GCC `-O1` and above ran out of memory trying to optimize an 8,000-label function. The JavaScript JIT hit similar walls. None of it was fast enough.

The challenge name was right: we couldn't be lazy. We had to actually read what the bytecode *does*.

### Step 2: The Compilation Phase Is a Red Herring (Sort Of)

When `mix()` is called, the VM first runs through a "compilation phase" of about 263 steps. This reads the first character of the input, stores its ASCII value at two memory addresses (`P[2827]` and `P[8170]`), and then... produces identical bytecode regardless of what you typed. Every input character goes through the exact same code path.

The compile phase builds an expression tree in memory at `P[1246+128..1246+1584]` — 728 opcode pairs. This is the actual computation engine.

### Step 3: The Execution Phase Is 1.36 Million Steps of Tree-Walking

The "execution phase" then walks this expression tree ~1.36 million times per call. That's why it's slow — it's a tree-walking interpreter *inside* a VM interpreter. We're three levels of interpretation deep at this point.

We instrumented the VM to log every XOR, shift, and multiply operation, then stared at the patterns.

### Step 4: The Algorithm Falls Out

After tracing the arithmetic operations across different inputs, we identified the structure:

The input to `mix()` is always exactly 12 characters: 4 chars from the previous answer (hex digits) concatenated with the 8-char challenge. The computation applies 12 rounds, one per input character:

```
accum[0]  = char[0] × 0x3a2a              (mod 65536)
accum[i]  = char[i] × state_{i-1}         (mod 65536)
state[i]  = ROTL5(SBOX4(accum[i] XOR key[i % 4]))
```

Where:
- `ROTL5(v)` = rotate left by 5 bits (16-bit value)
- `SBOX4(v)` = apply a 4-bit S-box to each of the 4 nibbles of `v` independently
- Round keys cycle through 4 values: `0x8e87, 0x4524, 0xb745, 0x9e51`
- S-box: `{0→8, 1→e, 2→c, 3→7, 4→f, 5→4, 6→5, 7→2, 8→6, 9→a, a→b, b→0, c→3, d→9, e→1, f→d}`

The final `state[11]` is the answer — the 4-hex-digit output.

The title's flag hint makes sense in retrospect: `c0mp1l1ng_t0_c0mb1n4t0rs` — the VM is literally implementing a combinator-based expression evaluator, which is a classic functional programming compilation technique from the 1980s. The "compile" phase builds combinators; the "execute" phase walks them. Retro indeed.

## Building the Exploit

### The Fast Implementation

Once we had the algorithm, reimplementing it in C took about 5 minutes:

```c
static const uint8_t sbox[16] = {8,14,12,7,15,4,5,2,6,10,11,0,3,9,1,13};
static const uint16_t keys[4] = {0x8e87, 0x4524, 0xb745, 0x9e51};

static inline uint16_t sbox4(uint16_t v) {
    return ((uint16_t)sbox[v&0xf])         |
           ((uint16_t)sbox[(v>>4)&0xf]<<4) |
           ((uint16_t)sbox[(v>>8)&0xf]<<8) |
           ((uint16_t)sbox[(v>>12)&0xf]<<12);
}
static inline uint16_t rotl5(uint16_t v){ return (v<<5)|(v>>11); }

uint16_t mix(const char *inp) {
    uint16_t state = 0;
    for (int i = 0; i < 12; i++) {
        uint16_t mul   = (i == 0) ? 0x3a2a : state;
        uint16_t accum = (uint16_t)((uint32_t)(unsigned char)inp[i] * mul);
        state          = rotl5(sbox4(accum ^ keys[i % 4]));
    }
    return state;
}
```

This is `mix_fast.c`. It reads challenges from stdin (one per line), prepends the previous 4-hex answer, runs the formula, and prints the next answer. No VM, no interpreter, no tree-walking. Just arithmetic.

```bash
gcc -O2 -o mix_fast mix_fast.c
```

### The Client

The server protocol is straightforward:
1. Connect
2. Read the `--- CHALLENGES ---` header, then 20,000 challenge lines, then `--- END ---`
3. For each challenge `c_i`, compute `mix(prev + c_i)` where `prev` starts as `"0000"`
4. Send all 20,000 hex answers, one per line

`solve.py` does this in two phases: receive everything first, then batch-solve with `mix_fast` via subprocess, then send all answers at once. This avoids per-round network latency.

```python
# Solve all 20000 at once
inp = "\n".join(challenges) + "\nEND\n"
proc = subprocess.run([MIX_BIN], input=inp, capture_output=True, text=True, timeout=5)
answers = proc.stdout.strip().split("\n")
```

The key insight for the network side: the server sends all 20,000 challenges *upfront* before expecting any answers. So we can read the entire batch, solve it offline, and fire back all answers in one `sendall`. This minimizes round-trips to essentially one.

## Running It

```
$ python3 solve.py
Received 20000 challenges in 0.68s
Computed 20000 answers in 0.018s
Total time: 1.26s
all 20000 correct
squ1rrel{c0mp1l1ng_t0_c0mb1n4t0rs_1s_s0_r3tr0}
```

18 milliseconds to solve 20,000 challenges. For reference, the original VM took 5,700 ms for a *single* challenge. That's a 6.3 million× speedup once you understand what the algorithm actually is.

The 1.26 second total time is essentially just network round-trip — the computation itself is noise.

## Key Takeaways

**The challenge teaches algorithm extraction from VM bytecode.** When a VM is too slow to oracle your way through a challenge, you have to actually read what the bytecode does. This is the "not lazy" hint in the description.

**What to look for when reversing VM bytecode:**
- Split execution into phases (compile vs. execute) — trace which memory regions change
- Log all arithmetic operations (XOR, multiply, shift) with their operands to spot patterns
- Look for regularity in the data: cycling constants scream "round keys"
- Nibble-wise table lookups are almost always S-boxes

**The "combinator" twist:** The VM doesn't directly implement the hash formula. It first "compiles" the input into a combinator expression tree, then evaluates that tree. This is a functional programming trick from the 1980s where programs are compiled to a graph of S, K, I combinators and reduced lazily. The flag spells this out: `c0mp1l1ng_t0_c0mb1n4t0rs_1s_s0_r3tr0`. We broke through this by not trying to understand the VM's internal structure — just observing the *inputs and outputs* of each arithmetic operation until the formula became visible.

**The performance trap is the real puzzle.** The challenge was specifically designed so that any naive "just run the VM" approach fails the time limit. With 2 solves total, this caught most teams. The VM is fast enough to verify answers locally (so you know your extraction is correct), but never fast enough to beat 5 seconds × 20,000.

If you want to dig deeper into this kind of reverse engineering, look up "combinator reduction machines" — Turner's original SK combinator papers from the early 1980s are surprisingly readable and explain exactly the architecture hidden inside this VM.
