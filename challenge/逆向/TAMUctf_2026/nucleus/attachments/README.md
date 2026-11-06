# Nucleus

Author: `beds`

This lab specimen is mysterious... it seems to be evolving. Get to the bottom of it for me, will you?

## Dev Notes

No compiler since it requires running the process 21 times with different xor keys to build the flag.

## Solution

We see that the binary takes in a single character as input, then saves a new file that is a copy of the old file. Then, it goes to the new file and edits the resource to be the original binary XORed with our input.

Working backwards, we can see that the current resource is the result of some nucleus21.exe XORed with `}`.

From here, we can assume we need to go all the way down to the original nucleus0 or nucleus1.exe, collecting the XOR keys along the way, and then putting it all together to get the flag.

This gives us `gigem{RCD4Ta_i5_N3aT}` as the flag.

flag:
`gigem{RCD4Ta_i5_N3aT}`
