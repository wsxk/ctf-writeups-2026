# Flag Finder Writeup

**Challenge:** flag-finder
**Category:** Reverse Engineering
**Points:** 500
**Solves:** 1
**Event:** LA CTF 2025

## TL;DR

The challenge presents a checkbox grid that must match a massive regex. Turns out it's a nonogram puzzle hidden inside regex lookaheads. Solve the nonogram with Z3, decode the pixel art text, get the flag.

## First Look

Visiting the challenge URL, we're greeted with a grid of 101 checkboxes across and 19 rows down. There's a "Find flag" button that presumably validates our checkbox pattern.

Peeking at `script.js` reveals the magic - a regex so long it made my browser cry:

```javascript
const theFlag = /^(?=.{101}$)(?=.{0}(....).{97}#)(?=.{0}(....).{93}##)...
```

This thing is absolutely massive. But what's it actually doing?

## Breaking Down the Regex

The regex has two main parts:

1. **Column constraints** - A bunch of lookaheads like `(?=.{0}(....).{97}#)` that check if specific columns have `#` at certain positions
2. **Row patterns** - The actual row-by-row matching at the end

Each checkbox is either `.` (unchecked) or `#` (checked). The regex is essentially encoding rules like "column 4 must have a `#` in rows 2, 3, 5" and so on.

Wait a minute... constraints on rows and columns that determine which cells are filled? That's a **nonogram** (also called picross)!

## What's a Nonogram?

For the uninitiated - a nonogram is a puzzle where you fill in a grid based on number clues. Each row/column has numbers telling you how many consecutive filled cells appear and in what groups. Like sudoku's artsy cousin.

The regex lookaheads are encoding these constraints in the most cursed way possible.

## Solving the Puzzle

First attempt: constraint propagation. Classic nonogram solving technique. Timed out.

Second attempt: fancier constraint propagation. Still timed out.

Third attempt: throw Z3 at it. Z3 is an SMT solver - basically a really smart tool for solving constraint satisfaction problems. Perfect for this.

```python
from z3 import *
import re

# Create boolean variables for each cell
cells = [[Bool(f"c_{r}_{c}") for c in range(101)] for r in range(19)]

solver = Solver()

# Parse column constraints from regex and add to solver
for match in re.finditer(r'\(\?=\.\{(\d+)\}(.+?)\.\{(\d+)\}(#*)\)', regex):
    # Add constraint: this column position must be filled/empty
    ...

# Parse row constraints and add those too
for row_idx, row_pattern in enumerate(row_patterns):
    # Add constraint: this row must match the pattern
    ...

# Let Z3 cook
if solver.check() == sat:
    # Extract solution!
```

After about a minute of thinking, Z3 spits out a solution. Verified it against the original regex - perfect match.

## The Solution Grid

```
......................................................................................................
.##...........#...##..##.#.#.#...#.#.###.......#..##..........##..........##.###.###.........#...###.
..#..##...##.###..#..##..#.#.##..#.#...#......##.#.#.....#.#.#.#.#.#.....#.....#...#.....#.#.##....#.
..#...##.#....#..###.#...###.#.#.###...#.....#.#.#.#.....#.#.#.#.#.#.....###.###...#.....###.#.#.###.
..#..#.#.#....#...#..##..###.#.#...#...#.....#.#.#.#.....###.#.#.#.#.....#.#...#...#.....###.#.#...#.
.###.###..##..##..#...##.#.#.#.#...#...#.###..##.###.###...#.###..##.###.###.###...#.###.###.#.#.###.
...
```

Squint at it and you can see... text! It's pixel art rendered in a 3x5 font.

## Decoding the Pixel Art

The grid uses a simple bitmap font:
- Each character is 3 pixels wide and 5 pixels tall
- 1-pixel gaps between characters (columns 0, 4, 8, ... are separators)
- 1-pixel gaps between rows (rows 0, 6, 12, 18 are separators)
- Three "lines" of text: rows 1-5, 7-11, and 13-17

Built a font lookup table by visually matching patterns:

```python
FONT = {
    ('##.', '.#.', '.#.', '.#.', '###'): 'l',
    ('...', '##.', '.##', '#.#', '###'): 'a',
    ('.##', '##.', '#..', '##.', '.##'): '{',
    # ... and so on for each character
}
```

Some characters use leet speak:
- `4` = a
- `3` = e
- `6` = g
- `0` = o
- `7` = t
- `5` = s

## The Flag

After decoding all three lines and stitching them together:

```
lactf{Wh47_d0_y0u_637_wh3n_y0u_cr055_4_r363x_4nd_4_n0n06r4m?_4_r363x06r4m!}
```

Or in plain English: **"What do you get when you cross a regex and a nonogram? A regexogram!"**

Beautiful. Cursed. I love it.

## Files

- `solve_z3.py` - Z3-based nonogram solver
- `decode_final.py` - Pixel font decoder
- `extract_flag.py` - Pattern analysis helper

## Lessons Learned

1. When you see a ridiculous regex, look for patterns - it might be encoding something else entirely
2. Z3 is your friend for constraint satisfaction problems
3. CTF authors have way too much free time (affectionate)

**Flag:** `lactf{Wh47_d0_y0u_637_wh3n_y0u_cr055_4_r363x_4nd_4_n0n06r4m?_4_r363x06r4m!}`
