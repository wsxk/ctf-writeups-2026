## `wromwarp` -- A throwback emulator for the fake "Lonely Entertainment System"

The `LES` system emulated here is at approximately the same sophistication as the ["First generation of home video game consoles"](https://en.wikipedia.org/wiki/First_generation_of_video_game_consoles).

Comments at the top of `wromwarp.c` describe the basic arcitecture, memory layout, CPU instructions, etc. Several games have been implemented using the LES assembly for this emulator:

* Pong (`pong.les`)
* Lunal Lander (`lunar.les`)
* Minesweeper (`minesweeper.les`)
* Conway's Game of Life (`life.les`)
* Flappy Bird (`flappy.les`)
* Snake / Blockade (`snake.les`)

Two test programs are also provided:

* `printflag.les` shows you where the flag is located in memory and prints it. The memory image distributed only contains a placeholder flag and `printflag.les` isn't available online.
* `pixtest.les` which just draws pixels to the screen and is meant to be a very simple demo of how LES works.

### Background

The name `wromwarp` is meant to be a hint that the intended solution involves altering how the ROM(s) are used in order to skip some place. Careful inspection of the program (or just random testing) will reveal that `/load` just loads the program and doesn't reset any registers, memory, screen, or other state. It's possible to pause execution on one program, then load another, and resume execution using the instructions from the new program but with the memory and registers of the previous program still lingering around.

This idea was inspired by:

* Retro Game Mechanics Explained ["Access Glitch Worlds in Super Mario Bros. via NES Tennis"](https://www.youtube.com/watch?v=hrFHNgJlJSg)
* Kosmic ["SMB1 Glitched Worlds"](https://www.youtube.com/watch?v=D0Eev2YdrKY)
* 100th Coin ["How I Beat NES Mario in 0.000005 Seconds"](https://www.youtube.com/watch?v=pK7hU-ovUso)


### Getting the flag

The flag is loaded into memory (WRAM) when the memory is initialized by either `/reset` or an `INIT` instruction. The flag is place starting at 0xF0. However, `wromwarp` doesn't provide any mechanism to directly dump or inspect memory and none of the provided games will directly read and report this memory. In fact, some of them overwrite the flag during initialization.

The goal is to find the right sequence of roms loads, breakpoints, and rom swaps to control execution enough to read the flag out of memory.

There is, no doubt, a pratically unlimited number of ways to solve this challenge. There is enough oportunity to control execution across all the provided programs that enumerating all the possible solutions is impossible.

But, there is one particularly simple method using the generation counter update routine in `life.les`. Specifically:

```
UGEN:
SET 9, mR
SET 57, gB

UGENINC:
DUPE mR, mW
LOAD gA
INC gA
CMP gA, gB; if digit > 9
JMPGT <UGENZERO>
STORE gA
JMP <MAIN>

UGENZERO:
SET 48, gA
STORE gA
DEC mR
JMP <UGENINC>
```

This routine is responsible for updating the `Gen: 0000` text to `Gen: 0001` and so forth. The string is located in memory starting at 0x00 and the routine works backwards from the end. The `SET 9, mR` instruction loads 9 into the read memory pointer register. It then sets the ASCII value for "9" into gB. Then it loads a digit out of memory, increments it, and checks if the incremented value exceedes "9". If it does, it jumps to `<UGENZERO>` which stores "0" for that digit back into memory and then decrements the memory read pointer and trys again with the new digit.

If the `SET 57, gB` instruction is somehow skipped, then the comparison to see if the digit exceedes "9" turns into a comparison to see if the digit exceedes 0 (because `gB` is zero before this set). It will, and the routine will keep backing up through memory. Eventually memory will underflow and it will start checking against the flag bytes. If the `SET 9, mR` is skipped the `mR` register also starts at 0 which speeds up the underflow process.


Using these steps:

`/load life.les` to load life. `/break <UGEN>` to cause execution to pause just at the instructions we need to skip. `/run` to run life. Execution will stop at `->* 094: 140 UGEN                 SET 9, mR`.

Now to avoid this instruction we can load another program. `/load pong.les` works. At PC 094 it shows:

```
->* 094: 138 -                    SET 1, gC
    095: 139 -                    SET 5, mW
```

Both of these instructions are fine to execute. They avoid the two instructions we need to skip without causing any nasty side-effects.

Run `/step` twice. At this point execution will be at `->  096: 140 -                    STORE gC`. We can swap back to life with `/load life.les`.

Execution will be at:
```
->  096: 144 UGENINC              DUPE mR, mW
```

And importantly, the registers will be:
```
gA     48           gB      0           gC      1           gD      0
iU      0           iD      0           iL      0           iR      0
iA      0           iB      0           mR      0           mW      5
cX1     0           cY1     0           cX2    31           cY2    30
pA      0           pB      0
PC     96           SPCN    0           CMP     0           HALT    0
SPC1    0           SPC2    0           SPC3    0           SPC4    0
ISC 39102
```

See that `gB` and `mR` are both 0.

Now we can set a breakpoint on instruction 98 with `/break 98` which will pause execution after each `LOAD gA`. `mR` will start getting decremented and this will let us read the flag out of memory backwards by looking at the value of `gA` after each load.

Run `/continue` and the first gA value is 71 (ASCII "G" from `mR` = 0). Keep running `/continue` and gA reads out:

* 0 (`\0` at `mR` == 255)
* 125 (`}` at `mR` == 254)
* 114 (`r` at `mR` == 253)
* 119 (`w` at `mR` == 252)
* 95 (`_` at `mR` == 251)
* 115 (`s` at `mR` == 250)
* 97 (`a` at `mR` == 249)
* 116 (`t` at `mR` == 248)
* 95 (`_` at `mR` == 247)
* 119 (`w` at `mR` == 246)
* 101 (`e` at `mR` == 245)
* 110 (`n` at `mR` == 244)
* 123 (`{` at `mR` == 243)
* 70 (`F` at `mR` == 242)
* 84 (`T` at `mR` == 241)
* 67 (`C` at `mR` == 240)
* 0 (`\0` at `mR` == 239)
* [...]

Flag is `CTF{new_tas_wr}`
