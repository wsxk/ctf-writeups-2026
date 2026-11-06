# Cabinet

**Category:** Pwn | **Points:** 210 | **Author:** bekkaze | **Flag:** `HZ{jk7iaSjf_c4b1n3t_MC8Y3l2h}`

## Challenge Description

A tiny platform game where completing a real play session is supposed to prove a
human is present. The service does not give a live terminal — it accepts a
recorded input session (a "replay") and plays it back. The win function
`attest_human()` prints the flag.

## Initial Analysis

Files: `cabinet`, `libc.so.6`, `ld-linux-x86-64.so.2`.

`checksec`:

```text
Arch:       amd64-64-little
RELRO:      Partial RELRO
Stack:      No canary found
NX:         NX enabled
PIE:        No PIE (0x400000)
Stripped:   No
```

Not stripped and no PIE — function names are visible and addresses are fixed.
Useful symbols:

```text
0x4018fe  attest_human      <- target
0x404120  ARENA
0x4042b8  g_live
```

**Replay format:** a 4-byte big-endian frame count, then one input byte per
frame. The input bits are `left=0x01`, `right=0x02`, `jump=0x04`, `stomp=0x08`,
`fine-movement=0x10` (combinable, so fine-right = `0x12`).

## The Vulnerability / Core Concept

`game_reset()` spawns seven gremlins into the global `ARENA` array. Each entity
record is `0x1c` bytes; the array holds 12 (indices 0–11), and **immediately
after it** at `ARENA + 12*0x1c = 0x404270` sits a per-frame hook function
pointer, called at the end of every `game_step()` (normally `default_hook`).

Stomping a gremlin removes it and spawns **two** dust objects, so live count
grows by one per stomp: `7 → 8 → 9 → 10 → 11 → 12`. On the sixth stomp the code
removes the gremlin (count 12 → 11), then checks `if (g_live <= 11)` before
spawning two dust objects at indices 11 **and 12**. Index 12 is out of bounds —
its `x` field (a 16.16 fixed-point coordinate) overlaps the hook, and the next
field is zeroed, clearing the pointer's upper half:

```text
entity[12].x  <->  game hook   (becomes 0x00000000_XXXXXXXX = player's x)
```

So the **player's x coordinate becomes the called function address.**

## Exploitation

Coordinates are 16.16 fixed point: one pixel is `0x10000`, normal speed is two
pixels (`0x20000`), and holding fine-movement changes the coordinate by one raw
unit per frame. Target:

```text
0x4018fe = 0x400000 + 0x18fe   ->   x = 64 pixels + 6398 fine steps
```

Plan (full generator in `solve.py`, output `cabinet-exploit.bin`):

1. Stomp five gremlins (x = 56, 60, 68, 72, 76), deliberately leaving the one at
   **x = 64** alive.
2. Return to x = 64.
3. Move right by `0x18fe` fine steps (still well within stomp range of x=64).
4. Stomp the sixth gremlin — the OOB dust object writes `0x4018fe` over the hook.
5. `game_step()` calls the hook → enters `attest_human()`.

```python
frames += bytes([LEFT]) * 6                              # return to x=64
frames += bytes([RIGHT | FINE]) * (0x4018FE - 0x400000)  # 0x400000 -> 0x4018fe
frames += bytes([STOMP])                                 # sixth stomp = OOB write
replay = pack(">I", len(frames)) + frames
```

A zero frame after each of the first five stomps is required because the game
checks the **rising edge** of the stomp button (a fresh press, not a held one).
The final replay is ~6,437 frames (6,441 bytes with the header); replay mode has
no animation delay, so it runs instantly.

```bash
python3 solve.py
./bin/cabinet < cabinet-exploit.bin
```

Locally, `attest_human()` prints a stub (`HZ{local_kiosk_attestation_stub}`)
when it can't reach the flag-dispenser socket — proof execution reached the
function. Remotely the replay was sent as binary over the authenticated
WebSocket and the service returned the real flag.

## Flag

`HZ{jk7iaSjf_c4b1n3t_MC8Y3l2h}`

## Key Takeaways

- No stack overflow, shellcode, or libc leak — just normal game logic growing an
  array one element past its bounds onto an adjacent function pointer.
- Off-by-one in a "remove one, add two" loop: the bound check ran while the count
  was temporarily low.
- A game's fine-movement mechanic doubled as a byte-precise write primitive: the
  player's coordinate directly became the code address to call.
