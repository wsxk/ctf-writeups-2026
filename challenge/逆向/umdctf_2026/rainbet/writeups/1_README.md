# rainbet

**Category:** Rev | **Difficulty:** Medium | **Flag:** `UMDCTF{one_might_argue_that_gambling_is_the_best_vice_but_they_would_be_wrong}`

## TL;DR

The challenge gives us the server's RNG backend as a WebAssembly file. Since the server generates game outcomes deterministically from `(session_id, round_idx)` using the same wasm we have, we can predict every game before we play it — then just always make the perfect move. Chain 25 perfect wins and collect the flag.

## What We're Given

- `rainbet_gen.wasm` — the "leaked RNG backend" (this is the whole joke; the flavor text says "for legal reasons this is not true" twice)
- `rainbet.py` — a Python wrapper around the wasm that exposes `generate_game(session_id, round_idx)`
- A live server at `rainbet.challs.umdctf.io` running two casino-style minigames: **Mines** and **Chicken**

The challenge description sells the premise perfectly: a gambling site accidentally leaked its RNG source code. Can you exploit that to win 25 times in a row and get the flag?

## Initial Recon

First thing we do is read `rainbet.py` to understand what we're working with. The wrapper is pretty clean:

```python
def generate_game(session_id: str, round_idx: int) -> dict:
    raw = _call_generate(session_id, round_idx)
    gtype = raw[0]
    if gtype == 0:
        # Mines: returns grid_size, num_mines, and exact mine positions
        ...
    if gtype == 1:
        # Chicken: returns risk level and exact car (obstacle) step positions
        ...
```

So `generate_game` takes your session ID and the current round number, runs it through the wasm, and hands back the *complete, exact game state* — including where every mine is, or where every car will appear.

That's... the entire vulnerability right there in the wrapper. The server calls this same function to generate your game. We call it locally to predict what the server just generated. Then we just win.

The two games work like this:
- **Mines**: a Minesweeper-style grid. Max win = reveal every safe tile without hitting a mine.
- **Chicken**: a Frogger-style road crossing with cars at certain steps. Max win = cross exactly as many steps as you can without getting hit, then cash out.

We need 25 consecutive max-wins to get the flag.

## The Vulnerability / Trick

This is a **predictable RNG** attack — one of the oldest tricks in online gambling security.

The server generates each game by calling `generate(session_id, round_idx)` inside the wasm. That function is deterministic: same inputs always produce the same game. There's no hidden server-side entropy mixed in after the fact.

Because we have the exact same wasm binary the server uses, we can call `generate_game(session_id, streak)` locally before we even send a move. The result tells us exactly which tiles are safe in Mines, or how far we can walk before a car appears in Chicken. We already know the answer before we're "asked" the question.

The only wrinkle: the server authenticates our moves with HMAC-SHA256. Each action we send has to include a `sig` field — a signature over a canonical "view string" that describes the current game state. The key for this HMAC comes from `/api/sessioninfo` at the start of the session. That endpoint just... hands it to us. So authentication is not actually a barrier here; it just means we have to construct the view strings correctly.

Let's look at the decompiled wasm (`rainbet_gen.dcmp`) for a moment to appreciate what's going on under the hood. The core state update in `f_d` is a custom 8-word 64-bit block cipher running 16 rounds with S-box lookups and XOR mixing:

```
a.g = ((f = a.b) << 37L ^ (g = a.d)) ^ (h = a.g);
a.h = (g << 13L ^ (i = a.a)) ^ (j = a.f);
...
a.a = g ^ (i ^ (h << 23L ^ (b << 3)[131086]:long));
```

This looks intimidating, but it doesn't matter at all how it works internally. What matters is that it's deterministic and we have the binary. We don't need to reverse the algorithm — we just *run it*.

## Building the Exploit

The solve script (`solve.py`) follows a tight loop:

**Step 1: Get our session credentials.**

```python
info = s.get(f"{BASE}/api/sessioninfo", verify=False).json()
sid = info["session_id"]
secret = bytes.fromhex(info["secret"])
```

The server hands us our session ID and the HMAC key. We save both.

**Step 2: Open the WebSocket and receive the first game.**

```python
ws = websocket.create_connection(WS, header=[f"Cookie: {cookie_header}"])
hello = recv()
streak = hello["streak"]   # how many wins we have so far
target = hello["target"]   # need to hit 25
game = hello["game"]       # the current game the server is showing us
```

The server sends a `hello` message with the current game state. `streak` starts at 0; we need to reach `target` (25).

**Step 3: Predict the game locally before playing.**

```python
predicted = generate_game(sid, streak)
```

We call the *same* wasm function the server used to generate this round, with the same session ID and round index. `predicted` now contains the exact mine positions or car positions for this game.

**Step 4a: Play Mines perfectly.**

```python
mines = set(predicted["mines"])
total = game["grid_size"] ** 2
safe_tiles = [t for t in range(total) if t not in mines and t not in revealed]

for t in safe_tiles:
    rev_sorted = ",".join(str(x) for x in sorted(revealed))
    view = f"mines:{streak}:{game['grid_size']}:{game['num_mines']}:{rev_sorted}"
    send({"action": "reveal", "tile": t, "view": view, "sig": sign(view)})
```

We build the HMAC-authenticated view string (the canonical description of the current board state), reveal each safe tile one by one, and sign each action. The server validates the signature before accepting the move.

The view string format for Mines is: `mines:<streak>:<grid_size>:<num_mines>:<comma-separated sorted revealed tiles>`. Keeping the revealed list sorted and comma-separated is important — any deviation breaks the HMAC.

**Step 4b: Play Chicken perfectly.**

```python
safe = max_safe_steps(predicted["cars"])

while crossed < safe:
    view = f"chicken:{streak}:{game['steps']}:{crossed}"
    send({"action": "cross", "view": view, "sig": sign(view)})
    m = recv()
    crossed = m["crossed"]

# cash out before the next car
view = f"chicken:{streak}:{game['steps']}:{crossed}"
send({"action": "cashout", "view": view, "sig": sign(view)})
```

`max_safe_steps` finds the index of the first car in the sequence — that's how many steps we can safely cross. We cross exactly that many times, then cash out. If we went one step further, we'd get hit. If we cashed out earlier, it wouldn't count as a max win.

**Step 5: Repeat until streak hits 25.**

After each completed round, the server sends a result message with the next game embedded in it. We update `streak`, `game`, `revealed`, and `crossed` from that message and loop back to Step 3.

When streak reaches 25, the server returns `complete=true` with the flag attached.

## Running It

```
$ python solve.py
session: {'session_id': 'abc123...', 'secret': 'deadbeef...'}
hello: {'streak': 0, 'target': 25, 'game': {'type': 'mines', ...}}
result: win streak: 1
result: win streak: 2
result: win streak: 3
...
result: win streak: 24
result: win streak: 25
FLAG: UMDCTF{one_might_argue_that_gambling_is_the_best_vice_but_they_would_be_wrong}
```

The script runs in a few seconds. Twenty-five perfect wins, no misses, no resets.

## Key Takeaways

**Predictable RNG is a classic casino attack.** Real gambling sites put enormous effort into ensuring the RNG output can't be predicted from publicly observable data. Seeding from `(session_id, round_idx)` with no additional server-side entropy, and then *distributing the RNG binary*, is about as bad as it gets.

**"You can verify it's fair" can backfire.** Provably fair gambling schemes exist where players can verify the outcome after the fact — but they use cryptographic commitments (hash the seed, reveal it later) precisely so the player can't predict outcomes in advance. Handing out the raw RNG binary is the opposite of that.

**You don't need to fully reverse the algorithm.** The wasm decompiles to a hairy-looking block cipher with S-box lookups and 64-bit XOR rotations. We never had to understand it. `wasmtime` just ran it for us. In CTFs (and in real attacks), running the target's own code against it is almost always faster than reimplementing it.

**HMAC signatures only protect integrity, not confidentiality.** The server signing moves with an HMAC stops tampering in transit, but it can't stop us from computing valid signatures ourselves once we have the key — which the server gave us.

If you want to dig deeper into predictable RNG attacks on gambling systems, look up the 2014 Wired article on cracking slot machine RNGs, or search CTFtime for "LCG prediction" challenges — linear congruential generators (a simpler form of this pattern) come up constantly in crypto and misc categories.
