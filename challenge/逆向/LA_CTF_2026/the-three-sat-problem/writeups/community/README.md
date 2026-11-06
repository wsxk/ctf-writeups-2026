# Three-Sat Problem Writeup

**CTF**: LA CTF 2025
**Category**: Reverse Engineering
**Flag**: `lactf{is_the_three_body_problem_np_hard}`

---

## The Challenge

We're given a binary called `three_sat_problem`. When you run it, it asks:

```
Have you solved the Three-Sat Problem?
```

And waits for input. If you type something wrong, it says "I see you haven't." Pretty rude, honestly.

## What's a 3-SAT Problem?

Before we dive in, let's talk about what "3-SAT" actually means (don't worry, I'll keep it simple).

Imagine you have a bunch of light switches, and someone gives you a list of rules like:
- "Switch 1 OR Switch 5 OR Switch 12 must be ON"
- "Switch 3 must be OFF OR Switch 7 must be ON OR Switch 2 must be OFF"
- ... hundreds more rules

Your job? Find a way to flip all the switches so that EVERY rule is satisfied. That's basically 3-SAT - each rule has 3 conditions connected by "OR", and all rules must be true at the same time.

This is famously one of the hardest types of problems in computer science (it's "NP-complete" for the nerds out there).

## First Look at the Binary

Throwing the binary into Binary Ninja, I found the `main` function. Here's what it does:

1. Reads exactly 1279 characters of input (each must be '0' or '1')
2. Calls a huge validation function `sub_401289`
3. Checks if character at position 754 is '1'
4. If both checks pass, it builds the flag from our input and prints it

So our input is basically 1279 binary digits, and we need to find the right combination.

## The Monster Function

The validation function `sub_401289` is absolutely massive - over 13,000 lines of intermediate code. Looking at it, it's doing exactly what I described above: checking hundreds of 3-SAT clauses.

The structure looks like:
```
result = (bit_A OR bit_B OR bit_C)
       AND (bit_D OR NOT bit_E OR bit_F)
       AND (NOT bit_G OR bit_H OR bit_I)
       AND ... (repeat ~2800 times)
```

If the result is non-zero (meaning ALL clauses are satisfied), we win.

## Extracting the Formula

I wrote a Python script to parse the binary's intermediate representation (LLIL SSA form) and extract all the clauses. The key patterns I looked for:

- **Loading input bits**: Direct memory access like `[0x415060 + offset]` gives us a positive literal
- **Negated bits**: The binary pre-computes `NOT(bit)` and stores them on the stack
- **OR operations**: Combining literals with `|`
- **AND operations**: When two OR-chains get AND-ed together, both become clauses

After extraction, I had **2848 clauses** involving the 1279 input bits.

## The Problem

I threw all these clauses into Z3 (a powerful SAT solver) with the constraint that bit 754 must be '1' (as required by main).

Result: **UNSAT** (unsatisfiable)

Wait, what? The challenge HAS to be solvable. Something's wrong with my extraction.

## Finding the Bug

I used Z3's MaxSAT feature to find out how many clauses COULD be satisfied with bit754=1. The answer: **2847 out of 2848**.

Only ONE clause was causing the entire formula to be unsatisfiable:
```
Clause 2833: bit_1095 OR bit_0 must be True
```

This clause was extracted from line 13754 in the IL, where a register `rcx#60` was being AND-ed with something else. But tracing back, this clause seemed fishy - it was likely a bug in my extraction logic where register state wasn't being tracked correctly through some complex operation.

## The Solution

Simple fix: just remove that one bad clause and solve again.

```python
# Remove the problematic clause
clauses = [c for c in clauses if c['lits'] != [(1095, True), (0, True)]]

# Solve with Z3
solver = Solver()
solver.add(bits[754] == True)  # Required by main
for clause in clauses:
    solver.add(Or(*[bits[i] if pos else Not(bits[i]) for i, pos in clause]))

result = solver.check()  # sat!
```

Z3 found a solution in seconds. I converted it to a string of '0's and '1's and fed it to the binary:

```
$ python3 solve.py | ./three_sat_problem
Have you solved the Three-Sat Problem?
Incredible! Let me get the flag for you...
lactf{is_the_three_body_problem_np_hard}
```

## The Flag

`lactf{is_the_three_body_problem_np_hard}`

Haha, nice pun! The "Three-Body Problem" is a famous unsolvable problem in physics (also a great sci-fi book), and "Three-SAT Problem" is NP-hard. The challenge author is asking: is the three-body problem NP-hard too?

(For the curious: the three-body problem is actually proven to be computationally undecidable in general, which is even worse than NP-hard!)

## Lessons Learned

1. **SAT solvers are your friend** - Z3 can handle thousands of clauses easily
2. **MaxSAT is great for debugging** - When regular SAT fails, MaxSAT tells you exactly which clauses are problematic
3. **Extraction is tricky** - One wrong clause out of 2848 was enough to make the whole thing unsolvable
4. **Trust but verify** - Always test partial solutions to narrow down issues

## Tools Used

- Binary Ninja (for reversing)
- Python + Z3 (for SAT solving)
- Way too much coffee

---

*Writeup by someone who now knows way more about SAT problems than they ever wanted to.*
