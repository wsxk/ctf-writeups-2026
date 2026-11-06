# War Hymn

Author: `Archan6el`

My friend had a psychotic break after A&M lost their playoff game against Miami this last season. He put a flag somewhere in this program, all the while chanting the Aggie War Hymn and muttering how he hid the key to A&M's victory. Can you try to find it? Maybe it'll bring him back to his senses.

## Hints

## Dev Notes

The main binary has some anti-debugger checks and some goofy trolling function pointer things to make static and dynamic analysis a little harder. Can make things harder by further obfuscation or more disassembly confusion tricks, but challenge is maybe fine as is for an easy-medium. Will probably add the latter eventually if I have time

Decryption function is hidden in `.init.checksum.validation`. XOR key is "hidden" in `.init.constructors.global`, encrypted zlib compressed shared library is hidden in `.bss.secure.buffer` 

Main binary extracts the data in the above sections. It uses the decryption function to decrypt the encrypted zlib compressed shared library. It then decompresses the zlib shared library and dynamically loads and executes the `run` function in said shared library

## Solution

LLM was able to realize it was unwrapping an inner shared library and calling the `run` function. However, it could not oneshot and did get a little confused on the network traffic, but mostly ignored it.

After decrypting / decompressing the inner shared library, we can then just feed it back to the LLM which easily recognizes rc4 and decrypts the flag. 

I then told it to put both steps together and it was able to do so without issue.

Output from end:
```
Implemented an end-to-end solver in solve.py that only assumes war-hymn exists.

What it does:
- Reads the staged sections from the outer ELF.
- Executes the stage function in memory.
- Extracts and inflates the zlib chunk to recover the inner ELF.
- Applies the inner RC4 routine to decrypt all challenge strings and the flag.
- Prints the final outputs.

Verified output from running it:
- Yeah, this aint it
- Keep going bruh
- Are we there yet?
- gigem{sh0uld_h4v3_r4n_th3_b411_0n_f1r$t_4nd_g04l!!!}
```

flag:
`gigem{sh0uld_h4v3_r4n_th3_b411_0n_f1r$t_4nd_g04l!!!}`
