# rival-battle

**Category:** Reversing | **Points:** 500 | **Author:** Abhi404 | **Flag:** `zdk{SQULRTl3_l5_7he_bES7_s7AR73r}`

## Description
> The rival says this old battle simulator is unbeatable. It always starts from the same trainer card, though, and old handheld games are not very random.

## TL;DR
A command-line Pokémon-style battle simulator plus a 64-byte trainer save. The battle looks random but is fully deterministic — the save seeds a tiny 16-bit PRNG. You must find the exact 14-turn route that drives the internal state to one specific value. The twist: a 32-bit verification hash has accidental collisions, so a route can pass the check yet decrypt the flag into garbage. Filter routes by requiring the decrypted output to start with `zdk{`.

## Initial Analysis

```
$ file battle trainer.sav
battle:      ELF 64-bit LSB pie executable, x86-64, stripped
trainer.sav: data
```

Running it sets the theme: *"This link cable battle is deterministic. You still cannot route it."* The description's "not very random" points straight at a predictable PRNG.

The save:

```
00000000: 5a44 4b4d 4f4e 0100 ...  ZDKMON..........
00000010: 5cf4 0000 ...
```

The binary checks the first six bytes are `ZDKMON`, version `1`, and a 16-bit value at `0x10` (`0xf45c`) that seeds the PRNG after XOR with `0x8748`:

```
0xf45c ^ 0x8748 = 0x7314   # fixed initial PRNG state
```

`strings` leaks all move commands and success/failure messages, including *"The battle ended too cleanly. The rival refuses to talk."* — so winning is not about knocking everything out; it's about reaching one exact internal state within 14 turns.

## Vulnerability / Core Concept

The enemy's "random" decisions come from a small 16-bit generator:

```python
def next_rng(x):
    x = (x * 0x41c6 + 0x4e6d) & 0xffff
    return x ^ rol16(x, 5)
```

Fixed seed → fully predictable enemy moves. But player moves like `EMBER` and `THUNDER SHOCK` also consume PRNG values, so changing one move shifts every later enemy decision. That makes it a **routing** problem, not a normal battle.

At battle end, the program takes the low 16 bits of **fourteen** state fields (the six Pokémon HP values, both active indices, score, PRNG state, a route checksum, potion availability, leech turns, status turns) and hashes them with 14 constants and rotations:

```python
h = 0x91d0f00d
for word, const, rot in zip(words, consts, rots):
    h ^= (word & 0xffff) * const
    h = rol32(h, rot)
# required: 0x9218a78c
```

**The collision trap.** Because the check is only 32 bits, different states collide to `0x9218a78c` and the program happily says *"That route was perfect."* — but the flag comes out as binary garbage. The flag **decryption** uses the *complete* final state (all 14 words), not the 32-bit hash. The key starts as ASCII `route151` (`0x726f757465313531`), each state field is mixed in with the SplitMix64 finalizer, and the resulting keystream XORs 33 encrypted bytes. Strong avalanche means only the *intended* state decrypts to `zdk{`.

## Exploitation

The search space is `8^14 = 2^42`, too large for a naive Python loop, so the state machine was ported to CUDA (`cuda_reverse_valid.cu`) and run on GPU. For each candidate route: simulate ≤14 turns → check the 32-bit hash == `0x9218a78c` → decrypt with the full final state → keep only routes whose plaintext starts with `zdk{`. A Python reference model (`solve.py`) validated the simulator against the real binary's HP bars and enemy moves; `z3solve.py` explored the route-checksum constraints.

One quirk that breeds fake collisions: a **failed command** (e.g. switching to the already-active Pokémon) skips the rival's action that turn, opening many odd-but-accepted states.

The unique intended route:

```
2 3 4 6 4 2 7 2 1 6 4 2 4 2
= GROWL, FOCUS ENERGY, EMBER, SWITCH BULBASAUR, GROWTH, VINE WHIP,
  SWITCH PIKACHU, THUNDER SHOCK, QUICK ATTACK, SWITCH BULBASAUR,
  GROWTH, VINE WHIP, GROWTH, VINE WHIP
```

Reproduce it:

```bash
$ printf '2\n3\n4\n6\n4\n2\n7\n2\n1\n6\n4\n2\n4\n2\n' | ./battle
RIVAL: ...fine. That route was perfect.
PROF.OAK: Here is the professor's secret:
zdk{SQULRTl3_l5_7he_bES7_s7AR73r}
```

> Excluded from this directory: `battle` binary, `trainer.sav`. Included: `solve.py` (reference sim), `z3solve.py`, `cuda_reverse_valid.cu` (GPU route search).

## Flag
`zdk{SQULRTl3_l5_7he_bES7_s7AR73r}`

## Key Takeaways
- **"Not very random" means find the PRNG.** A fixed seed makes the whole battle a deterministic routing puzzle.
- **A 32-bit acceptance hash has collisions.** When a second stage (decryption) consumes the full state, use *it* — checking for the `zdk{` prefix — as the real oracle rather than the lossy hash.
- **Massive but finite search spaces** (`2^42`) are a good fit for a straightforward CUDA port of the state machine.
