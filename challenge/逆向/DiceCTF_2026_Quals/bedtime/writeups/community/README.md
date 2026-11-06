# Bedtime

**Category:** Reversing | **Difficulty:** Hard | **Flag:** `dice{regularly_runs_like_mad_to_game_of_matches}`

## Overview
A stripped Rust static-PIE ELF binary that reads a stream of 4-digit decimal numbers and plays 384 rounds of bounded Nim against the user, using a custom PRNG for its moves when in a losing position.

## Solution

### Binary Structure

The binary reads input as concatenated 4-digit decimal numbers, with `9999` as a group separator. It processes 384 game entries, each containing:
- A set of pile values (varying count)
- A max-move parameter `k` (field3/checksum)
- The game uses bounded Nim rules: each turn, remove 1 to k items from any pile

### Game Theory

Each entry is classified using Sprague-Grundy theory:
- **Grundy value** per pile: `pile_value % (k+1)`
- **XOR** of all Grundy values determines position type:
  - **N-position** (XOR != 0): Current player has a winning strategy. The computer finds and plays the optimal move directly. Returns 0.
  - **P-position** (XOR == 0): Current player is in a losing position. The computer uses a PRNG to make a random move. If the PRNG move is invalid (pile too small), returns 1.

The binary sums all 384 return values and checks if the total equals 219 (0xdb). If so, it decrypts and prints the flag.

### PRNG Mechanics

The PRNG maintains 3 state values `[state0, state1, state2]`:

```python
r12 = state2 ^ 0x28027f28b04ccfa7
rax = (state1 + r12) & MASK64
state0_new = ROL64(state0^2 + rax, 32)
state1_intermediate = rax

r12_updated = (r12 + rax) & MASK64
state0_final = ROL64(state0_new^2 + r12_updated, 32)
state1_final = r12_updated

pile_idx = rax % pile_count
amount = (r12_updated % k) + 1
```

The critical discovery: **state[2] is updated by XORing in only the USER's move data** (pile_idx, amount, and new pile value after the move). PRNG move data does NOT affect state[2]. This creates a feedback loop where the user's moves influence future PRNG outputs.

### Solving

1. **Dump game data** from the binary at runtime using GDB (384 entries with pile values and parameters), saved to `all_entries.pkl`.

2. **Classify entries**: 219 are P-positions (must return 1), 165 are N-positions (return 0).

3. **Simulate each P-position entry**:
   - PRNG makes a move → user responds optimally (moving back to P-position when possible)
   - Track state[2] evolution through user moves
   - Game loops until PRNG generates an invalid move (pile too small) → returns 1
   - PRNG state carries between entries

4. **Generate input**: User moves encoded as 4-digit pairs (amount, pile) in reverse order per entry, separated by `9999`.

The final solver (`solve6.py`) correctly simulates all 384 entries, achieving byte_sum=219 and producing valid input that the binary accepts.

### Key Debugging Insights

- **Operator precedence bug**: Python's `&` has lower precedence than `+`, causing incorrect PRNG computation until explicit parenthesization.
- **state[2] is NOT always 0**: Initial testing with dummy input showed state[2]=0, but actual gameplay updates it via a B-tree node XOR loop. Discovered through GDB hardware watchpoints and targeted breakpoint tracing.
- **Only user nodes matter**: The binary maintains a B-tree of move nodes. The cleanup loop XORs node data into state[2], but only processes user move nodes, not PRNG move nodes.

## Key Takeaways
- When reversing game-theory binaries, identify the mathematical framework (Sprague-Grundy) early.
- PRNG state evolution can have subtle dependencies on user input — always verify with dynamic analysis.
- GDB Python scripting is invaluable for tracing complex state through obfuscated binaries.
- Watch for operator precedence issues in Python when translating assembly to high-level code.
