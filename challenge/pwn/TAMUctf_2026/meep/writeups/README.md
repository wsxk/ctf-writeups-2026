# meep

Author: `Archan6el`

The big Meep listens and waits. All it asks for is a name and a command...

## Dev Notes

There's two versions of source. `meep.c` doesn't fork when new connections come in, and `meep_prod.c` does. Give competitors `meep.c` so that debugging is easier (don't need to follow child), but have the server run `meep_prod.c`

Dist gives everything needed to run `meep` using Docker and allows for debugging. There's a lot so I definitely could have missed or overlooked something needed in order for the program to work

Also I lowkey don't know what to put for the chal description lol. We ball

## Solution

Look at the `solve` directory. Yes the ret2shellcode method is possible but was unintended, you were supposed to use ROP gadgets and ret2libc

flag:
`gigem{m33p_m1p_1_n33d_4_m4p}`
