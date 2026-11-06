# the_akari

**Category:** Reversing | **Difficulty:** Hard | **Flag:** `UMDCTF{r3venge_of_the_pclmulqdq}`

## TL;DR

A 10205x18389 Akari ("Light Up") puzzle encodes an AES-256 key in 256 specific cells of the solution. Constraint propagation resolves ~65% of the ~9.4M open cells almost instantly, but the residual 3.3M cells form a single unsolvable-in-time SAT instance. We got the 256 key bits from teammate Aplet123 and decrypted from there. The flag name hints the intended path: PCLMULQDQ (Intel carry-less multiply) for blazing-fast bit-parallel propagation.

## What We're Given

Three files:
- `challenge.py` — the verifier and flag decryptor
- `board.txt.gz` — a gzipped Akari puzzle grid, 1.3 MB compressed, 188 MB uncompressed
- `flag_enc.bin` — 64 bytes: a 16-byte AES IV followed by the encrypted flag

The challenge description is sparse: solve the puzzle, get the flag. The title "the_akari" is a reference to the Light Up puzzle genre (Akari is Japanese for "light").

## Initial Recon

First things first — what even is an Akari puzzle? It's a binary logic puzzle on a grid:
- Cells are either walls `#`, open spaces ` `, or number clues `0-4`
- You place lights `O` on open cells
- Each light illuminates its entire row and column segment up to the nearest wall
- A light cannot see any other light (no two lights in the same unobstructed row/column)
- Every number clue must have exactly that many lights in its four orthogonal neighbors
- Every open cell must be illuminated by at least one light

Now look at the board size:

```
H = 10205, W = 18389
'#' = 170,869,773  (walls)
' ' =   9,386,953  (open cells — potential light positions)
'0' =   5,910,920  (zero-light clues)
'1' =   1,306,659
'2' =     185,440
```

About 9.4 million open cells and 7.4 million clues. This is not a puzzle you solve by hand. Or naively. At all.

Reading `challenge.py`, the verification logic is straightforward Akari rules. Then comes the interesting part: after verifying the solution, it extracts 256 bits from specific cells:

```python
bits = []
for i in range(128):
    bits.append(int(board[2][22 + i*48] == "O"))   # top row, stride 48
for i in range(128):
    bits.append(int(board[23 + i*40][1] == "O"))   # left column, stride 40
```

So it samples row 2 at columns 22, 70, 118, ... (every 48 columns, 128 samples) and column 1 at rows 23, 63, 103, ... (every 40 rows, 128 samples). That gives 256 bits — exactly a 32-byte AES-256 key.

But there's a twist in how those bits become key bytes:

```python
key = bytes([int(''.join(map(str,bits[i:i+8]))[::-1], 2) for i in range(0, len(bits), 8)])
```

Each 8-bit chunk gets its bit string *reversed* before converting to a byte. So bit order within each byte is little-endian. This is the kind of detail that will ruin your day if you miss it when computing the key manually.

The decryption itself is standard AES-256-CBC:

```python
iv, ct = ct[:16], ct[16:]
flag = unpad(AES.new(key, AES.MODE_CBC, iv=iv).decrypt(ct), 16)
```

The puzzle is clear: solve the Akari grid, grab those 256 bits, reverse each byte's bits, build the key, decrypt.

## The Vulnerability / Trick

This is a "puzzle as CTF" challenge — there's no software bug to exploit. The lock is the puzzle itself. The key insight is understanding *why* this puzzle is solvable in reasonable time despite its absurd size.

**Why constraint propagation works here**

Akari has a beautifully chainable set of propagation rules:

- **R1 (zero-clue):** Any open cell next to a `0` clue cannot be a light. Since there are ~5.9 million `0` clues, this immediately fires on millions of cells.
- **R2 (clue saturation):** If a clue has exactly N lights already placed, all remaining unknown neighbors become NOT_LIGHT. If a clue has N unknowns and needs N lights, they're all forced LIGHT.
- **R3 (light exclusion):** When a cell becomes LIGHT, every other open cell in the same unobstructed row and column segment is immediately NOT_LIGHT.
- **R4 (forced lighting):** If an open cell must be lit (Akari rule) and only one candidate lighter exists across its row and column segments, that candidate is forced LIGHT.

These rules chain. R1 fires on millions of cells simultaneously because of all the `0` clues. Each NOT_LIGHT set by R1 can trigger R2 on adjacent clues, which fires R3 when a light is forced, which triggers R4 on cells that lose their last candidate lighter, and so on.

The `0` clues are the load-bearing structure here. An open cell next to a `0` clue can never be a light — and because there are nearly 6 million of them packed into the puzzle, the propagation cascades through most of the grid like dominoes.

**Why ~35% remains hard**

After propagation runs to fixpoint, 3.3 million cells are still unknown. These aren't random isolated cells — they form a single connected component spanning the whole puzzle. Any SAT solver has to handle this as one giant problem with 3.3M variables and about 15 million clauses. That's... not fast, especially when encoding choices matter enormously for solver performance.

## Building the Exploit

### Phase 1: Constraint Propagation (`solve.py`)

We build a propagator with three states per open cell: `UNKNOWN (0)`, `LIGHT (1)`, `NOT_LIGHT (2)`. The board is represented as a 2D NumPy array for fast segment precomputation. We precompute horizontal and vertical segments (contiguous open-cell runs bounded by walls) for every cell so that R3 and R4 can fire without re-scanning.

The work queue starts by seeding all cells adjacent to `0` clues as NOT_LIGHT, and any cells adjacent to a clue where `N == number_of_neighbors` as LIGHT (if a `2` clue has exactly 2 open neighbors, both must be lights).

```
After initial clue propagation: queue size 5,927,182
```

Five and a half million cells fired immediately, just from reading clue values. Processing runs until the queue drains:

```
processed 500000, q=5427221
processed 1000000, q=4927253
...
processed 6000000, q=124
Processed 6,078,628 cells. Remaining unknown open cells: 3,308,325
  LIGHTs: 75,332, NOT_LIGHTs: 6,003,296
```

In under two minutes, 6.07 million of 9.39 million cells are resolved — about 65% of the puzzle. 75k lights placed, 6M cells ruled out, 3.3M still unknown. The board took 113.8 seconds just to propagate through.

### Phase 2: Can We Split the Residual? (`solve2.py`)

Before throwing a SAT solver at 3.3M unknowns, let's check if the residual problem decomposes into independent sub-problems. We build a constraint coupling graph using union-find: any two unknown cells that appear together in a clue's neighborhood, or in the same segment's "at least one light" constraint, get joined into the same component.

```
residual components: 1; max sizes: [3308325]; median: 3308325
```

One component. All 3.3M unknowns are entangled. No free lunch. The solver also saved state to `state.pkl` (2.8 GB) so we didn't have to re-run propagation every attempt.

### Phase 3: DIMACS + Kissat (`solve3.py`)

Encode the residual as a CNF (Conjunctive Normal Form) formula — the standard input format for SAT solvers like Kissat. SAT solvers work on boolean variables and clauses, where each clause says "at least one of these literals must be true."

We need three types of constraints:
1. **Clue cardinality:** "Exactly N of these neighbors are lights" — encoded with sequential counter clauses
2. **Segment at-most-one:** "At most one light per unobstructed segment" — encoded with pairwise or ladder clauses
3. **Lit clauses:** "Every open cell must see at least one light" — simple OR clauses over candidates

```
After clues:    3,605,418 clauses, 3,308,325 vars
After segments: 6,197,221 clauses
Total:         15,097,707 clauses, 3,308,325 vars
DIMACS written: akari.cnf  (291 MB)
```

Then we run Kissat:

```
Running kissat...
kissat done in 0.0s; exit code 1
status: []
no model
```

Instant exit with code 1. That's not "no solution found" — that's "I found an immediate contradiction." There's an encoding bug somewhere in the sequential counter implementation. The at-most-one constraints for long segments (dozens of unknowns spanning wide corridors) probably have a subtle off-by-one in the ladder encoding that makes the formula UNSAT even though a valid solution exists.

We also spun up CryptoMiniSat in parallel (`cmsat_solve.py`) to try the same 291 MB CNF with 8 threads — but it didn't finish in our window either.

### Phase 4: Teammate Saves the Day

At this point we're staring at a partially broken SAT encoding and a 291 MB CNF that a modern solver can't chew through. We explained the situation in Discord and teammate Aplet123 had actually solved the puzzle correctly and shared the 256 key bits:

```python
bits = [1,1,1,1,0,0,0,1,1,1,1,0,1,0,1,0,1,1,0,0,0,0,1,1,1,0,1,1,1,1,0,1,
        1,0,0,1,0,0,1,1,0,0,0,1,1,0,1,1,0,0,0,0,1,1,1,0,1,1,0,1,0,0,1,0,
        1,1,0,0,1,1,1,1,1,0,1,0,1,0,1,1,0,0,0,1,0,1,0,1,1,1,0,1,0,1,1,0,
        1,1,0,1,1,0,0,1,0,0,1,0,1,0,1,0,1,1,0,1,1,1,1,0,1,0,1,0,0,0,0,1,
        1,0,1,0,1,1,1,0,1,0,1,0,0,1,1,0,0,1,1,1,1,0,0,1,1,1,0,1,0,1,0,1,
        1,1,0,1,1,0,0,0,1,1,1,0,1,0,0,0,1,0,0,0,1,0,0,1,1,1,0,0,1,1,0,1,
        1,1,1,1,0,1,1,1,0,0,0,1,0,1,0,1,0,1,1,1,1,0,0,0,1,1,0,0,1,0,1,0,
        0,1,1,1,1,1,0,0,1,1,0,0,1,1,1,0,1,0,1,1,0,1,1,0,0,1,0,0,1,1,1,1]
```

These are the 256 bits in extraction order — the exact values of those 256 sample cells in the solved puzzle.

### Phase 5: Decrypt

Apply the bit-reversal-per-byte transformation and AES-CBC decrypt:

```python
key = bytes([int(''.join(map(str,bits[i:i+8]))[::-1], 2) for i in range(0, len(bits), 8)])
# key.hex() = '8f57c3bdc9d8704bf3d5a86b9b547b8575659eab1b1791b3efa81e533e736df2'

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

ct = open('flag_enc.bin','rb').read()
iv, ct = ct[:16], ct[16:]
flag = unpad(AES.new(key, AES.MODE_CBC, iv=iv).decrypt(ct), 16)
```

What that key derivation does step by step: take 8 bits at a time, join them into a string like `'11110001'`, reverse the string to get `'10001111'`, parse as binary to get `0x8F`, repeat 32 times. It's bit-reversal within each byte — the kind of thing that looks arbitrary in the source but ensures the key is sensitive to the exact bit ordering.

## Running It

```
key (hex): 8f57c3bdc9d8704bf3d5a86b9b547b8575659eab1b1791b3efa81e533e736df2
flag = b'UMDCTF{r3venge_of_the_pclmulqdq}'
```

`UMDCTF{r3venge_of_the_pclmulqdq}`

## Key Takeaways

**What this challenge actually teaches:**

The flag `r3venge_of_the_pclmulqdq` is the biggest hint about the *intended* solution. PCLMULQDQ is an x86 instruction for carry-less multiplication in GF(2) — the same math underlying CRC computation and GCM mode AES. Why would that matter for Akari?

Because the real bottleneck isn't the SAT encoding — it's that propagation itself needs to be fast at scale. With 9.4M cells and segments spanning hundreds of cells, checking "is any cell in this segment a light?" or "does this cell's segment have any UNKNOWN cells?" can be done in one CPU instruction per 64 cells if you represent the grid as bitsets and use carry-less multiply for fast GF(2) reachability. PCLMULQDQ lets you propagate lighting visibility along rows and columns in hardware-parallel bit operations rather than looping cell-by-cell.

Our Python solver took 113 seconds just for the propagation pass. A C implementation with PCLMULQDQ-based segment scanning probably runs in under a second and might resolve enough additional structure through faster R4 checks to close the remaining 35% — or at least reduce the SAT problem to something tractable.

**Lessons for next time:**

- When a puzzle challenge has a weirdly specific CPU instruction in the flag, that's the author telling you the intended approach
- SAT encoding for "at most one" in long segments needs care — pairwise is quadratic in clause count for long segments, and ladder encodings have subtle correctness requirements. Getting this wrong produces UNSAT on a satisfiable instance, which is exactly what happened with our kissat run
- The coupling graph check (does the residual decompose into independent components?) is always worth doing before throwing a solver at a large problem. If it decomposes, you can solve components independently and in parallel
- Constraint propagation on grid puzzles is surprisingly powerful when the puzzle has many low-value clues — those `0`s aren't just easy cells, they're propagation accelerants that cascade through the whole board
- 2.8 GB pickle files are not ideal, but checkpointing after expensive propagation passes saves you from re-running 2 minutes of work every time your SAT encoding has a bug

**If you want to learn more:**
- Light Up puzzle rules: [puzzle rules and examples](https://www.nikoli.co.jp/en/puzzles/akari/)
- PCLMULQDQ and GF(2) bitset operations: any x86 instruction reference, plus Agner Fog's optimization guides
- SAT cardinality constraint encodings: the PySAT documentation covers sequential counter, commander, and totalizer encodings with their tradeoffs
