# Starless-C Writeup

**CTF:** LA CTF 2025
**Category:** Reverse Engineering
**Points:** 442
**Solves:** 4
**Author:** me

## TL;DR

Navigate a self-modifying binary maze using WASD controls. The twist? Moving through "active" cells transforms them, and you need exactly the right 5 cells active to unlock the flag. Oh, and one critical cell doesn't even exist in memory, breaking most obvious paths.

**Flag:** `lactf{starless_c_more_like_starless_0xcc}`

---

## The Challenge

We're given a binary called `starless_c` and a hint referencing "The Starless Sea" by Erin Morgenstern:

> *"The son of the fortune-teller stands before three doors. A bee. A key. A flag."*

Running the binary gives us this cryptic message:

```
There is a flag in the binary.
  (The flag is a metaphor but also still a flag.)
  (The binary could rightly be considered a gimmick.)
A person this far into a challenge has their path to follow...
```

Then it waits for input. Typing WASD moves us around, and 'f' presumably tries to get the flag. But pressing 'f' immediately just crashes. There must be something we need to do first.

---

## Initial Recon

First things first - what are we dealing with?

```bash
$ file starless_c
starless_c: ELF 64-bit LSB executable, x86-64, statically linked, no section header
```

Interesting - no section headers. Opening it in Binary Ninja reveals something wild: the binary has **23 separate memory-mapped regions**, each at addresses like `0x67679000`, `0x6767a000`, etc. Each region is basically a self-contained "cell" with its own code.

## Understanding the Maze

After staring at the disassembly for a while, the structure becomes clear:

### Cell Layout

Each cell (at address `0x67XXX000`) has:
- **Offset 0x00**: Either NOPs (`0x90909090`) if "active" or crash code (`xor eax,eax; mov [rax],al`) if "inactive"
- **Offset 0x04**: A jump to the next cell in a chain (for the flag path)
- **Offset 0x0C**: Input handler that reads WASD+F and navigates

### The Navigation Mechanic

When you press a direction key:
1. The current cell checks if the **destination cell is active**
2. If active: **consume** it (write crash code) and **activate** a "save target" (write NOPs)
3. Jump to the destination cell's input handler

This is basically a token-routing puzzle! You have 5 "active" tokens and need to route them to specific destinations.

### The Flag Chain

Pressing 'f' jumps to cell `0x6767a000` at offset 0. If that cell is active (NOPs), it falls through to a jump instruction that goes to the next cell. This creates a chain:

```
6767a → 67682 → 6768a → 67691 → 67692 → 0x42069000 (FLAG!)
```

All 5 cells must be active for the chain to complete without crashing.

## The Token Puzzle

Here's where it gets spicy:

**Initial active cells:** `{67689, 6768a, 6768c, 6768d, 67694}`
**Required active cells:** `{6767a, 67682, 6768a, 67691, 67692}`

We need to transform our 5 tokens into the 5 flag chain cells. Sounds simple enough, right?

### The Catch

Each move has a specific "save target". For example:
- From cell `67682`, pressing 's' goes to `6768a`. If `6768a` is active, consume it and activate `67692`.
- From cell `6768c`, pressing 'a' goes to `6768b`. If `6768b` is active, consume it and activate `6768a`.

The routes are fixed by the binary's code. Some tokens can only go to specific destinations.

## The Critical Discovery

I wrote a BFS solver to find the path, but it kept finding nothing. After millions of states searched - nothing. Something was wrong.

Time for GDB. I ran `info proc mappings` to see what's actually loaded in memory:

```
0x67679000 - mapped
0x6767a000 - mapped
...
0x67692000 - mapped
0x67693000 - NOT MAPPED!!!
0x67694000 - mapped
...
```

**Cell 67693 doesn't exist!**

This is huge. Several moves have `67693` as their save target:
- `67695 'a'`: dest=67694, save=67693
- `67691 'd'`: dest=67692, save=67693
- `67683 's'`: dest=6768b, save=67693

If you try to activate cell 67693, the binary writes to unmapped memory → **SEGFAULT**.

This means:
1. You can't consume `67694` from `67695` (would crash)
2. You can't consume `67692` from `67691` (would crash)
3. Many paths that looked valid are actually death traps

## The Corrected Solver

Armed with this knowledge, I rewrote the solver to account for unmapped save targets:

```python
# If destination is active and save_target is unmapped, move is INVALID
if dest in active and save not in MAPPED:
    return None  # This would crash!
```

Running the corrected solver finally found a solution:

```
Iter 538501: h=0, path len=145
*** SOLUTION FOUND ***
```

145 moves! That's a long path, but it works.

## The Solution

```
sddddswaasdwaaasdssawwdwddsawasassdddwsddwasaaaawwdwdddsawaasassdddwwdwasssaaawwdwwassdddssddwasaaawwddwdsaaawdasssddwsddwawaawasdddssawdwaaddwaaf
```

Testing locally with a dummy flag.txt:
```bash
$ echo "test_flag" > flag.txt
$ printf "sdddd...waaf" | ./starless_c
...
test_flag
```

It works! The flag function at `0x42069000` opens and prints `flag.txt`.

## Getting the Real Flag

```bash
$ printf "sddddswaasdwaaasdssawwdwddsawasassdddwsddwasaaaawwdwdddsawaasassdddwwdwasssaaawwdwwassdddssddwasaaawwddwdsaaawdasssddwsddwawaawasdddssawdwaaddwaaf" | nc chall.lac.tf 32223
```

```
lactf{starless_c_more_like_starless_0xcc}
```

The flag references `0xCC` which is the `int3` (breakpoint) instruction - fitting since the binary is full of them as padding!

## Key Takeaways

1. **Trust but verify**: Just because a cell address appears in the code doesn't mean it's mapped
2. **Dynamic analysis is your friend**: GDB's `info proc mappings` revealed what static analysis couldn't
3. **Token routing puzzles**: When tokens can only transform (never duplicate), the path constraints become very tight
4. **Self-modifying code**: Cells writing NOPs or crash code to each other is a clever mechanic

## Files

- `correct_solver.py`: The working solver that accounts for unmapped cells
- `starless_c`: The challenge binary

---

*This challenge was a beautiful example of how a simple concept (maze navigation) becomes fiendishly difficult with the right constraints. The unmapped cell 67693 was the key insight that made all the difference.*
