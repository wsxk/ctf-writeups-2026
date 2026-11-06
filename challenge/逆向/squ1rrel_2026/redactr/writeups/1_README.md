# Redactr

**Category:** Rev | **Difficulty:** Hard | **Flag:** `squ1rrel{1t5_4ll_4_blrrr}`

## TL;DR

A Rust binary applies a custom multi-stage blur to an image and gives us the blurred result. We have to recover the original. The core trick: the blur has a sneaky **parity-dependent pixel iteration order** — odd rows and odd columns are processed in *reverse* — that makes a naive inverse fail for exactly half the rows/columns. Once we corrected the forward model and applied MILP + Adam gradient descent, we got close enough for the server to hand us the flag.

## What We're Given

- `redactr` — a Rust ELF binary (the "redaction tool")
- `blurred.png` — a 384x96 grayscale PNG that the binary has already processed

The challenge setup: `redactr` reads some original image, applies its blur pipeline, and outputs `blurred.png`. Our job is to invert that pipeline and POST the recovered image to `http://34.59.146.32/submit` with field name `file`. The server compares our submission to the true original and responds with a `max_pixel_error` score. Get that score low enough (single digits, as it turned out) and you get the flag.

```bash
$ file redactr
redactr: ELF 64-bit LSB pie executable, x86-64, dynamically linked, Rust
$ file blurred.png
blurred.png: PNG image data, 384 x 96, 8-bit grayscale
```

![The blurred input image](blurred.png)

*The blurred.png we were given. It looks like a blurry text banner — clearly something readable underneath, which gave us strong motivation to get the inversion right.*

## Initial Recon

First thing: `strings` on the binary looking for anything interesting.

```
SERIAL-TIER-CHECK
Enhanced mode activated
Invalid license format
License verified: tier
```

Oh interesting — there's a license verification system. The binary expects a serial in `SERIAL-TIER-CHECK` hex format. That seemed like it might unlock some "enhanced mode" with a different code path. We spent a while on this.

**Spoiler: it's a complete red herring.** Here's why. The license check has a condition that goes something like `(TIER * 63 + 11) mod 7 <= 3`. Let's do the math:

- `63 mod 7 = 0`, so `TIER * 63 mod 7 = 0` for all TIER
- So the expression simplifies to `11 mod 7 = 4`
- `4 <= 3` is always **false**

The check is mathematically unsolvable — no valid license tier can ever pass it. We confirmed this by patching past it in gdb anyway: "enhanced mode" activates, prints different text, and then... does exactly the same blur. There's no alternate code path. The license system is pure trolling.

The real work was in the blur pipeline, which we had to reverse-engineer from binary constants.

### What the Binary Actually Does

After reversing `sub_41f0f0` (the main processing function), we mapped out the full pipeline:

```
original → tile_perm → H_blur → odd_tile_transpose → V_blur → blurred.png
```

The key parameters we extracted from the binary:

| Operation | Parameter | Value |
|-----------|-----------|-------|
| Fisher-Yates tile shuffle | seed | `0xa3f1d7e294b6085c` |
| H blur | radius / center / divisor | 63 / 19 / 145 |
| V blur | radius / center / divisor | 31 / 11 / 73 |
| PRNG | algorithm | xorshift32 (shifts 13/17/5) |
| H row PRNG seeds | `row * 0x45d9f3b7`, XOR'd with constants | left: `0x7c3ae91d`, right: `0xb4f26d08` |
| V col PRNG seeds | `col * 0x9e3779b9`, XOR'd with constants | top: `0xe8153ca7`, bottom: `0x2d96f4be` |

The blur at each pixel `c` in a row accumulates: the pixel's own value times the center weight, plus all in-bounds neighbors, plus PRNG-generated pseudo-pixels for the out-of-bounds positions. Then divide by the divisor (round-half-up), clamp to 255. Simple enough on paper.

## The Vulnerability / Trick

This is the real puzzle. We built our first forward model (`forward_fast.py`) assuming even, left-to-right processing for both rows and columns. It looked correct — the math was right, the constants matched. But when we tried to invert it, something was deeply wrong.

We ran a MILP feasibility check (MILP = Mixed Integer Linear Programming, which here means: "is there ANY integer solution in [0,255] that satisfies these blur constraints?"). The result:

- **Even columns: all feasible.** Our inverse worked perfectly.
- **Odd columns: ALL infeasible.** Every single one. Not "hard to solve" — provably impossible.

That 50/50 split was the smoking gun. Something fundamentally different was happening for odd rows/columns.

### The Parity-Dependent Iteration Order

Back to the binary. Closer reading of the disassembly of the row blur loop showed something subtle: there's a branch on `row_index & 1`. 

For even rows (`r & 1 == 0`): pixels iterate **left to right**, `c = 0, 1, 2, ..., 383`.  
For odd rows (`r & 1 == 1`): pixels iterate **right to left**, `c = 383, 382, ..., 1, 0`.

Same deal for columns: even columns go top-to-bottom, odd columns go bottom-to-top.

Why does this matter? Because the PRNG state is shared across the whole row. It advances once per out-of-bounds sample hit during iteration. When you flip the iteration order, you flip which pixels consume which PRNG outputs. A pixel at `c=383` in an even row gets one set of PRNG bytes for its right-OOB samples; the same pixel at `c=383` in an odd row gets a completely different set because the PRNG was already exhausted by the earlier positions.

It's a very easy thing to miss when reading the assembly — it looks like a "maybe this is an optimization" branch that couldn't possibly affect correctness. It absolutely does.

```python
# The key fix in forward_real.py (line 102-105):
if r & 1:
    order = range(W - 1, -1, -1)  # 383..0 for odd rows
else:
    order = range(W)              # 0..383 for even rows
```

Same pattern for the vertical blur:

```python
# forward_real.py (line 151-154):
if c & 1:
    order = range(H - 1, -1, -1)  # 95..0 for odd columns
else:
    order = range(H)              # 0..95 for even columns
```

After this fix, we re-ran MILP feasibility: **384/384 columns feasible. 0 infeasible.** That's how you know you've got the right model.

## Building the Exploit

With the corrected forward model (`forward_real.py`), the inversion strategy became:

1. **Invert V blur**: for each column, find pixel values that produce the observed blurred column (MILP per column, 96 integer variables each)
2. **Invert odd_tile_transpose**: it's involutive (applying it twice = identity), so just apply it again
3. **Invert H blur**: for each row, same MILP approach (384 integer variables per row)
4. **Invert tile permutation**: just apply the inverse permutation

The blur inversion is a standard "find x such that K @ x + oob ≈ divisor * target" problem, where:
- `K` is the banded convolution matrix (center weight on diagonal, 1s for in-bounds neighbors)
- `oob` is the precomputed PRNG contribution at each pixel
- `divisor * target` is our "desired output" scaled up before the division

The MILP constraints give us ranges: for each output pixel `q`, the true accumulated sum must be in `[divisor*q - half, divisor*q + half)`. In code:

```python
# solve_real.py lines 136-141 (V-blur inversion per column)
b_lo = 73 * blurred[:, col].astype(int) - 36 - oob_V[:, col]
b_hi = 73 * blurred[:, col].astype(int) + 36 - oob_V[:, col]
constraints = LinearConstraint(K_V, b_lo, b_hi)
res = milp(c, constraints=constraints, bounds=bounds_u8, integrality=integrality,
           options={'time_limit': 3, 'disp': False})
```

The V MILP ran clean — 0 infeasible columns, forward diff max 0. The H MILP was trickier because there's a subtlety we hit: inverting V and H independently, in sequence, can fail. V MILP finds *a* valid pre-V image, but not necessarily the one that's also consistent with *some* valid pre-H image. The two inversions aren't independent.

For the H stage, we had some infeasible rows where MILP timed out and fell back to least-squares. That gave us `final_x.png` with `max_pixel_error=14` on the server. Getting below that required refinement.

### Adam Gradient Descent on the Linearized Model

The key insight for the final push: treat the whole pipeline as differentiable. The blur is a linear operation (the rounding/clamping is the only nonlinearity, and if we stay close to the true answer it barely matters). We can compute `forward(x) - blurred` and backpropagate through the linearized blur to nudge `x` toward the right answer.

We started from `final_x.png` (max_pixel_error=14) and ran Adam optimizer — Adam is like gradient descent but with adaptive learning rates per parameter, which handles the very different sensitivities of near-edge pixels vs. center pixels much better.

The progression of `max_pixel_error` as Adam ran:
```
Start:  14
...     10
...     6
...     4
...     3
Final:  2  ← server returns flag
```

![Final recovered image (max_pixel_error=2)](final_adam_best.png)

*This is what we submitted to get the flag. Compare to the blurred version above — you can now clearly read the text that was hidden in the blur.*

At `max_pixel_error=2`, the server responded with the flag instead of just the error score.

### Submitting

```bash
curl -X POST -F "file=@final_adam_best.png" http://34.59.146.32/submit
# {"max_pixel_error": 2, "result": "correct", "flag": "squ1rrel{1t5_4ll_4_blrrr}"}
```

## Running It

The full pipeline:

```
$ python3 forward_real.py          # verify corrected forward model
Forward took 42.1s
Hash: [deterministic hash]

$ python3 solve_real.py            # V MILP + H MILP
Blurred (96, 384) range [0, 255]
Computing OOB... 8.3s
V MILP: 41.2s, infeasible: 0
V forward diff: max 0, mean 0.000    ← perfect V inversion
H MILP: 127.4s, infeasible: 8        ← 8 rows needed LSQ fallback
Saved final_real.png

[Submit final_real.png → max_pixel_error=14]

[Run Adam refinement from final_x.png...]
[After ~3000 iterations...]
[Submit final_adam_best.png → max_pixel_error=2]
[Server: squ1rrel{1t5_4ll_4_blrrr}]
```

## Key Takeaways

**The parity-dependent iteration bug is the whole challenge.** Everything else is just image deconvolution mechanics. The lesson: when reversing custom crypto or image processing code, read *every* branch, even ones that look like optimization artifacts. A single `if r & 1: order = reversed(...)` completely breaks a naive inverse.

**MILP feasibility as a diagnostic tool.** When half your columns came back infeasible, that told us immediately that our forward model was wrong for those cases — and the clean 50/50 even/odd split told us exactly *where* to look. If you're ever trying to invert something and the LP is mysteriously infeasible, check whether your model is actually correct before assuming the math is hard.

**PRNG-seeded OOB samples are subtle.** The blur uses separate PRNGs for left/right (and top/bottom) OOB samples, seeded deterministically per row/column. This means the OOB contribution is fully deterministic and computable, which is what makes the inversion tractable as an LP at all. If the OOB were truly random (entropy), you couldn't do this.

**Gradient descent as a polisher.** When MILP gives you something "close but not quite" (max_pixel_error=14), Adam on the linearized forward model is a great way to squeeze out the remaining error. The blur is smooth and well-conditioned enough that gradient descent converges well.

**The license check troll.** Author zerodaytea put a mathematically-unsolvable license verification (`TIER*63+11 mod 7 <= 3` always equals 4, never ≤ 3`) just to waste your time. Classic. If you see a verification system in a rev challenge, do the algebra before spending hours trying to crack it.
