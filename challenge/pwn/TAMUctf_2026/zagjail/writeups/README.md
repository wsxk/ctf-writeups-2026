# zagjail

Author: `flocto`

Shoutout my goat! Find <a href='https://github.com/macsencasaus/zag/tree/main' target='_blank'>zag here</a>.

## Dev Notes

Building might take a while since it needs to download Python. Maybe should switch to a python slim image.

## Solution

There are a quite a few bugs in the `server.py` implementation checking for pointer memory safe.

In particular, using `&` to create a pointer to a variable, then accessing an offset of that pointer is not checked correctly. 

Another bug, this time in zag itself, involved arrays, if you defined something like `var arr: [128]u32 = {1, 2, 3};`, the array would located an offset of 12 from RBP rather than 128 * 4. From there you could easily access out of bounds and write any ROP chain or onegadget.

For an example of a solution that works on Docker, see `solve.zag`, it jumps to `system` in libc, and prepares the argument `/bin/sh` by having a dummy function that accepts a string argument but does nothing. 

flag:
`gigem{custom_language_but_still_links_to_libc_:thinking:_jk_thanks_for_the_cool_language}`
