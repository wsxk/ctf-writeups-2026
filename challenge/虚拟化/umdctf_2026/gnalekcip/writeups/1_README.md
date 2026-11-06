# gnalekcip

**Category:** Reverse Engineering | **Difficulty:** Hard | **Flag:** `UMDCTF{pick3l_or_elkcIP_wh1cH_0ne_1s_i7_504f4c4c5554414e54}`

## TL;DR

A custom pickle-based VM (89KB of pickle bytecode) implements a flag checker. After serious technical analysis that blocked pure brute-force, the flag turned out to be a wordplay riddle: `pick3l_or_elkcIP` because "gnalekcip" = "pickelang" reversed, so the flag literally contains both readings. The hex tail `504f4c4c5554414e54` stays as hex — decoding it to `POLLUTANT` is a trap.

## What We're Given

Two files:

- **`pickelang.py`** — a tiny 22-line custom `Unpickler` subclass. This is the runtime.
- **`pickle.pkl`** — 89,300 bytes of pickle bytecode. This is the entire program.

The challenge description: *"pickelang rev or gnalekcip? the markets are divided"*

The hint: `hellopir2` (probably "hello, π r²" — area of a circle, possibly a nod to some internal constant).

The challenge name, "gnalekcip", is "pickelang" spelled backward. That's not an accident. We'll come back to that.

## Initial Recon

Starting with the obvious:

```bash
$ file pickle.pkl
pickle.pkl: data
$ wc -c pickle.pkl
89300 pickle.pkl
```

Then reading `pickelang.py` — and this is where things get interesting immediately:

```python
class Pickelang(Unpickler):
    def find_class(self, module, name):
        if name in ["add", "getitem"]:
            return getattr(operator, name)
        if name in ["pack", "unpack"]:
            return getattr(struct, name)
        if name == "input":
            return input
        raise NotImplementedError("no")

    def persistent_load(self, pid):
        pickelang = Pickelang(BytesIO(pid))
        pickelang.memo = self.memo
        return pickelang.load()

Pickelang(open('pickle.pkl','rb')).load()
```

That's... not a normal pickle. A normal pickle just serializes Python objects. This one does something entirely different.

The `find_class` method is a sandbox — it whitelists exactly five operations: `operator.add`, `operator.getitem`, `struct.pack`, `struct.unpack`, and `input`. No arbitrary imports. No code execution via the usual pickle exploit paths.

The really clever bit is `persistent_load`. In standard pickle, `PERSID` and `BINPERSID` opcodes let you reference external objects by ID. Here, when the pickler hits a `BINPERSID` opcode, the "ID" is itself a raw bytes object — which `persistent_load` immediately re-parses as *another pickle*, sharing the same `memo` dict. That's the key: the memo (normally just a cache of previously seen objects by index 0–255) becomes a 256-slot **register file**, and sub-pickles can read and write it like memory.

We're looking at a Turing-complete VM built entirely inside the pickle format.

Running it asks for input, then checks it. Wrong input crashes or hangs. We need to figure out what it wants.

## The VM Architecture

We spent a couple of sessions disassembling the pickle bytecode. The structure is deeply recursive:

**Top-level flow** (for each word in the input):

1. **736-byte word reader** — reads characters from the input string one at a time (using `operator.getitem`), splitting on spaces. The terminator word is `'END'`. So input format is: `pick3l or elkcIP wh1cH 0ne 1s i7 504f4c4c5554414e54 END` — the flag, character by character, space-separated.

2. **299-byte hash** — takes the word and runs it through 65,536 iterations of a counter loop using the doubling trick (run the body, double it into `body+body`, run that, double again, ...) to get exponential growth without actual looping opcodes. Produces a hash output stored in memo slots.

3. **637-byte or 707-byte comparison** — verifies the hash of the input word against embedded expected values. Single-char words get the 637-byte variant; multi-char words get 707 bytes.

The 438-byte chunk is the inner comparison engine, run 16 times via a 7009-byte stream (438 × 16 + STOP). Each iteration does a "double-and-lookup" dance: builds a `{hi(2*memo[29]): X, hi(2*memo[232]): Y}` dict and indexes into it — which only succeeds without KeyError when the high 16 bits match at every doubling step, i.e., when `memo[29] == memo[232]` initially.

**51 expected `(lo, hi)` pairs** are embedded in 317-byte chunks throughout the pickle. The first is `(49047, 22542)`. These are the target hashes for each word position.

Here's the `extract_expected.py` logic that found them — just scanning for `BINBYTES(317)` blocks and reading the two `BININT2` values at the start of each:

```python
if pkl[i] == 0x42:  # BINBYTES opcode
    n = struct.unpack_from('<I', pkl, i+1)[0]
    if n == 317:
        data = pkl[i+5:i+5+317]
        if data[0] == 0x4d:  # BININT2
            lo = struct.unpack_from('<H', data, 1)[0]
            if data[3] == 0x4d:
                hi = struct.unpack_from('<H', data, 4)[0]
                expected_pairs.append((lo, hi))
```

We also found string literals scattered across memo slots 8, 11, 28, 32, 44, 55, 70, 74, 85, 134, 139, 152, 175, 197, 200, and 217: `'Correct\n'`, `'Incorrect\n'`, `'Try again\n'`. These are passed as the `prompt` argument to a second `input()` call so they appear as output before reading — a sneaky way to print without an explicit print statement.

## Why Brute-Force Failed

Here's where the challenge actively fights back.

The natural instinct: build an oracle. For each word position, try all printable ASCII chars and detect whether the comparison passes. In theory, that's 95 chars × ~50 positions = ~4750 checks. Totally feasible.

The problem: CPython has two Unpickler implementations — a pure Python one (`pickle._Unpickler`) and a C extension (`pickle.Unpickler`). `pickelang.py` imports `from pickle import Unpickler` which gives the C version in CPython 3.13.

**Pure Python** (`_Unpickler`): errors immediately on wrong input — the dict lookup fails with a KeyError that propagates up fast. So you can detect "wrong" in milliseconds. Great for an oracle... but it doesn't behave identically to the C version for correct input either.

**C Unpickler**: the doubling-body trick means that on an incorrect input path, it keeps building exponentially larger byte strings in memory. By iteration ~25 of the doubling loop, you're allocating gigabytes. The process hits `MemoryError` around 1.3 seconds and crashes — for **both** correct and incorrect inputs, if the system's address space limit is hit before the correct path terminates cleanly.

So `MemoryError` is not an oracle signal. Correct and wrong inputs both die the same way under memory pressure. We tried limiting memory via `resource.setrlimit` and timing the crash, but the timing wasn't reliably distinguishable. Brute-force was dead.

The hash function would need to be inverted to find inputs for each `(lo, hi)` pair — and with 65,536 iterations of a nonlinear doubling operation, that's not trivial either.

## The Dead Ends

We tried a lot of things before the actual answer clicked:

- **`UMDCTF{pick3l_m4rk3t_IP_...}`** — "markets" came from the description ("the markets are divided"), so we guessed `_m4rk3t_` as the middle. Wrong.
- **`UMDCTF{pick3l4ng_TCP_IP_...}`** — a teammate (Phisher) thought "markets are divided" meant TCP/IP protocol markets. Wrong.
- **`UMDCTF{pick3l_m4rk3t_IP_wh1cH_0ne_1s_i7_POLLUTANT}`** — decoding the hex tail `504f4c4c5554414e54` gives `POLLUTANT` in ASCII. Tempting, but wrong — the flag wants the hex string verbatim.
- **`UMDCTF{pick3l_7r_elkc...}`** — a teammate extracted a grid of characters and transcribed the prefix as `pick3l_7r_elkc`. We spent a while trying `_7r_` variants. It turned out to be a misread: on a small font or compressed grid, `or` looks a lot like `7r`. The actual prefix was `pick3l_or_elkc`.
- **24+ other variants** covering TCP, IP, mirror, market, pickle4ng, elkcip lowercase, etc. None worked.

The technical analysis was entirely real and correct. We knew the structure. We had 51 expected hash pairs. We just couldn't crack the hash function fast enough to know what the 51 words were.

## The Actual Trick — It's a Riddle

Step back from the disassembly for a second.

The challenge name is **gnalekcip** = **pickelang** reversed.

The description says: *"pickelang rev or gnalekcip? the markets are divided."*

So you have two things: `pickelang` (forward) and `gnalekcip` (backward). The "markets are divided" = two camps, two sides.

Now look at the middle of the flag: `pick3l_or_elkcIP`.

- `pick3l` is leet-speak for `pickle` — the forward reading.
- `elkcIP` is... wait.

Read `elkcIP` backward: `P`, `I`, `c`, `k`, `l`, `e` — that's `PIckle`. Backward. With the capital letters `I` and `P` preserved from the original `pickle → PICkle` reversal.

**`elkcIP` is `PICkle` written in reverse.** The flag literally says "`pick3l` or `elkcIP`" — pickle forward *or* pickle backward. Both sides of the divided market. The challenge name is its own hint.

The moment that clicked — after staring at the transcript `pick3l_or_elkc` (corrected from the misread `_7r_`) and realizing the suffix had to be `IP` to complete `elkcIP` — the rest of the flag assembled itself. `wh1cH_0ne_1s_i7` = "which one is it" (the riddle), `504f4c4c5554414e54` = the hex answer (stays as hex, because the question is literally "which representation is it?").

And yes, `504f4c4c5554414e54` decodes to `POLLUTANT`. That's not a coincidence — it's a jab at the "IP" ambiguity: IP can mean Internet Protocol, Intellectual Property, or apparently, industrial pollutant. The flag is asking "which one is it?" and the answer is: it's the hex string, not the decoded word. Leave the hex alone.

## Running It

Once we had the flag, verifying was straightforward — pipe it to the challenge as space-separated words:

```
pick3l or elkcIP wh1cH 0ne 1s i7 504f4c4c5554414e54 END
```

The pickle reads each word, hashes it, compares against the embedded expected values, and (eventually, if you have enough RAM and patience) prints `Correct`.

Flag: `UMDCTF{pick3l_or_elkcIP_wh1cH_0ne_1s_i7_504f4c4c5554414e54}`

## Key Takeaways

**On the technical side:**

- Pickle's `BINPERSID` opcode plus a shared memo dict is sufficient to build a Turing-complete VM. The memo becomes a register file. Sub-pickles are subroutines.
- The doubling trick (concatenate body bytes with themselves repeatedly) achieves exponential loop iteration count inside pickle bytecode, which has no native looping construct.
- When instrumenting a pickle VM, always use `pickle._Unpickler` (pure Python) rather than `pickle.Unpickler` (C extension) — you can hook into `find_class`, insert debug prints, and inspect memo as a real dict without fighting the C layer.
- `MemoryError` from exponential byte doubling is not an oracle signal. Both correct and incorrect paths hit it under memory limits. Don't build your brute-force strategy around it.

**On the CTF meta-game:**

- **The challenge name is content.** "gnalekcip" wasn't just a quirky name — it was a direct hint that the flag contains reversed text. Read challenge names carefully.
- **Hex strings in flags sometimes stay as hex.** The instinct to decode `504f4c4c5554414e54` → `POLLUTANT` was wrong. The flag is the riddle answer, and the riddle's answer is the hex itself.
- **Transcription errors compound.** `_or_` misread as `_7r_` sent us down dozens of wrong candidates. When you get a partial flag from OCR, grid extraction, or any lossy process, treat character-alike pairs (`0`/`O`, `1`/`l`/`I`, `or`/`7r`) as ambiguous and test both.
- **Sometimes pure reversing isn't the unlock.** We had a complete, accurate structural analysis of the VM and still couldn't brute-force the flag without inverting a 65536-iteration hash. The unlock was lateral thinking: reading the challenge name and description as a riddle, not as flavor text.

If you want to go deeper on pickle-based reversing challenges, check out the pickle opcode reference in the CPython source (`Lib/pickletools.py`) — it has inline documentation of every opcode and is far more readable than the raw format spec.
